# 前端定制文档总览

## 📚 文档结构

本目录包含 Dify 前端定制和开发的完整指南。

### 文档列表

1. **[GETTING_STARTED.md](./GETTING_STARTED.md)** - 5 分钟快速入门 🚀
   - 三步开始开发
   - 尝试第一次修改
   - 快速部署

2. **[README.md](./README.md)** - 前端定制概览
   - Docker 配置说明
   - 快速命令参考
   - 常见修改场景

3. **[SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md)** - 安全的本地开发指南 ⭐
   - 完整的开发环境设置
   - 详细的工作流程
   - 安全检查清单
   - 故障排查指南
   - 最佳实践

4. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - 快速参考卡片
   - 常用命令速查
   - 关键文件位置
   - 环境变量配置
   - 常见问题解决

## 🎯 快速导航

### 我想...

#### 首次设置开发环境
→ 阅读 [GETTING_STARTED.md](./GETTING_STARTED.md) - 5 分钟快速入门 🚀  
→ 或阅读 [SAFE_LOCAL_DEV.md - 快速开始](./SAFE_LOCAL_DEV.md#-快速开始)  
→ 运行 `./scripts/dev-web.sh setup`

#### 开始开发前端
→ 阅读 [SAFE_LOCAL_DEV.md - 开发工作流](./SAFE_LOCAL_DEV.md#-开发工作流)  
→ 运行 `./scripts/dev-web.sh dev`

#### 修改 UI 界面
→ 阅读 [SAFE_LOCAL_DEV.md - 场景 1](./SAFE_LOCAL_DEV.md#场景-1-只修改前端-ui样式)  
→ 编辑 `web/app/` 下的文件

#### 修改中文文案
→ 阅读 [SAFE_LOCAL_DEV.md - 场景 2](./SAFE_LOCAL_DEV.md#场景-2-修改前端文案i18n)  
→ 编辑 `web/i18n/zh-Hans/` 下的文件

#### 部署到 Docker
→ 阅读 [README.md - 快速命令](./README.md#-快速命令)  
→ 运行 `./scripts/dev-web.sh deploy`

#### 查找常用命令
→ 查看 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

#### 解决问题
→ 查看 [SAFE_LOCAL_DEV.md - 常见问题排查](./SAFE_LOCAL_DEV.md#-常见问题排查)  
→ 查看 [QUICK_REFERENCE.md - 常见问题](./QUICK_REFERENCE.md#-常见问题)

## 🛠️ 开发工具

### 开发脚本

我们提供了一个便捷的开发脚本 `scripts/dev-web.sh`，包含以下功能：

```bash
./scripts/dev-web.sh setup      # 首次设置
./scripts/dev-web.sh dev        # 启动开发服务器
./scripts/dev-web.sh check      # 代码检查
./scripts/dev-web.sh test       # 运行测试
./scripts/dev-web.sh build      # 构建测试
./scripts/dev-web.sh deploy     # 部署到 Docker
./scripts/dev-web.sh full       # 完整发布流程
./scripts/dev-web.sh logs       # 查看日志
./scripts/dev-web.sh status     # 查看状态
./scripts/dev-web.sh help       # 帮助信息
```

### VSCode 配置

推荐安装的扩展：
- ESLint
- TypeScript and JavaScript Language Features
- Tailwind CSS IntelliSense
- i18n Ally

配置文件位置：`web/.vscode/settings.example.json`

## 📖 学习路径

### 新手入门

1. **快速开始**：阅读 [GETTING_STARTED.md](./GETTING_STARTED.md) - 5 分钟上手 🚀
2. **了解配置**：阅读 [README.md](./README.md) 了解整体配置
3. **深入学习**：阅读 [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) 完整开发指南
4. **命令速查**：查看 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) 熟悉常用命令

### 进阶开发

1. 深入阅读 [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) 全文
2. 了解项目结构和文件组织
3. 学习 Git 工作流和分支管理
4. 掌握测试编写和运行
5. 了解 Docker 构建和部署流程

### 高级主题

1. 阅读 `web/testing/testing.md` 了解测试规范
2. 阅读 `web/AGENTS.md` 了解开发规范
3. 学习 Next.js 15 和 React 19 新特性
4. 优化构建性能和运行时性能
5. 贡献代码和文档

## 🔗 相关资源

### 项目文档

- [Web README](../../../web/README.md) - 前端项目说明
- [Web Testing Guide](../../../web/testing/testing.md) - 测试指南
- [Web AGENTS.md](../../../web/AGENTS.md) - 开发规范
- [Classroom Mode Changes](../class/CLASSROOM_CHANGES.md) - 教室模式修改记录

### 外部文档

- [Next.js 15 文档](https://nextjs.org/docs)
- [React 19 文档](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [pnpm](https://pnpm.io/)
- [Vitest](https://vitest.dev/)
- [Docker](https://docs.docker.com/)

## 💡 最佳实践总结

### 开发流程

1. ✅ 始终在本地开发服务器测试
2. ✅ 频繁运行 lint 和 type-check
3. ✅ 提交前运行完整检查
4. ✅ 使用 Git 分支开发
5. ✅ 编写测试覆盖新功能
6. ✅ 更新相关文档

### 代码质量

1. ✅ 遵循 ESLint 规则
2. ✅ 使用 TypeScript 严格模式
3. ✅ 避免使用 `any` 类型
4. ✅ 编写清晰的注释
5. ✅ 保持函数简洁
6. ✅ 提取可复用组件

### 性能优化

1. ✅ 使用 Next.js 图片优化
2. ✅ 实现代码分割
3. ✅ 避免不必要的重渲染
4. ✅ 使用 React.memo 和 useMemo
5. ✅ 优化包体积
6. ✅ 启用生产构建优化

### 安全实践

1. ✅ 不提交敏感信息
2. ✅ 使用环境变量
3. ✅ 验证用户输入
4. ✅ 防止 XSS 攻击
5. ✅ 使用 HTTPS
6. ✅ 定期更新依赖

## 🆘 获取帮助

### 遇到问题时

1. 查看 [SAFE_LOCAL_DEV.md - 常见问题排查](./SAFE_LOCAL_DEV.md#-常见问题排查)
2. 查看 [QUICK_REFERENCE.md - 常见问题](./QUICK_REFERENCE.md#-常见问题)
3. 运行 `./scripts/dev-web.sh status` 检查系统状态
4. 查看日志：`./scripts/dev-web.sh logs`
5. 在项目 GitHub Issues 中搜索
6. 询问团队成员

### 报告问题

提供以下信息：
- 问题描述
- 复现步骤
- 错误日志
- 系统环境（Node.js、pnpm、Docker 版本）
- 相关配置文件

## 📝 文档维护

### 更新文档

当进行以下更改时，请更新相应文档：

- 添加新功能 → 更新 SAFE_LOCAL_DEV.md
- 修改命令 → 更新 QUICK_REFERENCE.md
- 改变配置 → 更新 README.md
- 添加脚本 → 更新所有相关文档

### 文档规范

- 使用清晰的标题层级
- 提供代码示例
- 包含实际的命令输出
- 添加截图（如果有帮助）
- 保持内容同步更新

## 🎓 贡献指南

欢迎贡献文档改进！

1. Fork 项目
2. 创建功能分支
3. 修改文档
4. 提交 Pull Request
5. 等待审查

---

**最后更新**: 2025-12-26  
**维护者**: Dify Yuri Config Team

如有疑问，请查看具体文档或联系团队成员。

