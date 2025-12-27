# 前端开发快速参考

## ⚡ 常用命令速查

### 本地开发

```bash
# 首次设置
cd web
pnpm install
cp .env.example .env.local
# 编辑 .env.local 配置后端 API

# 启动开发服务器
pnpm dev                    # http://localhost:3000

# 代码检查
pnpm lint:fix              # 自动修复 lint 问题
pnpm type-check:tsgo       # TypeScript 类型检查
pnpm test                  # 运行测试
pnpm check-i18n            # 检查国际化文案

# 构建测试
pnpm build                 # 本地构建测试
```

### Docker 部署

```bash
# 重新构建并部署前端
cd docker
docker-compose build web && docker-compose up -d web

# 查看日志
docker-compose logs -f web

# 重启服务
docker-compose restart web

# 完全重建
docker-compose down && docker-compose up -d --build
```

## 📁 关键文件位置

```
web/
├── app/                           # 页面和组件
│   ├── account/                  # 账户页面
│   ├── components/base/          # 基础组件
│   └── layout.tsx                # 根布局
├── i18n/                         # 国际化
│   ├── zh-Hans/                  # 简体中文
│   └── en-US/                    # 英文
├── service/                      # API 服务
├── .env.local                    # 本地环境变量（不提交）
└── next.config.js                # Next.js 配置

docker/
├── docker-compose.yaml           # Docker 配置
└── .env                          # Docker 环境变量
```

## 🔧 环境变量配置

### 本地开发 (`web/.env.local`)

```bash
NEXT_PUBLIC_DEPLOY_ENV=DEVELOPMENT
NEXT_PUBLIC_EDITION=SELF_HOSTED
NEXT_PUBLIC_API_PREFIX=http://localhost/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost/api
NEXT_PUBLIC_COOKIE_DOMAIN=
```

### Docker 生产 (`docker/.env`)

```bash
CONSOLE_API_URL=http://api:5001
APP_API_URL=http://api:5001
# 其他配置见 docker/.env
```

## 🚦 开发流程

### 标准流程

```
1. 创建分支
   git checkout -b feature/xxx

2. 本地开发
   cd web && pnpm dev
   
3. 修改代码
   编辑文件，浏览器自动刷新

4. 提交前检查
   pnpm lint:fix
   pnpm type-check:tsgo
   pnpm test

5. 本地构建测试
   pnpm build

6. Docker 构建测试
   cd ../docker
   docker-compose build web

7. 提交代码
   git add .
   git commit -m "feat: xxx"
   git push origin feature/xxx
```

## 🐛 常见问题

### API 连接失败

```bash
# 检查后端是否运行
cd docker && docker-compose ps

# 检查 nginx 日志
docker-compose logs -f nginx

# 确认环境变量
cat web/.env.local | grep API_PREFIX
```

### 热重载不工作

```bash
cd web
rm -rf .next
pnpm dev
```

### 依赖安装失败

```bash
cd web
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### TypeScript 报错

```bash
cd web
pnpm type-check:tsgo
# 根据错误提示修复
```

## 📝 修改示例

### 修改 UI 组件

```bash
# 1. 找到组件文件
vim web/app/components/base/button/index.tsx

# 2. 在开发服务器中测试
cd web && pnpm dev

# 3. 部署到 Docker
cd ../docker
docker-compose build web && docker-compose up -d web
```

### 修改中文文案

```bash
# 1. 编辑文案文件
vim web/i18n/zh-Hans/common.ts

# 2. 检查完整性
cd web && pnpm check-i18n

# 3. 测试并部署
pnpm dev  # 测试
cd ../docker && docker-compose build web && docker-compose up -d web
```

### 修改页面逻辑

```bash
# 1. 编辑页面文件
vim web/app/account/(commonLayout)/account-page/index.tsx

# 2. 运行类型检查
cd web && pnpm type-check:tsgo

# 3. 运行测试
pnpm test

# 4. 部署
cd ../docker && docker-compose build web && docker-compose up -d web
```

## 🎯 提交前清单

```bash
cd web

# ✅ 代码格式
pnpm lint:fix

# ✅ 类型检查
pnpm type-check:tsgo

# ✅ 测试通过
pnpm test

# ✅ i18n 完整
pnpm check-i18n

# ✅ 能成功构建
pnpm build

# ✅ Docker 构建成功
cd ../docker && docker-compose build web
```

## 🔍 调试技巧

### 查看详细日志

```bash
# 开发服务器日志
cd web && pnpm dev  # 终端输出

# Docker 日志
cd docker
docker-compose logs -f web
docker-compose logs -f api
docker-compose logs -f nginx
```

### 进入容器调试

```bash
cd docker
docker-compose exec web sh
docker-compose exec api bash
```

### 查看构建过程

```bash
cd docker
docker-compose build --no-cache --progress=plain web
```

## 🔗 相关链接

- [完整开发指南](./SAFE_LOCAL_DEV.md)
- [前端定制指南](./README.md)
- [项目测试文档](../../../web/testing/testing.md)
- [Web README](../../../web/README.md)

## 💡 小贴士

1. **始终在本地开发服务器测试**，不要直接在 Docker 中修改
2. **频繁运行 `pnpm lint:fix`**，保持代码风格一致
3. **提交前必须通过所有检查**，避免 CI 失败
4. **使用 Git 分支开发**，保护 main 分支
5. **小步提交**，便于回滚和审查
6. **编写测试**，提高代码质量
7. **更新文档**，帮助团队成员

---

**快速帮助**: 遇到问题先查看 [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) 的"常见问题排查"部分

