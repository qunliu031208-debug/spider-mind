# Stage 2: 补环境扣代码

使用此 playbook 进行第二阶分析：Playwright 定位加密参数来源，扣下 JS 代码，本地 Node.js 补环境运行。

## 核心原则

不要试图理解整段混淆代码。定位到加密参数的"出生点"，扣最小的那一段，本地跑通就够。

## 工作方法

### 第一步：Playwright 网络观察

启动 Playwright 并监听网络请求：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 先非无头模式观察
    page = browser.new_page()

    # 监听所有网络请求
    page.on("request", lambda req: print(f"-> {req.method} {req.url}"))
    page.on("response", lambda resp: print(f"<- {resp.status} {resp.url}"))

    page.goto("目标URL")
    page.wait_for_timeout(5000)  # 等 JS 执行完

    browser.close()
```

也可以在 Playwright 中使用 `page.route()` 拦截特定请求，查看 headers 和 body。

### 第二步：定位加密参数的来源

在 Playwright 中打开 DevTools（或使用 `page.pause()`）：

1. **Network 面板**：找到目标 API 请求，查看 Request Headers 和 Payload
2. **识别动态参数**：哪些字段看起来是签名/加密/时间戳？
3. **Initiator 列**：点进去看是哪个 JS 文件发起的
4. **Search**：在 Sources 中全局搜索参数名（如 `sign`、`token`、`encrypt`）
5. **断点调试**：在可疑函数处打断点，刷新页面，观察调用栈

```python
# Playwright 打印请求详情
page.on("request", lambda req: print(
    f"{req.method} {req.url}\n"
    f"Headers: {dict(req.headers)}\n"
    f"PostData: {req.post_data}"
))
```

### 第三步：扣下加密 JS 代码

定位到加密函数后：

1. 在 Sources 中找到完整函数体
2. 复制到本地 `encrypt.js` 文件
3. 如果函数依赖其他模块/变量，一并扣下来
4. 识别依赖的外部对象（`window`、`document`、`navigator` 等）

典型需要扣的内容：
- 加密入口函数（如 `function encrypt(data) {...}`）
- 依赖的工具函数（MD5、SHA、AES 实现等）
- 常量数组、密钥字符串
- 签名参数的时间戳生成逻辑

### 第四步：本地 Node.js 补环境

创建 `env.js` 补全缺失的浏览器环境：

```javascript
// 常见的补环境代码
const crypto = require("crypto");

// 补 window 对象
if (typeof window === "undefined") {
    global.window = global;
}

// 补 navigator
if (!global.navigator) {
    global.navigator = {
        userAgent: "Mozilla/5.0 ...",
        appVersion: "5.0 ...",
        platform: "Win32",
        language: "zh-CN",
    };
}

// 补 document
if (!global.document) {
    global.document = {
        cookie: "",
        createElement: () => ({}),
        getElementsByTagName: () => [],
    };
}

// 补 atob / btoa
if (typeof atob === "undefined") {
    global.atob = (str) => Buffer.from(str, "base64").toString("binary");
    global.btoa = (str) => Buffer.from(str, "binary").toString("base64");
}
```

创建 `test.js` 测试扣下来的代码：

```javascript
// test.js
require("./env.js");          // 补环境
const { encrypt } = require("./encrypt.js");  // 扣下来的代码

// 固定输入测试
const input = "test_data_123";
const output = encrypt(input);
console.log("Output:", output);
```

```bash
node test.js
```

### 第五步：验证输出一致性

用固定输入比对浏览器和本地 Node.js 的输出：

```python
import subprocess
import json

def js_encrypt(data):
    """调用 Node.js helper 生成加密参数"""
    result = subprocess.run(
        ["node", "helper/encrypt.js", json.dumps(data)],
        capture_output=True,
        text=True,
        cwd="项目目录"
    )
    return result.stdout.strip()

# 测试
test_input = {"page": 1, "size": 20}
output = js_encrypt(test_input)
print(output)
```

关键验证：
- 同一输入多次运行，输出是否一致
- 与浏览器中相同输入下的输出是否一致
- 时间戳类参数是否随调用更新

### 第六步：接入 Python 采集器

```python
import requests
import subprocess
import json

