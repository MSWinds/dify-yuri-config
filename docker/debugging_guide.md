# Dify 调试与管理指南

本指南用于快速管理 Dify 服务，特别是如何暴露数据库端口以便进行调试（查看 Redis/Postgres 数据）。

## 1. 启动所有服务（暴露端口调试模式）

**推荐使用**。此命令会启动主服务（API/Web）以及中间件（Redis/Postgres），并**自动暴露**数据库端口 (Redis: 6379, Postgres: 5432)，方便使用 VS Code 插件连接。

```bash
# 请在 docker/ 目录下执行
docker compose -f docker-compose.yaml -f docker-compose.middleware.yaml up -d
```

> **原理**：Dify 将服务拆分成了两个文件。主文件 (`docker-compose.yaml`) 负责业务，中间件文件 (`middleware.yaml`) 负责数据库并预置了端口映射。同时加载两个文件即可实现功能叠加。

## 2. 单独暴露/刷新中间件端口

如果你已经启动了 Dify，但发现连不上 Redis（端口没开），**不需要重启所有服务**，只需运行此命令“打补丁”：

```bash
# 只刷新 Redis, Weaviate 等中间件配置
docker compose -f docker-compose.middleware.yaml up -d
docker compose -f docker-compose.middleware.yaml down
```

## 3. 停止所有服务

```bash
# 同时停止主服务和中间件
docker compose -f docker-compose.yaml -f docker-compose.middleware.yaml down
```

## 4. 连接信息 (VS Code Database Client)

使用 VS Code 插件连接时的配置：

### Redis
*   **Host**: `127.0.0.1`
*   **Port**: `6379`
*   **Password**: `xxxx` (见 `.env` 中的 `REDIS_PASSWORD`)
*   **SSL/Cluster**: **不勾选**

### PostgreSQL
*   **Host**: `127.0.0.1`
*   **Port**: `5432`
*   **User**: `genaiclass` (见 `.env` 中的 `DB_USERNAME`)
*   **Password**: `xxxx` (见 `.env` 中的 `DB_PASSWORD`)
*   **Database**: `dify`

---

**注意**：
*   所有操作建议在项目根目录下的 `docker/` 文件夹中进行。
*   如果修改了 `.env` 文件，必须重新运行第 1 条中的启动命令才能生效。

## 5. 服务端口映射总览 (Port Map)

当开启所有调试端口时，以下端口会被暴露到宿主机（`localhost`）：

### 核心访问入口
*   **Web / API**: `80` (http) / `443` (https)
    *   这是用户和前端访问 Dify 的主要入口（通过 Nginx 转发）。
*   **API 后端直连**: `5001`
    *   用于直接调用后端 Python API，绕过 Nginx，适合开发调试。

### 数据存储与中间件
*   **PostgreSQL**: `5432`
    *   核心关系型数据库，存储用户、应用、配置等结构化数据。
*   **Redis**: `6379`
    *   缓存、Celery 任务队列、Pub/Sub 消息。
*   **Weaviate**: `8080` (HTTP) / `50051` (gRPC)
    *   （默认向量库）存储文档向量索引。

### 其他服务
*   **Sandbox**: `8194`
    *   代码沙箱服务，用于运行 Workflow 中的代码节点。
*   **SSRF Proxy**: `3128`
    *   安全代理，用于过滤 AI模型发出的外部网络请求。

