# SpiderMind 🕷️

> 从目标 URL 到可维护的爬虫项目，全自动走完结构侦察 → 逆向决策 → 代码实现 → 质量检查 → 文档输出。内置验证码自动处理流水线。不是一次性脚本，是完整的工程交付。

## 为什么需要 SpiderMind

大多数爬虫工具给你的是一个「裸脚本」——跑完就扔，换个目标又得从头来。没有日志、没有配置分离、没有异常处理、没有注释，两周后连自己都看不懂。

SpiderMind 把爬虫逆向从「手艺活」变成了「标准化工程」：

- 🔍 **结构化侦察** — 站点架构、反爬指纹、请求链路、数据画像，动手前先建立系统认知
- 📦 **项目脚手架** — 目录结构、虚拟环境、日志系统、配置分离、存储层，一键生成
- 🖼️ **验证码自动处理** — Playwright 截图 + AI 预处理增强（锐化/放大/去噪）+ ddddocr 识别，最大化自动化率
- 🧪 **质量门禁** — 独立环境重建验证、编码检查、异常处理审查、注释完整性扫描，不通过不交付
- 📝 **开发文档** — 逆向推理全记录、关键代码解析、踩坑复盘、执行流程图，可交接可维护
- 🔧 **渐进式武装** — 能用 requests 解决绝不上浏览器，能扣代码绝不上深度逆向，每一步都有退出条件

## 方法论：三阶渐进 + 两翼辅助

SpiderMind 的核心信条：**把重武器留给真正难啃的骨头。**

```
阶段 0: 结构化侦察 — 站点画像 + 反爬指纹 + 请求链路追踪
   ↓
阶段 1: 纯 Python 探路 — requests 直连，拿到数据直接交付
   ↓ (触发了反爬)
     ├─ 遇到验证码 → 🖼️ 验证码流水线（截图 → AI 预处理 → ddddocr）
     └─ 加密参数 → 阶段 2
   ↓
阶段 2: Playwright 补环境 — 定位加密点 → 扣 JS 代码 → Node.js 本地验证 → Python 调用
   ↓ (VMP / 重度混淆 / WASM)
阶段 3: jsreverser 深度逆向 — AST 分析 → 反混淆 → 逻辑还原
   ↓
阶段 4: 项目脚手架交付 — 完整工程结构
   ↓
阶段 5: 代码质量检查 — 环境重建、编码、异常、注释全审
   ↓
阶段 6: 开发文档输出 — DEV.md 完整记录
```

**两翼辅助**：验证码流水线（穿插在任意阶段）+ 结构化侦察（阶段 0 驱动全局决策）。

大部分采集任务在阶段 1 就结束了。不是所有目标都值得上 jsreverser。但每个项目都值得有一份 DEV.md。

## 🖼️ 验证码处理流水线

遇到验证码不直接放弃。SpiderMind 内置了三步自动化流水线：

```
触发验证码
    ↓
① Playwright 定位验证码元素 → 元素级截图（PNG 无损）
    ↓
② PIL 预处理增强
   · 放大 3x（Lanczos 算法）
   · 灰度化 → 锐化（UnsharpMask）
   · 对比度增强 2x → 二值化去噪
    ↓
③ ddddocr 智能识别
    ↓
   ┌───┴───┐
 成功      失败（重试 ≤3 次）
   ↓        ↓
继续采集   降级：调参重试 / AI 视觉 / 人工 / 跳过
```

**识别率参考**：

| 验证码类型 | 预处理后识别率 |
|-----------|-------------|
| 纯数字（4-6 位） | 90-98% |
| 数字+字母（4 位） | 80-95% |
| 中文验证码 | 60-80% |
| 滑块 / 点选 | Playwright 模拟 |

## 最终交付物

每完成一个采集目标，你得到的不是一个 `main.py`，而是一个完整的项目目录：

```
{project_name}/
├── main.py              # 主入口，命令行参数支持
├── config.yaml          # 配置分离（目标 URL、采集参数）
├── .env                 # 敏感信息（不入 Git）
├── requirements.txt     # Python 依赖清单
├── fetcher.py           # 请求调度（重试 + 超时 + UA 轮换 + 代理）
├── parser.py            # 数据解析（HTML / JSON）
├── encrypt.py           # 签名/加密参数生成
├── captcha_handler.py   # 验证码处理（截图 + 预处理 + OCR）
├── storage.py           # 存储层（去重 + JSON Lines / SQLite）
├── logger.py            # 日志系统（控制台 + 按天轮转）
├── node_helper/         # Node.js 补环境模块（按需生成）
├── storage/             # 采集数据输出
├── logs/                # 运行日志
├── .gitignore           # Git 忽略规则
└── DEV.md               # 开发文档：从 0 到 1 的完整推理过程
```

所有 Python 代码附带**详细中文注释**，解释每一步的意图和原理。

## 快速开始

在 Codex 中，给一个目标就够了：

```
帮我采集 https://target-website.com/search 的商品列表
```

SpiderMind 会自动完成全流程——包括遇到验证码时自动截图、预处理、识别。

你也可以用脚手架生成器手动初始化项目：

```bash
python scripts/scaffold_project.py my_project --with-node
cd my_project
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py
```

## 适用场景

| 场景 | 反爬强度 | 预计阶位 | 预计耗时 |
|------|---------|---------|---------|
| 静态 HTML / 无鉴权 API | 无 | 阶段 1 | ~20 min |
| 带 Token / Cookie 的 API | 低 | 阶段 1 | ~30 min |
| 简单数字验证码 | 低 | 阶段 1 + 验证码流水线 | ~35 min |
| JS Challenge（`__jsl_clearance` 等） | 中 | 阶段 2 | ~60 min |
| 自定义加密参数签名 | 中高 | 阶段 2 | ~90 min |
| obfuscator.io 混淆 / VMP / WASM | 高 | 阶段 3 | ~2 h |

## 项目结构

```
spider-mind/
├── SKILL.md                      # 入口：方法论 & 路由
├── agents/openai.yaml            # Agent 配置
├── references/                   # 各阶段详细手册（14 篇）
│   ├── recon.md                  # 🆕 结构化侦察分析（站点画像 + 反爬指纹 + 请求链路）
│   ├── workflow-overview.md      # 端到端执行地图
│   ├── strategy-triage.md        # 策略决策树（含验证码分流）
│   ├── stage-1-pure-py.md        # 纯 Python 探测
│   ├── stage-2-env-patch.md      # Playwright 调试 + 环境补丁
│   ├── stage-3-jsreverser.md     # 深度逆向工程
│   ├── captcha.md                # 🆕 验证码处理流水线（截图 → AI 预处理 → ddddocr）
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

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 核心运行时 |
| Node.js | 18+ | 补环境 JS 执行（阶段 2） |
| Playwright | 最新 | 浏览器调试 + 验证码截图 |
| ddddocr | 最新 | 验证码文字识别 |
| Pillow | 最新 | 验证码图像预处理增强 |
| jsreverser-mcp | — | 深度逆向（仅阶段 3 需要） |

安装命令：
```bash
pip install playwright ddddocr Pillow
playwright install chromium
```

## 许可

本项目仅供学习与研究使用。使用者应遵守目标网站的 robots.txt 及当地法律法规。