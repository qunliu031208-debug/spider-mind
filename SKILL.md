---
name: spider-mind
description: 三阶渐进式爬虫逆向框架。从接收目标 URL 开始，先结构化侦察定级，再裸 Python 探路，受阻后用 Playwright 配合补环境扣代码，最后以 jsreverser 深度逆向兜底，交付从零到一的完整爬虫项目脚手架。内置验证码处理流水线（Playwright 截图 + AI 预处理增强 + ddddocr 识别）。适用场景：用户提供目标页面 URL、API 地址、JS 片段、加密参数样本，或要求搭建完整爬虫采集项目。
---

# SpiderMind

## Role

从一个 URL 开始，交付一个可维护的爬虫项目。

这个 skill 不是"帮你写个 requests 脚本"，也不只是"帮你过掉某个加密参数"。
它是从零到一的爬虫项目交付框架，覆盖目标分析、逆向决策、脚本实现、质量检查、文档输出的完整链路。

核心信念：**能简单就不要上工具，渐进式武装，每一步都有退出条件。**

## Non-Negotiables

- 拿到目标后，第一件事是结构化侦察定级（见 `references/recon.md`），再裸 Python 直连探路，不跳过直接上浏览器。
- Playwright 只用于调试观察、定位加密点和截图识别验证码，不是最终交付方案。
- 补环境扣代码路线中，扣下来的 JS 必须在本地 Node.js 独立运行验证通过后才接入 Python。
- jsreverser 是最后手段，仅当前两阶无法解决时才启用。
- 遇到验证码：Playwright 截图 → AI 预处理增强（锐化+放大+对比度） → ddddocr 识别，不要直接放弃或跳过。
- 最终交付必须是纯 Python 脚本（含可选的本地 Node.js helper），不依赖浏览器运行。
- 所有 Python 关键代码必须有详细的中文注释，解释每一步的意图和原理。
- 至少验证两条数据可重复获取后才算交付完成。
- 交付前必须通过代码质量检查（独立环境重建、编码检查、异常处理审查）。
- 交付物包含：完整项目脚手架 + 质量检查通过的代码 + 开发文档 DEV.md。
- 交付物包含完整项目脚手架：目录结构、虚拟环境、日志、配置、存储层。

## 六阶段流程

```
阶段 0：结构化侦察
  确认站点架构（SSR/SPA）、反爬指纹（JS Challenge/加密参数/验证码/WASM）
  追踪请求链路依赖（Cookie → Header → Token 的传递链）
  输出侦察报告 → 驱动阶位决策
  （详见 references/recon.md）

阶段 1：裸 Py 探路
  Python requests 直连目标
  → 拿到数据 → 跳到阶段 4 交付
  → 403/加密/签名 → 进入阶段 2
  → 触发验证码 → 启动验证码流水线（Playwright 截图 + AI 预处理 + ddddocr）

阶段 2：补环境扣代码
  ① Playwright 打开页面，Network 面板定位加密参数来源
  ② 把加密 JS 代码扣下来
  ③ 本地 Node.js 补环境运行，输出参数
  ④ Python 调用 Node.js helper，完成采集（代码带详细中文注释）
  → 扣不出来/VMP/重度混淆 → 进入阶段 3
  → 触发验证码 → 验证码流水线

阶段 3：jsreverser 深度逆向
  启动 jsreverser-mcp 对 VMP/混淆/WASM 做深度分析
  还原为纯 Python 或最小 JS helper
  → 进入阶段 4 交付

阶段 4：项目脚手架交付
  完整目录结构、venv、日志、配置、存储层
  至少两条数据验证通过

阶段 5：代码质量检查
  独立环境重建测试、编码检查、异常处理审查、注释完整性检查
  → 质量不过关 → 回阶段 4 修正

阶段 6：开发文档
  输出 DEV.md：环境要求、逆向推理过程、关键代码、难点总结、执行流程图
  → 项目才算真正落地
```

每一阶段都有明确的进入条件和退出条件，不越级，不原地打转。
升级和降级的详细规则见 `references/escalation-ladder.md`。

## Startup Gate

对每个新目标，在动手前先做完三件事：

1. **结构化侦察**（详见 `references/recon.md`）
   - 站点架构识别：SSR 还是 SPA？数据从哪来？
   - 反爬指纹：IP 封禁 / JS Challenge / 加密参数 / 验证码 / WASM / 字体反爬
   - 请求链路追踪：Cookie → Header → Token 的完整依赖链
   - 输出侦察报告，驱动后续阶位决策