def get_encrypted_params(data):
    result = subprocess.run(
        ["node", "helper/encrypt.js", json.dumps(data)],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def fetch_data(page=1):
    params = get_encrypted_params({"page": page})
    resp = requests.get(API_URL, params=params, headers=HEADERS)
    return resp.json()
```


### 注释要求

所有 Python 关键代码段必须添加详细的中文注释：

- 每个函数需要 docstring：用途、参数说明、返回值说明
- 加密流程的每一步需要注释解释"为什么这样做"
- 补环境代码（`env.js`）需要注释每个 mock 的用途
- 关键常量需要注释来源（从哪里扣的，代表什么含义）

示例：
```python
def generate_sign(page: int, timestamp: int) -> str:
    """生成请求签名

    签名算法：MD5(timestamp + page + 固定密钥)
    固定密钥 "abc123" 从 app.xxx.js 第 152 行的 _KEY 变量扣取

    Args:
        page: 页码
        timestamp: 毫秒时间戳

    Returns:
        32 位小写 MD5 签名
    """
    # 拼接签名原文：时间戳 + 页码 + 固定密钥
    raw = f"{timestamp}{page}abc123"
    # 通过 Node.js helper 计算 MD5
    result = subprocess.run(
        ["node", "helper/sign.js"],
        input=raw,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout.strip()
```

## 补环境常见坑

| 坑 | 表现 | 解法 |
|----|------|------|
| window 对象缺失 | `ReferenceError: window is not defined` | `global.window = global` |
| document 引用 | `document.createElement` 报错 | 补空函数返回 `{}` |
| CryptoJS/MD5 | 标准实现与页面输出不一致 | 页面可能魔改了，扣页面版本 |
| navigator 探测 | 运行结果与浏览器不同 | 补完整 navigator 属性 |
| eval/Function | 动态执行代码 | new Function 或 vm2 沙箱 |
| 定时器依赖 | setTimeout/setInterval | 补立即执行的 mock |
| DOM 操作依赖 | 依赖 HTML 元素属性 | 找到实际取值逻辑，mock 返回值 |
| XHR/fetch 链 | 加密依赖异步请求 | 把异步请求结果也扣下来 mock |
| 原型链检测 | 检测环境是否真实浏览器 | 补原型链方法 |
| canvas 指纹 | 需要 canvas 计算结果 | 扣 canvas 计算逻辑，或用 node-canvas |

## 退出条件

**成功退出（进入交付）：**
- 固定输入下 Node.js 输出与浏览器一致
- 同一输入多次输出稳定
- 采集脚本能成功获取数据

**升级退出（进入三阶）：**
- 代码 VMP 虚拟化，看不懂控制流
- 严重混淆 + 多层扁平化，无法定位加密入口
- WASM 签名，JS 只做胶水调用
- 代码动态生成（eval chain），每次请求代码都变
- 补环境后输出有差异但无法定位缺失了什么


## 验证清单

在阶段 2 完成前逐项确认：

- [ ] Playwright 已成功启动并导航到目标页
- [ ] Network 面板中已找到目标 API 请求
- [ ] 加密参数已定位：具体是哪个字段（sign/token/encrypt/...）
- [ ] 加密代码位置已定位：具体 JS 文件名和函数名
- [ ] 加密函数完整扣下，无遗漏的依赖
- [ ] env.js 补环境代码已完成
- [ ] `node test.js` 无报错
- [ ] 固定输入 A 下，Node.js 输出与浏览器输出一致
- [ ] 固定输入 B（不同数据）下，输出也一致
- [ ] 同一输入运行两次，输出一致（排除随机数干扰）
- [ ] Python subprocess 能成功调用 Node.js helper
- [ ] 使用 helper 生成的参数发送请求，成功获取数据
- [ ] 两条不同的数据（如第 1 页和第 2 页）都能成功获取
- [ ] 升级到三阶之前，已记录阶段 2 的精确失败原因和证据

## 常见陷阱

- 不要一次扣太多代码。先扣入口函数，缺什么补什么。
- 不要在补环境的第一行就用 `jsdom`——太重了，能手工 mock 就手工 mock。
- 不要把 Playwright 脚本当交付物。
- 不要跳过固定输入验证，直接用在真实请求上
- 调试过程中如遇验证码，启动 captcha.md 流水线（Playwright 截图 + PIL 预处理 + ddddocr），不要因为验证码而放弃当前阶——可能会被风控。
- 不要把补环境代码和加密逻辑混在一个文件里——分开便于维护。
- 不要在 Node.js helper 里硬编码 URL 或业务参数——helper 只负责参数生成。
