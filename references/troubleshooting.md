# Troubleshooting

使用此文件处理环境问题和常见运行时故障。

## 环境检查

在开始任何工作前，先确认基础环境：

```bash
python --version     # 需要 >= 3.8
node --version       # 需要 >= 16
pip list | findstr requests    # 确认 requests 已安装
pip list | findstr playwright  # 确认 playwright 已安装
```

### Python 环境问题

**`pip install` 失败**

```bash
# 先升级 pip
python -m pip install --upgrade pip
# 或使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests
```

**虚拟环境创建失败**

```bash
python -m venv venv
# 如果报错，确保 Python 安装完整
# Windows 下有时需要管理员权限
```

**SSL 证书错误**

```python
# 临时方案（仅调试用）
requests.get(url, verify=False)
# 正确方案：安装证书
# pip install pip-system-certs
```

### Playwright 环境问题

**`playwright` 安装失败**

```bash
pip install playwright
playwright install chromium
# 如果下载浏览器慢，设置镜像
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
playwright install chromium
```

**Playwright 启动失败**

```python
# 常见原因 1：浏览器没装
# 解决：playwright install chromium

# 常见原因 2：缺少系统依赖
# 解决：playwright install-deps

# 常见原因 3：端口被占用
# 解决：换端口或关闭占用进程

# 常见原因 4：沙箱问题（Linux）
# 解决：browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
```

**Playwright 找不到浏览器**

```python
# 确认浏览器安装位置
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    print(p.chromium.executable_path)
```

### Node.js 环境问题

**Node.js 未安装**

```bash
# 从官网 https://nodejs.org 下载 LTS 版本
# 安装后重启终端
node --version
```

**`require()` 找不到模块（扣下来的 JS）**

```javascript
// 确认路径正确
// 如果 encrypt.js 在 helper/ 下
const { encrypt } = require("./helper/encrypt.js");

// 如果使用了 npm 包但未安装
// npm install crypto-js
// 但注意：npm 版本可能与页面版本不同！
```

**Node.js helper 报错 `window is not defined`**

这是补环境不完整的信号。在 `env.js` 中补充：
```javascript
if (typeof window === "undefined") {
    global.window = global;
}
```

### jsreverser-mcp 不可用

如果 jsreverser-mcp 在当前环境中不可用：

1. **降级处理**：回到二阶，尝试更精细的手动分析
2. **分块扣代码**：把混淆代码按函数分开，逐个击破
3. **动态调试**：在 Playwright 中用 `page.evaluate()` 直接在浏览器上下文执行代码片段
4. **明确告知用户**：jsreverser 不可用的具体原因和当前的降级方案

## 常见运行时故障

### 请求突然全部失败

排查顺序：
1. IP 是否被拉黑？→ 换代理或等一段时间
2. Cookie 是否过期？→ 重新获取 Cookie
3. 目标站是否改版？→ 检查响应内容是否变化
4. 加密参数是否有时效性？→ 检查时间戳类参数

### 只能获取第一页，后面的都失败

可能原因：
- 分页参数有签名，签名的输入包含了页码——确认签名逻辑
- 有 cursor/token 分页，token 在使用后失效——每次请求用新的 token
- 反爬升级了——降低频率，检查是否需要更新 headers

### 数据有时能拿到有时拿不到

说明不是参数问题，是风控：
- 降低请求频率（DELAY 从 1 秒提到 3 秒）
- 检查 IP 是否被间歇性封禁
- 添加随机延时（`time.sleep(random.uniform(1, 3))`）
- 检查是否有并发限制

### Python 调用 Node.js helper 无输出

```python
# 调试方法：先单独跑 Node.js
# node helper/test.js

# 检查 subprocess 是否正确
result = subprocess.run(
    ["node", "helper/bridge.js"],
    input=json.dumps(test_data),
    capture_output=True,
    text=True,
    timeout=10
)
print("stdout:", result.stdout)
print("stderr:", result.stderr)  # 错误信息在这里
print("returncode:", result.returncode)
```

### 补环境输出与浏览器不一致

排查清单：
1. 输入完全相同吗？——字符串编码、空格、换行
2. 时间戳一致吗？——浏览器和本地的时间可能不同
3. 环境变量一致吗？——`navigator.userAgent`、`navigator.platform`
4. 随机数可控吗？——代码中可能有 `Math.random()`
5. 加密库一样吗？——页面可能魔改了标准库

## 验证码处理故障

### ddddocr 识别率极低

**排查清单**：
1. 截图方式是否正确？——必须用 `element.screenshot()` 元素级截图，非整页截图
2. 预处理参数是否合适？——尝试调整 scale（3→5）、contrast（2.0→3.0）
3. 原始图片是否太小？——小于 100px 的验证码需增大 scale
4. 验证码是否有颜色干扰？——确保走了灰度化步骤
5. 验证码类型是否正确？——中文验证码需更大 scale（4-5x），滑块/点选需 det=True

### PIL 预处理后图片全黑或全白

- 全黑：降低二值化阈值（128→100 或更低）
- 全白：提高二值化阈值（128→180 或更高）
- 文字残缺：降低对比度增强倍数（2.0→1.5）

### ddddocr 导入失败

```bash
pip install ddddocr
# 如果安装失败，检查是否缺少 Visual C++ 运行时
# ddddocr 依赖 onnxruntime，可能需要 VC++ 2019+
```

### 验证码刷新后页面状态丢失

- 某些网站的验证码与 session 绑定，刷新验证码可能导致页面跳转
- 解决：刷新验证码后检查页面 URL 是否变化，如变化需重新导航

## 求助边界

以下情况不要自己硬撑，尽早告知用户：

- jsreverser-mcp 不可用且手动分析也无进展
- 目标使用了硬件级保护（如手机端的 SafetyNet）
- 目标需要真实设备指纹才能通过（非软件可模拟）
- 目标的反爬在 30 分钟内无法通过至少一个请求
- Cookie 的获取需要真实的手机扫码/短信验证
