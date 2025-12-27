# 5 分钟快速入门

这是一个快速入门指南，帮助你在 5 分钟内开始前端开发。

## 📋 前置条件

确保你已经安装：
- Node.js >= v22.11.0
- pnpm v10.x
- Docker 和 Docker Compose

## 🚀 三步开始

### 步骤 1: 检查系统状态

```bash
./scripts/dev-web.sh status
```

如果看到错误，按照提示安装缺失的依赖。

### 步骤 2: 首次设置

```bash
./scripts/dev-web.sh setup
```

这会：
- ✅ 安装所有前端依赖
- ✅ 创建 `.env.local` 配置文件
- ✅ 准备开发环境

### 步骤 3: 启动开发服务器

```bash
./scripts/dev-web.sh dev
```

然后访问 http://localhost:3000 🎉

## 🎨 尝试修改

### 修改一个文案

1. 打开文件：
```bash
vim web/i18n/zh-Hans/common.ts
```

2. 找到并修改任意文案，例如：
```typescript
export const common = {
  welcome: '欢迎使用 Dify',  // 改成 '欢迎来到我的 Dify'
  // ...
}
```

3. 保存文件，浏览器会自动刷新！

### 修改一个样式

1. 打开任意组件文件，例如：
```bash
vim web/app/components/base/button/index.tsx
```

2. 修改样式类名或添加新样式

3. 保存文件，立即看到效果！

## ✅ 提交前检查

完成修改后，运行检查：

```bash
./scripts/dev-web.sh check
```

如果通过，你的代码就可以提交了！

## 🚢 部署到 Docker

测试完成后，部署到 Docker：

```bash
./scripts/dev-web.sh deploy
```

然后访问 http://localhost 查看生产版本。

## 📚 下一步

- 阅读 [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) 了解完整开发流程
- 查看 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) 学习更多命令
- 浏览 [SUMMARY.md](./SUMMARY.md) 查看所有文档

## 🆘 遇到问题？

运行诊断命令：
```bash
./scripts/dev-web.sh status
```

查看日志：
```bash
./scripts/dev-web.sh logs web
```

或查看 [故障排查指南](./SAFE_LOCAL_DEV.md#-常见问题排查)

---

**恭喜！** 你已经完成了快速入门 🎉

现在你可以：
- ✅ 启动开发服务器
- ✅ 修改前端代码
- ✅ 运行代码检查
- ✅ 部署到 Docker

继续探索其他文档，学习更多高级功能！

