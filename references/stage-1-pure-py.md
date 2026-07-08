# Stage 1: 裸 Py 探路

使用此 playbook 进行第一阶分析：用最轻量的方式测试目标可访问性。

## 核心原则

在动用任何工具之前，先用最原始的 HTTP 请求搞清楚：目标到底有没有反爬，有多重。

## 工作方法

### 第一步：最小请求

```python
import requests

url = "目标URL"
resp = requests.get(url, timeout=10)
print(resp.status_code, resp.text[:500])
```

只带最基本的参数，不加任何 headers。观察：

- 状态码是什么（200/403/302/412/429）
- 响应体前 500 字符长什么样
- 有没有返回有用数据

### 第二步：逐步加装

如果第一步被拦，按顺序逐个添加：

1. **User-Agent**：模拟主流浏览器 UA
2. **Referer**：设置为目标站点首页
3. **Accept / Accept-Language / Accept-Encoding**：标准浏览器 headers
4. **Cookie**：从浏览器手动获取一份 Cookie 试试
5. **Origin / Host**：补充来源相关 headers

每一步只加一个变量，确认哪个 header 是关键因子。

### 第三步：session 保活

如果需要登录态：

```python
session = requests.Session()
# 先请求登录接口获取 cookie
login_resp = session.post(login_url, data={...})
# 再请求目标接口
data_resp = session.get(target_url)
```

### 第四步：数据解析

数据到手后确认格式：

- JSON → `resp.json()` 直接解析
- HTML → `BeautifulSoup` / `lxml` / `parsel` 提取
- XML → `lxml` 或 `xml.etree`
- 二进制 → 按格式处理（图片下载、PDF 等）

## 常见响应速查

| 状态码/表现 | 可能原因 | 尝试方案 |
|------------|---------|---------|
| 200 有数据 | 无防护 | 直接写采集逻辑 |
| 200 无数据/空 | 前端渲染 | 检查是否是 API，可能需要 Playwright |
| 200 加密数据 | 响应加密 | 找解密 JS 逻辑，可能进入三阶 |
| 302 跳转 | 重定向 | `allow_redirects=True` 跟进 |
| 403 | IP/UA 拦截 | 加 headers、代理 |
| 412 | 前置验证 | 可能需要 Cookie 或挑战验证 |
| 429 | 频率限制 | 加延时，降低并发 |
| 503/连接超时 | 被直接封 | 切换 IP，降低请求频率 |
| 验证码页面 | 需要识别 | 启动验证码流水线（captcha.md），非升级信号 |

## 退出条件

**成功退出（直接交付）：**
- 裸请求或加了基础 headers 后能稳定获取数据
- 数据格式清晰可解析
- 分页逻辑明确

**升级退出（进入三阶）：**
- headers/cookies 无效，参数是 JS 动态生成
- 响应体被 JS 加密，需要还原解码逻辑
- 出现 JS 挑战页面（如 __jsl_clearance 等）
- 出现字体反爬特征（页面能看到但抓下来是乱码）

**验证码分支（不升级，走 captcha.md）：**
- 触发验证码页面 → 启动 Playwright 截图 + PIL 预处理 + ddddocr 识别
- 验证码流水线重试 3 次仍失败 → 降级处理（人工介入/跳过当前任务）


## 验证清单

在阶段 1 完成前逐项确认：

- [ ] 裸 GET 请求已发送并记录状态码
- [ ] 裸 POST 请求已发送（如有需要）
- [ ] 逐个加 headers 测试，已确定哪个是关键 header
- [ ] Cookie 是否需要及如何获取已明确
- [ ] 响应格式已确认（JSON/HTML/XML/二进制）
- [ ] 响应内容不是空壳——确认包含目标数据
- [ ] 如果是 JSON，数据结构已记录
- [ ] 如果是 HTML，确认数据在 HTML 中而非 JS 渲染
- [ ] 分页方式已确定（页码/游标/滚动）
- [ ] 每次请求是否返回相同结构已确认
- [ ] 如触发验证码，已启动 captcha.md 流水线处理
- [ ] 升级到三阶之前，已记录阶段 2 的精确失败原因

## 常见陷阱

- 不要拿到 200 就以为成功了——响应可能是空壳或错误提示页
- 不要忽略响应 headers 中的 Set-Cookie
- 不要在一个 header 还没验证有效时就加了三个
- 不要用浏览器里复制的一长串 headers 一把梭——不知道哪个是关键的
- 不要忽略 HTTPS 证书问题（verify=False 可以临时跳过但要注意安全）
- 不要遇到验证码就直接升级——正确做法是先走 captcha.md 流水线