2. **阶位决策**（详见 `references/strategy-triage.md`）
   - 先发一个裸 Python GET/POST 看响应
   - 根据侦察报告 + 裸请求结果决定进入第几阶
   - 声明本轮预计的最终交付形态：纯 Python / Python + Node.js helper / 需要 jsreverser 介入

3. **项目骨架**
   - 确定项目名称和目录
   - 创建虚拟环境和依赖文件
   - 初始化日志和配置文件
   - 所有后续产出都落在这个项目目录里

规则：
- 启动门没走完，说明目标还没理解透
- 中途分类变了，重新过一遍启动门

## What This Skill Optimizes For

- 渐进式决策，避免过度工程
- 补环境扣代码的经典路线作为主力
- 完整项目交付而非一次性脚本
- 每一步都有可验证的退出条件
- 交付物附带开发文档，可交接可维护
- 方法论的通用性和可转移性
- 验证码处理自动化（AI 预处理 + ddddocr），减少人工介入

## Knowledge Modules

入口文件保持精简，按场景路由到专项 reference：

侦察与决策：
- `references/recon.md` 结构化侦察分析（站点画像 + 反爬指纹 + 请求链路）
- `references/workflow-overview.md` 端到端执行地图
- `references/strategy-triage.md` 拿到目标后选哪一阶的决策树
- `references/escalation-ladder.md` 升级阶梯，防止跳级

三阶 playbook：
- `references/stage-1-pure-py.md` 裸 Py 探路 playbook
- `references/stage-2-env-patch.md` 补环境扣代码 playbook（含中文注释要求）
- `references/stage-3-jsreverser.md` jsreverser 深度逆向 playbook

专项能力：
- `references/captcha.md` 验证码处理流水线（Playwright 截图 + AI 预处理 + ddddocr）
- `references/tool-playbook.md` 工具选用与切换指南
- `references/troubleshooting.md` 故障排查与环境诊断

工程交付与运维：
- `references/project-scaffold.md` 项目脚手架规范和模板
- `references/code-quality.md` 代码质量检查清单
- `references/dev-doc.md` 开发文档规范与模板
- `references/report-templates.md` 阶段报告与交付报告模板

## Reference Router

侦察与决策：
- `references/recon.md` 第一个要看的：怎么系统分析目标
- `references/workflow-overview.md` 完整流程地图（从侦察到交付）
- `references/strategy-triage.md` 侦察结果 → 阶位选择
- `references/escalation-ladder.md` 升级阶梯与决策记录

三阶 playbook：
- `references/stage-1-pure-py.md` 裸 Python 探路
- `references/stage-2-env-patch.md` 补环境扣代码（含中文注释要求）
- `references/stage-3-jsreverser.md` jsreverser 深度逆向

专项能力：
- `references/captcha.md` 验证码处理（截图 → AI 增强 → OCR）
- `references/tool-playbook.md` 工具选用与切换
- `references/troubleshooting.md` 故障排查与环境诊断

工程交付与运维：
- `references/project-scaffold.md` 项目脚手架
- `references/code-quality.md` 代码质量检查清单
- `references/dev-doc.md` 开发文档规范与模板
- `references/report-templates.md` 阶段报告与交付报告模板

## Anti-Patterns

- 不要跳过结构化侦察直接上浏览器。
- 不要跳过裸 Py 探路直接上浏览器。
- 不要在 Playwright 能看清楚加密点时就用 jsreverser。
- 不要把扣下来的 JS 直接认为 OK，必须本地 Node.js 验证通过。
- 不要把 Playwright 脚本当作最终交付。
- 不要把环境写死在 helper 里——补环境代码要独立、可迁移。
- 不要只测一条数据就交付。
- 不要交付没有日志和配置的"裸脚本"。
- 不要混淆数据清洗和参数生成逻辑，各自独立。
- 不要在加密参数还没稳定复现时就急于写分页逻辑。
- 不要跳过项目脚手架直接给一个 main.py。
- 不要跳过代码质量检查直接交付——别人跑不起来就是你的问题。
- 不要交付没有开发文档的项目——两周后你自己也看不懂。
- 不要遇到验证码就放弃——先用 Playwright 截图 + AI 预处理增强 + ddddocr 尝试，重试 3 次后再降级。

## Bottom Line

这个 skill 要养成的习惯：

1. 拿到目标 → 结构化侦察 → 先发请求看结果 → 再决定用多重的武器
2. 遇到验证码 → 截图 → AI 预处理增强 → ddddocr → 重试 → 再降级
3. 代码写好 → 加上中文注释 → 质量检查 → 写开发文档

大部分爬虫任务在第一阶或第二阶就能搞定。
不是所有目标都值得上 jsreverser。
但每个项目都值得有 DEV.md。