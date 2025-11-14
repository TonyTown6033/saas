# API 参考手册

本文档提供所有核心 API 的详细说明和使用示例。

## 目录

1. [服务注册中心 API](#服务注册中心-api)
2. [核心服务 API](#核心服务-api)
3. [API 网关](#api-网关)
4. [通用响应格式](#通用响应格式)
5. [错误代码](#错误代码)

---

## 服务注册中心 API

基础 URL: `http://localhost:8001`

### 注册服务

注册一个新的微服务到注册中心。

**端点:** `POST /api/registry/register`

**请求体:**
```json
{
  "name": "my-service",
  "display_name": "我的服务",
  "description": "服务描述",
  "version": "1.0.0",
  "host": "localhost",
  "port": 8100,
  "base_path": "/",
  "health_check_url": "/health",
  "service_metadata": {
    "author": "Your Name",
    "category": "business"
  },
  "tags": ["demo", "example"],
  "requires_auth": false,
  "endpoints": [
    {
      "path": "/hello",
      "method": "GET",
      "description": "问候端点",
      "is_public": true
    }
  ]
}
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-service",
  "display_name": "我的服务",
  "version": "1.0.0",
  "host": "localhost",
  "port": 8100,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_heartbeat": "2024-01-15T10:30:00Z"
}
```

**curl 示例:**
```bash
curl -X POST http://localhost:8001/api/registry/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-service",
    "display_name": "我的服务",
    "version": "1.0.0",
    "host": "localhost",
    "port": 8100,
    "base_path": "/",
    "health_check_url": "/health",
    "service_metadata": {},
    "tags": ["demo"],
    "requires_auth": false,
    "endpoints": []
  }'
```

### 发送心跳

保持服务活跃状态。建议每 30 秒发送一次。

**端点:** `POST /api/registry/heartbeat`

**请求体:**
```json
{
  "service_id": "my-service",
  "status": "healthy"
}
```

**响应示例:**
```json
{
  "message": "心跳已更新",
  "service_id": "my-service",
  "last_heartbeat": "2024-01-15T10:31:00Z"
}
```

**curl 示例:**
```bash
curl -X POST http://localhost:8001/api/registry/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "my-service"
  }'
```

### 获取服务列表

获取所有已注册的活跃服务。

**端点:** `GET /api/registry/services`

**查询参数:**
- `is_active` (可选): 过滤活跃/不活跃服务 (true/false)
- `tag` (可选): 按标签过滤

**响应示例:**
```json
{
  "total": 3,
  "services": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "core-service",
      "display_name": "核心服务",
      "version": "1.0.0",
      "host": "localhost",
      "port": 8002,
      "is_active": true,
      "last_heartbeat": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**curl 示例:**
```bash
# 获取所有服务
curl http://localhost:8001/api/registry/services

# 只获取活跃服务
curl http://localhost:8001/api/registry/services?is_active=true

# 按标签过滤
curl http://localhost:8001/api/registry/services?tag=demo
```

### 获取服务详情

获取指定服务的详细信息。

**端点:** `GET /api/registry/services/{service_id}`

**路径参数:**
- `service_id`: 服务 ID 或服务名称

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-service",
  "display_name": "我的服务",
  "description": "服务描述",
  "version": "1.0.0",
  "host": "localhost",
  "port": 8100,
  "base_path": "/",
  "health_check_url": "/health",
  "is_active": true,
  "service_metadata": {
    "author": "Your Name"
  },
  "tags": ["demo"],
  "endpoints": [
    {
      "id": 1,
      "path": "/hello",
      "method": "GET",
      "description": "问候端点",
      "is_public": true
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "last_heartbeat": "2024-01-15T10:31:00Z"
}
```

**curl 示例:**
```bash
# 按名称获取
curl http://localhost:8001/api/registry/services/my-service

# 按 ID 获取
curl http://localhost:8001/api/registry/services/550e8400-e29b-41d4-a716-446655440000
```

### 注销服务

从注册中心移除服务。

**端点:** `POST /api/registry/deregister/{service_id}`

**路径参数:**
- `service_id`: 服务 ID 或服务名称

**响应示例:**
```json
{
  "message": "服务已注销",
  "service_id": "my-service"
}
```

**curl 示例:**
```bash
curl -X POST http://localhost:8001/api/registry/deregister/my-service
```

---

## 核心服务 API

基础 URL: `http://localhost:8002`

### 用户注册

创建新用户账户。

**端点:** `POST /auth/register`

**请求体:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "user"
}
```

**字段说明:**
- `username`: 用户名（必填，唯一）
- `email`: 邮箱（必填，唯一）
- `password`: 密码（必填，至少 8 字符）
- `role`: 角色（可选，默认 "user"）
  - `super_admin`: 超级管理员
  - `tenant_admin`: 租户管理员
  - `user`: 普通用户

**响应示例:**
```json
{
  "id": "b302562b-b182-4527-95c5-68276f3a809d",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**curl 示例:**
```bash
curl -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

### 用户登录

获取访问令牌。

**端点:** `POST /auth/login`

**请求体:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**响应示例:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**字段说明:**
- `access_token`: 访问令牌（有效期 30 分钟）
- `refresh_token`: 刷新令牌（有效期 7 天）
- `token_type`: 令牌类型（始终为 "bearer"）
- `expires_in`: 访问令牌过期时间（秒）

**curl 示例:**
```bash
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

### 刷新令牌

使用刷新令牌获取新的访问令牌。

**端点:** `POST /auth/refresh`

**请求体:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应示例:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**curl 示例:**
```bash
curl -X POST http://localhost:8002/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token"
  }'
```

### 获取当前用户信息

获取当前登录用户的详细信息（需要认证）。

**端点:** `GET /auth/me`

**请求头:**
```
Authorization: Bearer {access_token}
```

**响应示例:**
```json
{
  "id": "b302562b-b182-4527-95c5-68276f3a809d",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "tenant_id": null,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T11:00:00Z"
}
```

**curl 示例:**
```bash
# 先登录获取令牌
TOKEN=$(curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# 使用令牌获取用户信息
curl http://localhost:8002/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 创建租户

创建新租户（需要 super_admin 权限）。

**端点:** `POST /tenants`

**请求头:**
```
Authorization: Bearer {access_token}
```

**请求体:**
```json
{
  "name": "acme-corp",
  "display_name": "Acme Corporation",
  "config": {
    "max_users": 100,
    "features": ["feature1", "feature2"]
  },
  "enabled_services": ["demo-service", "analytics-service"]
}
```

**响应示例:**
```json
{
  "id": "tenant-uuid",
  "name": "acme-corp",
  "display_name": "Acme Corporation",
  "config": {
    "max_users": 100,
    "features": ["feature1", "feature2"]
  },
  "enabled_services": ["demo-service", "analytics-service"],
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**curl 示例:**
```bash
curl -X POST http://localhost:8002/tenants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "name": "acme-corp",
    "display_name": "Acme Corporation",
    "config": {},
    "enabled_services": []
  }'
```

### 获取租户列表

获取所有租户（需要 super_admin 权限）。

**端点:** `GET /tenants`

**请求头:**
```
Authorization: Bearer {access_token}
```

**查询参数:**
- `skip`: 跳过记录数（默认 0）
- `limit`: 返回记录数（默认 100）
- `is_active`: 过滤活跃状态 (true/false)

**响应示例:**
```json
{
  "total": 10,
  "tenants": [
    {
      "id": "tenant-uuid",
      "name": "acme-corp",
      "display_name": "Acme Corporation",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**curl 示例:**
```bash
# 获取所有租户
curl http://localhost:8002/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 分页查询
curl "http://localhost:8002/tenants?skip=0&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## API 网关

基础 URL: `http://localhost:8000`

API 网关是所有微服务的统一入口点。

### 路由规则

网关使用以下路由模式转发请求：

```
http://gateway/api/{service_name}/{path}
           ↓
http://{service_host}:{service_port}/{base_path}/{path}
```

**示例:**

```bash
# 请求
GET http://localhost:8000/api/demo-service/items

# 转发到
GET http://localhost:8003/items
```

### 通过网关访问服务

**示例 1: 获取演示服务的项目列表**

```bash
curl http://localhost:8000/api/demo-service/items
```

**示例 2: 创建新项目**

```bash
curl -X POST http://localhost:8000/api/demo-service/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新项目",
    "description": "项目描述",
    "price": 99.99
  }'
```

**示例 3: 带认证的请求**

```bash
# 先登录获取令牌
TOKEN=$(curl -X POST http://localhost:8000/api/core/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 使用令牌访问受保护的端点
curl http://localhost:8000/api/my-service/protected \
  -H "Authorization: Bearer $TOKEN"
```

### 查看可用服务

```bash
curl http://localhost:8000/gateway/services
```

**响应示例:**
```json
{
  "total": 3,
  "services": [
    {
      "name": "demo-service",
      "display_name": "演示服务",
      "version": "1.0.0",
      "base_url": "http://localhost:8003",
      "is_active": true
    }
  ]
}
```

---

## 通用响应格式

### 成功响应

```json
{
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误响应

```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 错误代码

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源未找到 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 常见错误代码

| 错误代码 | 说明 | 解决方案 |
|---------|------|----------|
| `INVALID_CREDENTIALS` | 用户名或密码错误 | 检查登录凭据 |
| `USER_NOT_FOUND` | 用户不存在 | 确认用户名 |
| `USER_ALREADY_EXISTS` | 用户已存在 | 使用不同的用户名 |
| `TOKEN_EXPIRED` | 令牌已过期 | 使用刷新令牌获取新令牌 |
| `INVALID_TOKEN` | 令牌无效 | 重新登录 |
| `SERVICE_NOT_FOUND` | 服务未找到 | 检查服务是否已注册 |
| `SERVICE_UNAVAILABLE` | 服务不可用 | 等待服务恢复或联系管理员 |
| `INSUFFICIENT_PERMISSIONS` | 权限不足 | 联系管理员分配权限 |

---

## 完整示例

### 完整的用户注册和认证流程

```bash
#!/bin/bash

# 1. 注册新用户
echo "注册新用户..."
curl -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# 2. 登录获取令牌
echo -e "\n\n登录..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }')

# 提取访问令牌
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "访问令牌: $ACCESS_TOKEN"

# 3. 获取用户信息
echo -e "\n\n获取用户信息..."
curl http://localhost:8002/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. 访问受保护的服务
echo -e "\n\n访问受保护的服务..."
curl http://localhost:8000/api/my-service/protected \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 创建和测试插件服务

```bash
#!/bin/bash

# 1. 注册服务
echo "注册服务..."
curl -X POST http://localhost:8001/api/registry/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-service",
    "display_name": "测试服务",
    "version": "1.0.0",
    "host": "localhost",
    "port": 8200,
    "base_path": "/",
    "service_metadata": {},
    "tags": ["test"],
    "requires_auth": false,
    "endpoints": [
      {
        "path": "/test",
        "method": "GET",
        "description": "测试端点",
        "is_public": true
      }
    ]
  }'

# 2. 发送心跳
echo -e "\n\n发送心跳..."
curl -X POST http://localhost:8001/api/registry/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "test-service"
  }'

# 3. 验证服务已注册
echo -e "\n\n查看服务列表..."
curl http://localhost:8001/api/registry/services

# 4. 通过网关访问服务
echo -e "\n\n通过网关访问..."
curl http://localhost:8000/api/test-service/test

# 5. 注销服务
echo -e "\n\n注销服务..."
curl -X POST http://localhost:8001/api/registry/deregister/test-service
```

---

## 更多资源

- 📖 [新手完全指南](./新手完全指南.md)
- 🔌 [插件开发指南](./PLUGIN_DEVELOPMENT.md)
- 🏗️ [架构设计文档](./ARCHITECTURE.md)
- 🐛 [故障排查](../TROUBLESHOOTING.md)

**需要帮助？** 查看我们的 [文档](../README.md) 或提交 Issue。
