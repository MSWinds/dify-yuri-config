# 安全的前端本地开发指南

## 🎯 目标

在不破坏 Docker 环境的前提下，安全地进行前端开发和测试。

## 📋 前置要求

```bash
# 检查 Node.js 版本（必须 >= v22.11.0）
node --version

# 检查 pnpm 版本（必须 v10.x）
pnpm --version

# 如果没有 pnpm，安装它
npm install -g pnpm@10
```

## 🚀 快速开始

### 1️⃣ 首次设置

```bash
# 进入 web 目录
cd web

# 安装依赖（首次或 package.json 变更后）
pnpm install

# 创建本地环境变量文件
cp .env.example .env.local
```

### 2️⃣ 配置 `.env.local`

编辑 `web/.env.local`，连接到本地 Docker 后端：

```bash
# 开发环境配置
NEXT_PUBLIC_DEPLOY_ENV=DEVELOPMENT
NEXT_PUBLIC_EDITION=SELF_HOSTED

# 连接到本地 Docker 后端 API
# 注意：如果在虚拟机中开发，需要使用虚拟机的 IP 地址
# 本机开发使用: http://localhost/console/api
# 虚拟机开发使用: http://YOUR_VM_IP/console/api
NEXT_PUBLIC_API_PREFIX=http://localhost/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost/api

# Cookie 域名（本地开发留空）
NEXT_PUBLIC_COOKIE_DOMAIN=

# Sentry（本地开发留空）
NEXT_PUBLIC_SENTRY_DSN=
```

**⚠️ 虚拟机环境特别说明**：

如果你在虚拟机（如 Ubuntu VM）中开发，需要使用虚拟机的 IP 地址：

```bash
# 1. 获取虚拟机 IP
hostname -I | awk '{print $1}'
# 例如: 134.173.236.127

# 2. 使用虚拟机 IP 配置
NEXT_PUBLIC_API_PREFIX=http://134.173.236.127/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://134.173.236.127/api
```

这样浏览器才能从 Windows 主机访问虚拟机中的 Docker 服务。

### 3️⃣ 启动开发服务器

```bash
# 在 web 目录下
pnpm dev
```

访问 http://localhost:3000 查看前端界面。

## 🔄 开发工作流

### 场景 1: 只修改前端 UI/样式

```bash
# 1. 确保 Docker 后端正在运行
cd docker && docker-compose ps

# 2. 启动前端开发服务器
cd ../web && pnpm dev

# 3. 编辑文件，浏览器自动热重载
# 例如: web/app/account/(commonLayout)/account-page/index.tsx

# 4. 测试完成后，构建并部署到 Docker
cd ../docker
docker-compose build web && docker-compose up -d web
```

### 场景 2: 修改前端文案（i18n）

```bash
# 1. 编辑中文文案
vim web/i18n/zh-Hans/common.ts

# 2. 检查 i18n 完整性
cd web && pnpm check-i18n

# 3. 在开发服务器中测试
pnpm dev

# 4. 确认无误后部署
cd ../docker
docker-compose build web && docker-compose up -d web
```

### 场景 3: 同时修改前后端

```bash
# 终端 1: 启动前端开发服务器
cd web && pnpm dev

# 终端 2: 后端已在 Docker 中运行，修改后重启
cd docker
# 修改 api/services/account_service.py 等文件
docker-compose restart api worker

# 前端自动连接到 Docker 后端 API
```

## 🛡️ 安全检查清单

### ✅ 提交前必做

```bash
cd web

# 1. 代码格式检查和自动修复
pnpm lint:fix

# 2. TypeScript 类型检查
pnpm type-check:tsgo

# 3. 运行测试
pnpm test

# 4. 检查 i18n 完整性
pnpm check-i18n
```

### ✅ 构建前验证

```bash
# 本地构建测试（确保能成功构建）
cd web
pnpm build

# 如果构建成功，再部署到 Docker
cd ../docker
docker-compose build web && docker-compose up -d web
```

## 🔍 常见问题排查

### 问题 1: 前端无法连接后端 API

```bash
# 检查 Docker 后端是否运行
cd docker && docker-compose ps

# 检查 nginx 是否正常
docker-compose logs -f nginx

# 确认 .env.local 配置正确
cat web/.env.local | grep API_PREFIX
```

### 问题 2: pnpm install 失败

```bash
# 清理缓存重试
cd web
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 如果还是失败，检查 Node.js 版本
node --version  # 必须 >= v22.11.0
```

### 问题 3: 热重载不工作

```bash
# 重启开发服务器
cd web
# Ctrl+C 停止
pnpm dev

# 如果还是不行，清理 Next.js 缓存
rm -rf .next
pnpm dev
```

### 问题 4: TypeScript 报错

```bash
# 重新生成类型
cd web
pnpm type-check:tsgo

# 如果是第三方库的类型问题，检查 tsconfig.json
cat tsconfig.json
```

## 📁 项目结构

