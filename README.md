# SpiderMind 🕷️

> 渐进式爬虫逆向工程框架 — 从零到一的完整采集项目交付系统

## 核心理念

**能用纯 Python 解决的问题，绝不引入浏览器。** SpiderMind 采用渐进式三层策略，按需升级工具复杂度，在效率和成功率之间找到最优解。

```
Stage 0: 目标站点指纹识别
   ↓
Stage 1: 纯 Python 请求探测 → 成功则直接交付
   ↓ (被反爬)
Stage 2: Playwright 补环境 + Node.js 本地代码还原
   ↓ (极端混淆)
Stage 3: jsreverser-mcp 深度逆向
   ↓
Stage 4: 项目脚手架 + 代码质量检查
   ↓
Stage 5: 开发文档 (DEV.md) 完整交付
```

## 与 spider-king 的区别

| 特性 | SpiderMind | spider-king |
|------|-----------|-------------|
| 浏览器工具 | **Playwright** | chrome-devtools |
| 逆向工具 | **jsreverser-mcp** | js-reverse |
| 策略 | **渐进式按需升级** | 直接进入逆向 |
| 纯 Python 优先 | ✅ | ❌ |
| 补环境方案 | ✅ 默认路径 | ❌ |
| 中文化交付 | ✅ 注释+文档 | 英文 |

## 使用方式

在 Codex 中，直接给出目标网站即可触发 SpiderMind：

```
帮我采集 https://example.com 的数据
```

Skill 会自动完成指纹识别 → 策略选择 → 逆向分析 → 代码交付全流程。

## 项目结构

```
spider-mind/
├── SKILL.md                      # 入口：方法论 & 路由
├── agents/openai.yaml            # Agent 配置
├── references/                   # 各阶段详细手册
│   ├── workflow-overview.md      # 6 阶段端到端流程图
│   ├── strategy-triage.md        # 策略决策树
│   ├── stage-1-pure-py.md        # 纯 Python 探测
│   ├── stage-2-env-patch.md      # Playwright 调试 + 环境补丁
│   ├── stage-3-jsreverser.md     # 深度逆向工程
│   ├── escalation-ladder.md      # 升级阶梯（防跳步）
│   ├── code-quality.md           # 交付前 QA 检查清单
│   ├── dev-doc.md                # DEV.md 开发文档模板
│   ├── project-scaffold.md       # 项目脚手架规范
│   ├── tool-playbook.md          # 工具选择与切换指南
│   ├── troubleshooting.md        # 环境问题排查
│   └── report-templates.md       # 各阶段报告模板
└── scripts/
    └── scaffold_project.py       # 一键生成项目目录
```

## 安装

将 `spider-mind/` 放入 Codex 的 skills 目录：

```
%CODEX_HOME%/skills/spider-mind/
```

或通过 skill-installer 安装。

## 环境要求

- Python 3.9+
- Node.js 18+
- Playwright（含 Chromium）
- jsreverser-mcp（MCP 服务）

## 许可

本项目仅供学习与研究使用。使用者应遵守目标网站的 robots.txt 及当地法律法规。

*Made with ❤️ for the scraping community.*
