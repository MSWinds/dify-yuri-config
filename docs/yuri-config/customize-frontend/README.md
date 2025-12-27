# Dify 前端定制指南

## 📌 配置说明

已将 `docker/docker-compose.yaml` 中的 web 服务从官方镜像改为本地源码构建，支持完全自定义前端。

```yaml
web:
  build:
    context: ../web
    dockerfile: Dockerfile
  # image: langgenius/dify-web:1.11.2  # 需要时可切回官方镜像
```

**优点**：完全可定制 UI、文案、样式  
**代价**：首次构建需要 5-10 分钟

## 🚀 快速命令

```bash
# 首次启动（构建所有服务）
cd docker && docker-compose up -d --build

# 修改前端后重新构建
cd docker && docker-compose build web && docker-compose up -d web

# 修改后端后重启（无需构建）
cd docker && docker-compose restart api worker

# 查看日志
docker-compose logs -f web
docker-compose logs -f api
```

## 📝 常见修改

### 修改 UI 界面
```bash
# 编辑文件
vim web/app/account/(commonLayout)/account-page/index.tsx

# 重新构建
cd docker && docker-compose build web && docker-compose up -d web
```

### 修改中文文案
```bash
# 编辑文件
vim web/i18n/zh-Hans/common.ts

# 重新构建
cd docker && docker-compose build web && docker-compose up -d web
```

### 修改后端逻辑
```bash
# 编辑文件
vim api/services/account_service.py

# 重启服务（无需构建）
cd docker && docker-compose restart api worker
```

### 修改环境变量
```bash
# 编辑文件
vim docker/.env

# 重启服务
cd docker && docker-compose up -d
```

## 🔧 开发模式（推荐频繁修改时使用）

### 前端开发
```bash
cd web
pnpm install
pnpm dev  # 访问 http://localhost:3000
```

### 后端开发
```bash
cd api
uv sync
uv run flask run --debug
```

## ⚡ 优化技巧

### 加速构建
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
cd docker && docker-compose build web
```

### 清理缓存
```bash
docker builder prune -a
docker image prune -a
```

## 🐛 故障排查

```bash
# 查看详细构建日志
docker-compose build --no-cache --progress=plain web

# 查看服务日志
docker-compose logs -f

# 进入容器调试
docker-compose exec api bash
docker-compose exec web sh

# 完全重建
docker-compose down -v && docker-compose up -d --build
```

## 🔄 切回官方镜像

编辑 `docker/docker-compose.yaml`：
```yaml
web:
  # build:
  #   context: ../web
  #   dockerfile: Dockerfile
  image: langgenius/dify-web:1.11.2
```

然后重启：
```bash
cd docker && docker-compose up -d web
```

## 📊 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 磁盘空间 10GB+
- 内存 4GB+（建议 8GB+）

## 🔐 安全建议

1. 修改 `docker/.env` 中的默认密码
2. 配置 HTTPS 和 SSL 证书
3. 定期备份数据库和配置
4. 使用 Git 管理代码变更

## 📚 参考资源

- [官方文档](https://docs.dify.ai)
- [GitHub Issues](https://github.com/langgenius/dify/issues)
- [社区讨论](https://github.com/langgenius/dify/discussions)

