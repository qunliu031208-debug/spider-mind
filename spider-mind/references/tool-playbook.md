# Tool Playbook

使用此文件进行工具选用与切换决策。

## 工具清单及选用原则

### Python requests

**用途**：裸 HTTP 请求探路、轻量级数据采集。

**何时选用**：
- 目标无反爬或仅有基础 headers 验证
- 不需要保持复杂 session 状态
- 单线程顺序采集

**何时切换**：
- 需要异步并发 → httpx
- 需要浏览器环境 → Playwright（仅调试）

### Python httpx

**用途**：高性能异步 HTTP 采集。

**何时选用**：
- 数据量大，需要并发提速
- 目标支持 HTTP/2
- 需要异步 session 管理

**最低使用门槛**：requests 版本先跑通，再改写成 httpx。

```python
import asyncio
import httpx

async def fetch_all():
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"{URL}?page={p}") for p in range(1, 50)]
        return await asyncio.gather(*tasks)
```

### Playwright

**用途**：浏览器调试观察、网络请求拦截分析。

**何时选用**：
- 需要看浏览器里真实发出的请求长什么样
- 需要在 Sources 面板定位加密代码的位置
- 需要观察 JS 执行顺序和参数生成时机

**何时不用**：
- 请求已经通过 Python 成功获取数据
- 只是想"自动点按钮"——那是交付方案，不是调试工具

**Playwright 调试最佳实践**：
- 非无头模式启动（`headless=False`），方便观察
- 始终监听 `page.on("request")` 和 `page.on("response")`
- 使用 `page.pause()` 打开 Playwright Inspector
- 调试完后关闭浏览器，代码不依赖 Playwright 运行

### Node.js

**用途**：本地运行扣下来的 JS 加密代码。

**环境要求**：
- Node.js >= 16
- 不需要 npm 包（补环境代码纯手写，不用 jsdom 等重库）

**与 Python 的通信方式**：
- subprocess + stdin/stdout（推荐，最简单）
- 临时文件（参数多时）
- HTTP 本地服务（仅当 helper 需要持久运行时）

### jsreverser-mcp

**用途**：深度逆向混淆/VMP/WASM。

**何时选用**：
- 代码 VMP 虚拟化保护
- 重度混淆，连入口函数都找不到
- WASM 签名，核心逻辑不在 JS 中

**何时不用**：
- Playwright 中能直接找到清晰的加密函数
- 代码只是简单的 obfuscator.io 混淆（手动也能看懂）

## 工具切换决策表

| 当前状态 | 下一步工具 | 切换条件 |
|---------|-----------|---------|
| requests 被 403 | requests + headers | 添加 UA/Referer 后重试 |
| requests + headers 仍 403 | Playwright | 需要看浏览器里真实请求 |
| Playwright 看到请求结构 | requests + Node.js | 扣下加密代码后可本地生成 |
| 加密代码扣不下来 | jsreverser | 代码 VMP/重度混淆 |
| requests 单线程太慢 | httpx | 已有稳定采集逻辑，只需提速 |

## 环境检查

在启动任何工具前，先确认环境可用：

```bash
python --version          # >= 3.8
node --version            # >= 16
npx playwright --version  # 确认 Playwright 可用
```

如果没有 Playwright：
```bash
pip install playwright
playwright install chromium
```

如果 jsreverser-mcp 不可用：
- 明确告知用户，降级使用手动分析
- 不假装 jsreverser 在运行

## 常见陷阱

- 不要同时开多个 Playwright 实例调试同一个目标
- 不要在 Playwright 中直接调用 requests——它们之间没有 cookie 共享
- 不要在 Node.js helper 中引入 npm 包（如 crypto-js）除非确认输出与浏览器一致
- 不要在 jsreverser 还在运行时就去改扣出来的代码
- 不要跳过环境检查直接开始写代码
