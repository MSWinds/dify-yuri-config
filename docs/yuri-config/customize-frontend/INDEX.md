# 📑 前端定制文档索引

## 📖 所有文档

| 文档 | 说明 | 适合人群 | 阅读时间 |
|------|------|----------|----------|
| [.README_FIRST.md](./.README_FIRST.md) | 👋 欢迎指南 | 所有人 | 3 分钟 |
| [GETTING_STARTED.md](./GETTING_STARTED.md) | 🚀 5 分钟快速入门 | 新手 | 5 分钟 |
| [README.md](./README.md) | 📖 前端定制概览 | 所有人 | 5 分钟 |
| [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) | ⚡ 快速参考卡片 | 所有人 | 随时查阅 |
| [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) | 🛡️ 安全的本地开发指南 | 开发者 | 15 分钟 |
| [SUMMARY.md](./SUMMARY.md) | 📚 文档总览 | 所有人 | 5 分钟 |

## 🎯 按需求查找

### 我想快速上手
→ [GETTING_STARTED.md](./GETTING_STARTED.md) - 三步开始开发

### 我想了解配置
→ [README.md](./README.md) - Docker 配置和快速命令

### 我想深入学习
→ [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) - 完整开发指南

### 我想查命令
→ [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 命令速查表

### 我想看全局
→ [SUMMARY.md](./SUMMARY.md) - 文档总览和学习路径

### 我是新来的
→ [.README_FIRST.md](./.README_FIRST.md) - 从这里开始

## 🛠️ 开发脚本

位置：`scripts/dev-web.sh`

```bash
./scripts/dev-web.sh help     # 查看所有命令
./scripts/dev-web.sh setup    # 首次设置
./scripts/dev-web.sh dev      # 启动开发服务器
./scripts/dev-web.sh check    # 代码检查
./scripts/dev-web.sh test     # 运行测试
./scripts/dev-web.sh build    # 构建测试
./scripts/dev-web.sh deploy   # 部署到 Docker
./scripts/dev-web.sh full     # 完整发布流程
./scripts/dev-web.sh logs     # 查看日志
./scripts/dev-web.sh status   # 查看状态
./scripts/dev-web.sh clean    # 清理缓存
```

## 📂 关键文件位置

```
项目根目录/
├── web/                              # 前端源码
│   ├── app/                         # Next.js 页面和组件
│   ├── i18n/                        # 国际化文案
│   ├── .env.local                   # 本地环境变量（不提交）
│   └── package.json                 # 依赖管理
├── docker/
│   ├── docker-compose.yaml          # Docker 配置
│   └── .env                         # Docker 环境变量
├── scripts/
│   └── dev-web.sh                   # 开发脚本
└── docs/yuri-config/customize-frontend/  # 你在这里
    ├── .README_FIRST.md             # 欢迎指南
    ├── GETTING_STARTED.md           # 快速入门
    ├── README.md                    # 概览
    ├── SAFE_LOCAL_DEV.md            # 完整指南
    ├── QUICK_REFERENCE.md           # 快速参考
    ├── SUMMARY.md                   # 文档总览
    └── INDEX.md                     # 本文档
```

## 🎓 推荐学习顺序

### 第 1 阶段：入门（第 1 天）
1. [.README_FIRST.md](./.README_FIRST.md) - 了解整体结构
2. [GETTING_STARTED.md](./GETTING_STARTED.md) - 快速上手
3. 实践：运行 `./scripts/dev-web.sh setup && ./scripts/dev-web.sh dev`

### 第 2 阶段：实践（第 2-3 天）
1. [README.md](./README.md) - 了解配置和常见修改
2. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 熟悉常用命令
3. 实践：修改一个页面或组件

### 第 3 阶段：深入（第 4-7 天）
1. [SAFE_LOCAL_DEV.md](./SAFE_LOCAL_DEV.md) - 完整开发流程
2. [SUMMARY.md](./SUMMARY.md) - 了解最佳实践
3. 实践：完成一个完整的功能开发

### 第 4 阶段：精通（持续）
1. 阅读 `web/testing/testing.md` - 测试规范
2. 阅读 `web/AGENTS.md` - 开发规范
3. 贡献代码和文档

## 🔗 外部资源

- [Next.js 15 文档](https://nextjs.org/docs)
- [React 19 文档](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Dify 官方文档](https://docs.dify.ai)
- [Dify GitHub](https://github.com/langgenius/dify)

## 📊 文档统计

- 总文档数：7 个
- 总字数：约 15,000 字
- 代码示例：100+ 个
- 涵盖主题：
  - ✅ 环境设置
  - ✅ 开发流程
  - ✅ 代码检查
  - ✅ 测试
  - ✅ 构建
  - ✅ 部署
  - ✅ 故障排查
  - ✅ 最佳实践

## 🆘 获取帮助

1. **查看文档**：根据需求选择合适的文档
2. **运行诊断**：`./scripts/dev-web.sh status`
3. **查看日志**：`./scripts/dev-web.sh logs`
4. **搜索问题**：在文档中搜索关键词
5. **询问团队**：联系团队成员

## 📝 贡献文档

发现文档问题或有改进建议？

1. 创建 Issue 描述问题
2. 或直接提交 PR 修改文档
3. 遵循现有文档风格
4. 添加实际示例

---

**最后更新**: 2025-12-26  
**文档版本**: 1.0.0  
**维护者**: Dify Yuri Config Team

**开始探索**: [.README_FIRST.md](./.README_FIRST.md) 👋

