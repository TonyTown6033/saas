# 生产环境部署指南

本指南将帮助你将微服务 SAAS 平台部署到生产环境。

## 目录

1. [部署前准备](#部署前准备)
2. [Docker 部署](#docker-部署)
3. [Kubernetes 部署](#kubernetes-部署)
4. [配置管理](#配置管理)
5. [监控和日志](#监控和日志)
6. [安全最佳实践](#安全最佳实践)
7. [性能优化](#性能优化)
8. [备份和恢复](#备份和恢复)

---

## 部署前准备

### 环境要求

**生产服务器配置建议：**

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB | 50 GB SSD |
| 网络 | 100 Mbps | 1 Gbps |

**软件要求：**

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+ （或使用托管服务）
- Redis 7+ （可选）
- Nginx/Traefik（反向代理）
- SSL 证书

### 域名和 SSL

1. **注册域名**
   - 主域名：`yourdomain.com`
   - API 子域名：`api.yourdomain.com`
   - 管理后台：`admin.yourdomain.com`

2. **获取 SSL 证书**
   ```bash
   # 使用 Let's Encrypt
   sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
   ```

---

## Docker 部署

### 1. 准备生产配置文件

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: saas_postgres_prod
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - saas_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: saas_redis_prod
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - saas_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  registry:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        SERVICE_NAME: registry
    container_name: saas_registry_prod
    restart: always
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - saas_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  gateway:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        SERVICE_NAME: gateway
    container_name: saas_gateway_prod
    restart: always
    environment:
      - REGISTRY_URL=http://registry:8001
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - ENVIRONMENT=production
    depends_on:
      registry:
        condition: service_healthy
    networks:
      - saas_network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gateway.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.gateway.tls=true"
      - "traefik.http.routers.gateway.tls.certresolver=letsencrypt"

  core:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        SERVICE_NAME: core
    container_name: saas_core_prod
    restart: always
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - REGISTRY_URL=http://registry:8001
      - ENVIRONMENT=production
    depends_on:
      postgres:
        condition: service_healthy
      registry:
        condition: service_healthy
    networks:
      - saas_network

  frontend:
    build:
      context: ./frontend/admin
      dockerfile: ../../docker/Dockerfile.frontend
    container_name: saas_frontend_prod
    restart: always
    environment:
      - VITE_API_URL=https://api.yourdomain.com
    networks:
      - saas_network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`admin.yourdomain.com`)"
      - "traefik.http.routers.frontend.tls=true"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"

  traefik:
    image: traefik:v2.10
    container_name: saas_traefik
    restart: always
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourdomain.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_certs:/letsencrypt
    networks:
      - saas_network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  traefik_certs:
    driver: local

networks:
  saas_network:
    driver: bridge
```

### 2. 环境变量配置

创建 `.env.prod`：

```bash
# 数据库配置
POSTGRES_DB=saas_platform
POSTGRES_USER=saas_user
POSTGRES_PASSWORD=<strong-password-here>

# Redis 配置
REDIS_PASSWORD=<redis-password-here>

# 应用配置
SECRET_KEY=<generate-random-secret-key>
ENVIRONMENT=production

# CORS 配置
CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com

# JWT 配置
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 日志级别
LOG_LEVEL=INFO
```

**生成强密钥：**
```bash
# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成数据库密码
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 3. 部署步骤

```bash
# 1. 克隆代码
git clone https://github.com/your-repo/SAAS.git
cd SAAS

# 2. 配置环境变量
cp .env.prod .env
vim .env  # 修改所有配置

# 3. 构建镜像
docker-compose -f docker-compose.prod.yml build

# 4. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 5. 检查状态
docker-compose -f docker-compose.prod.yml ps

# 6. 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 7. 运行数据库迁移（首次部署）
docker-compose -f docker-compose.prod.yml exec core alembic upgrade head
```

### 4. 配置 Nginx（可选，如果不使用 Traefik）

创建 `/etc/nginx/sites-available/saas`:

```nginx
# API 网关
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# 管理后台
server {
    listen 80;
    server_name admin.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/admin.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.yourdomain.com/privkey.pem;

    root /var/www/saas/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/saas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Kubernetes 部署

### 1. 创建命名空间

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: saas-platform
```

### 2. ConfigMap 和 Secrets

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: saas-config
  namespace: saas-platform
data:
  REGISTRY_URL: "http://registry-service:8001"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
---
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: saas-secrets
  namespace: saas-platform
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/saas"
  SECRET_KEY: "your-secret-key"
  REDIS_PASSWORD: "your-redis-password"
```

### 3. 部署文件

**Registry 服务：**
```yaml
# registry-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: registry
  namespace: saas-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: registry
  template:
    metadata:
      labels:
        app: registry
    spec:
      containers:
      - name: registry
        image: your-registry/saas-registry:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: saas-secrets
              key: DATABASE_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: saas-secrets
              key: SECRET_KEY
        envFrom:
        - configMapRef:
            name: saas-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: registry-service
  namespace: saas-platform
spec:
  selector:
    app: registry
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

**Gateway 服务：**
```yaml
# gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: saas-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: your-registry/saas-gateway:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: saas-config
        - secretRef:
            name: saas-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: gateway-service
  namespace: saas-platform
spec:
  selector:
    app: gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### 4. Ingress 配置

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: saas-ingress
  namespace: saas-platform
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.yourdomain.com
    - admin.yourdomain.com
    secretName: saas-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway-service
            port:
              number: 8000
  - host: admin.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### 5. 部署到 K8s

```bash
# 应用配置
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# 部署服务
kubectl apply -f registry-deployment.yaml
kubectl apply -f gateway-deployment.yaml
kubectl apply -f core-deployment.yaml

# 配置 Ingress
kubectl apply -f ingress.yaml

# 检查状态
kubectl get pods -n saas-platform
kubectl get services -n saas-platform
kubectl get ingress -n saas-platform

# 查看日志
kubectl logs -f deployment/gateway -n saas-platform
```

---

## 配置管理

### 环境变量最佳实践

1. **不要在代码中硬编码敏感信息**
2. **使用环境变量或密钥管理服务**
3. **为不同环境使用不同的配置文件**

### 使用 HashiCorp Vault

```python
# backend/shared/vault_config.py
import hvac

def get_secrets():
    client = hvac.Client(url='https://vault.yourdomain.com')
    client.token = os.getenv('VAULT_TOKEN')

    secrets = client.secrets.kv.v2.read_secret_version(
        path='saas/production'
    )

    return secrets['data']['data']
```

---

## 监控和日志

### 1. Prometheus + Grafana

**docker-compose.monitoring.yml:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - saas_network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - saas_network

volumes:
  prometheus_data:
  grafana_data:

networks:
  saas_network:
    external: true
```

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'registry'
    static_configs:
      - targets: ['registry:8001']

  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8000']

  - job_name: 'core'
    static_configs:
      - targets: ['core:8002']
```

### 2. ELK Stack（日志管理）

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### 3. 应用监控代码

```python
# backend/shared/monitoring.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
import time

# 定义指标
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response

# 在 FastAPI 应用中使用
app = FastAPI()
app.add_middleware(MonitoringMiddleware)

@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

---

## 安全最佳实践

### 1. 网络安全

- ✅ 使用 HTTPS (TLS 1.2+)
- ✅ 配置防火墙规则
- ✅ 使用 VPC 或私有网络
- ✅ 定期更新安全补丁

### 2. 应用安全

- ✅ 使用强密码和定期轮换
- ✅ 启用 JWT 令牌过期
- ✅ 实施 RBAC 权限控制
- ✅ 输入验证和 SQL 注入防护
- ✅ XSS 防护
- ✅ CSRF 防护

### 3. 数据安全

- ✅ 加密敏感数据
- ✅ 定期备份
- ✅ 数据库访问控制
- ✅ 审计日志

### 4. 安全检查清单

```bash
# 1. 检查开放端口
sudo netstat -tulpn

# 2. 检查 SSL 配置
openssl s_client -connect api.yourdomain.com:443

# 3. 扫描漏洞
docker scan your-image:latest

# 4. 检查密码强度
python -c "import secrets; print(len(secrets.token_urlsafe(32)))"
```

---

## 性能优化

### 1. 数据库优化

```python
# 连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 添加索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_services_name ON services(name);
CREATE INDEX idx_services_active ON services(is_active);
```

### 2. Redis 缓存

```python
# backend/shared/cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host='redis',
    port=6379,
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)

def cached(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 尝试从缓存获取
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )

            return result
        return wrapper
    return decorator
```

### 3. 负载均衡

使用 Nginx 或 Traefik 配置负载均衡：

```nginx
upstream gateway_backend {
    least_conn;
    server gateway1:8000 weight=1;
    server gateway2:8000 weight=1;
    server gateway3:8000 weight=1;
}

server {
    location / {
        proxy_pass http://gateway_backend;
    }
}
```

---

## 备份和恢复

### 1. 数据库备份

**自动备份脚本：**
```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/saas_backup_$DATE.sql"

# 备份数据库
docker-compose exec -T postgres pg_dump -U saas_user saas_platform > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

**设置 Cron 任务：**
```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/backup-db.sh >> /var/log/backup.log 2>&1
```

### 2. 恢复数据库

```bash
# 解压备份
gunzip saas_backup_20240115_020000.sql.gz

# 恢复数据库
docker-compose exec -T postgres psql -U saas_user saas_platform < saas_backup_20240115_020000.sql
```

### 3. 备份到云存储

```bash
# 使用 rclone 备份到 S3
rclone sync /backups s3:your-bucket/saas-backups/
```

---

## CI/CD 流程

### GitHub Actions 示例

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push images
      run: |
        docker-compose -f docker-compose.prod.yml build
        docker-compose -f docker-compose.prod.yml push

    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/saas
          git pull
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
```

---

## 监控检查清单

部署后，确保以下监控项正常：

- [ ] 所有服务健康检查通过
- [ ] SSL 证书有效
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] 服务注册成功
- [ ] API 网关路由正常
- [ ] 日志收集正常
- [ ] 监控指标正常
- [ ] 备份任务运行
- [ ] 告警配置生效

---

## 故障恢复

### 快速回滚

```bash
# 1. 查看历史版本
docker-compose images

# 2. 回滚到上一个版本
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# 3. 或使用 Git 标签
git checkout v1.0.0
docker-compose -f docker-compose.prod.yml up -d --build
```

### 灾难恢复计划

1. **RTO (Recovery Time Objective)**: 目标恢复时间 < 1 小时
2. **RPO (Recovery Point Objective)**: 数据恢复点 < 24 小时
3. **定期演练**：每季度进行一次灾难恢复演练

---

**部署成功后**，记得测试所有关键功能，并监控系统运行状况。

更多帮助请参考：
- [架构文档](./ARCHITECTURE.md)
- [API 参考](./API_REFERENCE.md)
- [故障排查](../TROUBLESHOOTING.md)
