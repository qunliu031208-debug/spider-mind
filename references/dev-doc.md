# Development Documentation

使用此文件规范最终交付的开发文档 `DEV.md` 的内容和格式。

## 文档目的

让接手项目的开发者：
- 不看代码就能理解整个逆向过程
- 知道每一步为什么这样做而不是那样做
- 能快速定位关键代码位置
- 遇到类似问题时能参考推理思路

## DEV.md 模板

```markdown
# {项目名称} - 开发文档

## 项目概述

- **目标站点**：{URL}
- **数据类型**：{商品/新闻/用户/...}
- **数据量级**：约 {N} 条
- **技术路线**：{纯 Python / Python + Node.js helper / Python + WASM}
- **开发日期**：{YYYY-MM-DD}
- **最后更新**：{YYYY-MM-DD}

---

## 一、环境要求

### 基础环境

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.8 | 采集器主语言 |
| Node.js | >= 16 | 仅加密 helper 需要（如有） |
| pip | >= 20 | |

### Python 依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| requests | 2.28+ | HTTP 请求 |
| python-dotenv | 1.0+ | 环境变量管理 |

### 快速启动

```bash
# 1. 克隆项目
cd {项目名}

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
copy .env.example .env
# 编辑 .env，填入 COOKIE 等必要信息

# 5. 运行
python main.py
```

---

## 二、逆向过程总览

### 整体时间线

```
{YYYY-MM-DD}  阶段 1：裸 Py 探路
              → 裸请求返回 403，加了 UA 和 Cookie 后返回 200
              → 发现响应数据是加密的，不能直接解析

{YYYY-MM-DD}  阶段 2：补环境扣代码
              → Playwright 定位到 sign 参数在 app.xxx.js 中生成
              → 扣下 encrypt 函数（约 80 行）
              → 补了 window、navigator、document 三个对象
              → 本地 Node.js 输出与浏览器一致

{YYYY-MM-DD}  阶段 4：项目落地
              → 生成项目脚手架
              → 编写采集逻辑
              → 测试通过

{YYYY-MM-DD}  阶段 5：质量检查
              → 独立环境重建测试通过
              → 编码和异常处理检查通过

{YYYY-MM-DD}  阶段 6：文档编写
              → 本文档完成
```

### 阶位决策记录

（按 escalation-ladder 格式记录）

```markdown
### 阶梯日志
**目标**: https://example.com/api/list
**进入阶位**: 阶段 2 - 补环境扣代码
**进入原因**: 裸请求返回 200 但响应体是加密乱码，解码逻辑在 JS 中
**最终交付形态**: Python + Node.js helper
```

---

## 三、关键技术细节

### 3.1 加密参数分析

**参数名**：`sign`
**位置**：请求 URL query string `?sign=xxxxx`
**生成方式**：MD5(timestamp + page + fixed_key)
**关键代码**：`helper/encrypt.js` 第 15-35 行

```javascript
// 加密核心逻辑（伪代码，示意）
function generateSign(timestamp, page) {
    const raw = timestamp + page + "固定密钥";
    return md5(raw);
}
```

**补环境要点**：
- 原代码依赖 `window.crypto` 生成随机数，已 mock 为 Node.js `crypto` 模块
- `navigator.userAgent` 被用于签名计算，必须与浏览器一致

### 3.2 请求结构分析

**目标 API**：`https://example.com/api/list`
**请求方式**：GET
**关键参数**：
| 参数 | 来源 | 说明 |
|------|------|------|
| page | 采集器传入 | 页码 |
| size | 固定值 | 每页条数 |
| t | `Date.now()` | 时间戳 |
| sign | helper 生成 | MD5 签名 |

### 3.3 验证码处理方案（如适用）

**验证码类型**：{数字/字母/中文/滑块/点选}
**识别方案**：Playwright 截图 + PIL 预处理增强 + ddddocr 识别
**预处理参数**：
| 参数 | 值 | 说明 |
|------|-----|------|
| scale | {3} | 放大倍数 |
| contrast | {2.0} | 对比度增强 |
| threshold | {128} | 二值化阈值 |

**识别率**：预估 {80-95}%（实际测试 {N} 次通过 {M} 次）

### 3.4 响应解析

**响应格式**：JSON
**数据结构**：
```json
{
    "code": 0,
    "data": {
        "list": [
            {"id": 1, "title": "商品名", "price": 99.00}
        ],
        "total": 500
    }
}
```

**解析要点**：
- `code=0` 表示成功，`code=-1` 表示签名错误
- 分页通过 `total` 和 `page*size` 对比判断是否到末页

---

## 四、遇到的重要难点

### 难点 1：sign 参数依赖 navigator.userAgent

**现象**：扣下来的 JS 在 Node.js 中生成的 sign 与浏览器不一致
**原因**：原代码 `navigator.userAgent` 被拼接到签名输入中
**解决**：在 `env.js` 中补了完整的 userAgent 字符串，与 Playwright 中看到的完全一致

### 难点 2：代码混淆导致定位困难

**现象**：`app.xxx.js` 是 10 万行的混淆文件，找不到加密函数入口
**原因**：代码经过了 obfuscator.io 混淆
**解决**：在 Playwright 中通过 XHR 断点（Network → Initiator）反向追踪到 `_encryptData` 函数

---

## 五、项目结构

```
{项目名}/
├── main.py              # 主入口：调度采集流程
├── config.py            # 配置文件
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── DEV.md               # 本文档
├── collector/
│   ├── __init__.py
│   ├── client.py        # HTTP 请求封装（含 sign 生成调用）
│   ├── parser.py        # 数据解析提取
│   └── pipeline.py      # 数据清洗和存储
├── helper/
│   ├── env.js           # 补环境代码（mock 浏览器对象）
│   ├── encrypt.js       # 扣下来的加密核心逻辑
│   ├── bridge.js        # Python 调用入口（stdin/stdout）
│   └── test.js          # helper 自测脚本
├── storage/data/        # 数据输出
└── logs/                # 日志文件
```

---

## 六、执行流程

```
启动 main.py
    │
    ├→ 读取 .env 配置
    ├→ 初始化日志和存储
    │
    ├→ for page in 1..MAX_PAGE:
    │       │
    │       ├→ generate_sign(page) ──调用──→ helper/bridge.js
    │       │       │
    │       │       └→ env.js 补环境
    │       │          encrypt.js 生成 sign
    │       │          返回 sign 值
    │       │
    │       ├→ GET /api/list?page=N&sign=xxx
    │       │
    │       ├→ 解析 JSON 响应
    │       ├→ 清洗字段
    │       ├→ 写入 storage/data.jsonl
    │       └→ 日志记录 + 延时
    │
    └→ 采集完成，输出统计信息
```

---

## 七、常见问题

### Q: 运行报错 `ModuleNotFoundError: No module named 'requests'`
A: 确保已激活虚拟环境并安装依赖：`pip install -r requirements.txt`

### Q: helper 报错 `window is not defined`
A: 检查 `helper/env.js` 是否正确补了 `global.window = global`

### Q: 所有请求返回签名错误
A: Cookie 可能过期了，重新从浏览器获取 Cookie 更新到 `.env`

### Q: 数据文件中文显示乱码
A: 确认 `pipeline.py` 中文件写入使用了 `encoding="utf-8"`