```
web/
├── app/                    # Next.js 15 App Router 页面
│   ├── account/           # 账户相关页面
│   ├── components/        # 共享组件
│   └── ...
├── i18n/                  # 国际化文案
│   ├── zh-Hans/          # 简体中文
│   ├── en-US/            # 英文
│   └── ...
├── service/               # API 服务层
├── utils/                 # 工具函数
├── .env.local            # 本地环境变量（不提交）
├── .env.example          # 环境变量模板
├── next.config.js        # Next.js 配置
├── package.json          # 依赖管理
└── tsconfig.json         # TypeScript 配置
```

## 🎨 开发技巧

### 使用 Storybook 开发组件

```bash
cd web
pnpm storybook
# 访问 http://localhost:6006
```

### 分析组件复杂度

```bash
cd web
pnpm analyze-component app/components/your-component/index.tsx
```

### 代码覆盖率测试

```bash
cd web
pnpm test:coverage
```

### 监听模式测试

```bash
cd web
pnpm test:watch
```

## 🔐 Git 工作流

### 创建功能分支

```bash
# 从 main 创建新分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 进行开发...
cd web
pnpm dev

# 提交前检查
pnpm lint:fix
pnpm type-check:tsgo
pnpm test

# 提交
git add .
git commit -m "feat: your feature description"
```

### 合并前验证

```bash
# 确保能成功构建
cd web
pnpm build

# 测试 Docker 构建
cd ../docker
docker-compose build web

# 如果都成功，推送分支
git push origin feature/your-feature-name
```

## 🚨 不要做的事

❌ **不要直接修改 Docker 容器内的文件**
```bash
# 错误示例
docker-compose exec web vi /app/web/app/layout.tsx
```

❌ **不要提交 `.env.local` 文件**
```bash
# .env.local 已在 .gitignore 中，不要强制添加
git add -f .env.local  # ❌ 不要这样做
```

❌ **不要跳过 lint 和 type-check**
```bash
# 不要这样提交
git commit --no-verify  # ❌ 跳过 pre-commit hooks
```

❌ **不要在生产环境使用开发服务器**
```bash
# 生产环境必须使用构建后的版本
pnpm build && pnpm start  # ✅ 正确
pnpm dev                   # ❌ 仅用于开发
```

## 📊 性能优化

### 开发服务器优化

```bash
# 使用 Turbopack（已在 package.json 中配置）
pnpm dev  # 自动使用 --turbopack

# 增加 Node.js 内存（如果需要）
export NODE_OPTIONS="--max-old-space-size=8192"
pnpm dev
```

### 构建优化

```bash
# 分析构建产物大小
cd web
pnpm analyze

# 查看报告
open .next/analyze/client.html
```

## 🔄 环境切换

### 开发环境 → Docker 环境

```bash
# 1. 停止开发服务器（Ctrl+C）

# 2. 构建并部署到 Docker
cd docker
docker-compose build web && docker-compose up -d web

# 3. 访问 http://localhost（通过 nginx）
```

### Docker 环境 → 开发环境

```bash
# 1. 确保 Docker 后端运行
cd docker && docker-compose ps

# 2. 启动前端开发服务器
cd ../web && pnpm dev

# 3. 访问 http://localhost:3000（直接访问前端）
```

## 📚 相关文档

- [Next.js 15 文档](https://nextjs.org/docs)
- [React 19 文档](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Vitest 测试框架](https://vitest.dev/)
- [项目测试指南](../../../web/testing/testing.md)

## 💡 最佳实践

1. **始终在开发服务器中测试**：不要直接在 Docker 中开发
2. **频繁运行 lint 和 type-check**：在提交前捕获问题
3. **编写测试**：为新功能和修复的 bug 编写测试
4. **使用 Git 分支**：不要直接在 main 分支开发
5. **小步提交**：每个提交只做一件事
6. **代码审查**：合并前请团队成员审查
7. **文档更新**：修改功能时同步更新文档

## 🆘 获取帮助

如果遇到问题：

1. 查看 [web/README.md](../../../web/README.md)
2. 查看 [web/testing/testing.md](../../../web/testing/testing.md)
3. 检查 Docker 日志：`docker-compose logs -f web`
4. 检查开发服务器日志（终端输出）
5. 在项目 GitHub Issues 中搜索类似问题

## 🎓 学习资源

### 推荐阅读顺序

1. [web/README.md](../../../web/README.md) - 项目基础
2. [web/testing/testing.md](../../../web/testing/testing.md) - 测试规范
3. [web/AGENTS.md](../../../web/AGENTS.md) - 开发规范
4. 本文档 - 安全开发流程

### 示例代码

- 工具函数测试：`web/utils/classnames.spec.ts`
- 组件测试：`web/app/components/base/button/index.spec.tsx`
- 复杂组件：`web/app/account/(commonLayout)/account-page/index.tsx`

---

**记住**：本地开发是为了快速迭代和测试，最终部署必须通过 Docker 构建！

