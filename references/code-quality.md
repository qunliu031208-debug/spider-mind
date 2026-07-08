# Code Quality

使用此 playbook 在项目交付前做最终质量检查。不是跑一遍就过了，而是从"换一台电脑也能跑"的标准来审视。

## 核心原则

交付物不是你本地能跑就行——是别人拿到也能跑。质量检查就是模拟"别人拿到"的状态。

## 检查步骤

### 第一步：独立环境重建测试

不用当前开发目录，从零重建：

```bash
# 在一个全新的目录中
cd C:\temp
python -m venv test_env
test_env\Scripts\activate
pip install -r D:\项目路径\requirements.txt
python D:\项目路径\main.py
```

观察：
- `pip install` 有没有漏掉的依赖？
- `python main.py` 能不能直接跑起来？
- 有没有 import 报错？
- 有没有文件路径硬编码问题？

### 第二步：编码问题检查

逐一检查以下编码隐患：

**Python 文件编码声明**
```python
# 每个 .py 文件头部确认有（Python 3 默认 UTF-8，但有声明更安全）
# -*- coding: utf-8 -*-
```

**文件读写编码**
```python
# 所有 open() 调用必须显式指定 encoding
with open("file.json", "r", encoding="utf-8") as f:  # ✓
with open("file.json", "r") as f:                     # ✗ 可能 GBK 误读
```

**日志文件编码**
```python
# 日志 handler 必须指定编码
logging.FileHandler("logs/app.log", encoding="utf-8")
```

**subprocess 调用编码**
```python
# Node.js helper 调用指定 encoding
subprocess.run(["node", "helper/bridge.js"],
               input=data,
               capture_output=True,
               text=True,
               encoding="utf-8")  # 显式指定
```

**中文注释编码**
- 所有中文注释在 IDE 中正常显示（不出现乱码）
- 所有 print/logging 中的中文正常输出（不出现 UnicodeEncodeError）

### 第三步：异常处理完整性检查

```python
# 网络请求必须有异常处理
try:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
except requests.Timeout:
    logger.error(f"请求超时: {url}")
except requests.HTTPError as e:
    logger.error(f"HTTP 错误: {e}")
except requests.RequestException as e:
    logger.error(f"请求异常: {e}")
```

检查清单：
- [ ] 所有 HTTP 请求都有 timeout 设置
- [ ] 所有 HTTP 请求都有异常捕获
- [ ] 分页终止条件明确（空数据、错误码、超出页码）
- [ ] 网络中断后可以重试
- [ ] Node.js helper 调用有超时和错误处理
- [ ] 数据存储写入失败不会导致程序崩溃

### 第四步：硬编码和安全检查

```bash
# 搜索硬编码的敏感信息
# 以下内容不应出现在代码中，应该在 .env 或 config.py 中
```

检查清单：
- [ ] Cookie 不在代码中硬编码 → 在 `.env.example` 中
- [ ] API Key/Token 不在代码中 → 在环境变量中
- [ ] 文件路径不使用绝对路径 → 使用相对路径或 os.path
- [ ] 代理地址如果变化 → 在配置文件中

### 第五步：运行完整性测试

```bash
# 至少跑通两页数据
python main.py
```

检查：
- [ ] 程序正常启动，无 import 错误
- [ ] 第一页数据成功获取并存储
- [ ] 第二页数据成功获取（分页逻辑正确）
- [ ] 日志文件正常写入，中文无乱码
- [ ] 数据文件正常写入，中文无乱码
- [ ] 程序正常退出，无残留进程

### 第六步：注释完整性检查

代码注释标准：

```python
# -*- coding: utf-8 -*-
"""
项目名称：XXX 采集器
功能：从 XXX 获取商品列表数据
作者：-
日期：2026-07-08
"""

def fetch_page(page: int) -> dict:
    """获取指定页码的数据

    Args:
        page: 页码，从 1 开始

    Returns:
        API 返回的原始 JSON 数据

    加密逻辑说明：
    1. 使用 helper/bridge.js 生成 sign 参数
    2. sign 输入为 时间戳 + page + 固定密钥
    3. 输出为 32 位 MD5 签名
    """
    ...
```

检查清单：
- [ ] 每个 `.py` 文件头部有文件说明注释
- [ ] 每个函数有 docstring 说明用途、参数、返回值
- [ ] 加密/签名逻辑有详细的中文注释解释原理
- [ ] captcha_handler.py（如有）独立可运行，ddddocr + Pillow 正常导入
- [ ] ddddocr 识别测试通过（提供一张测试图片验证 OCR 功能）
- [ ] 补环境代码（`env.js`）有注释说明每个 mock 的用途
- [ ] 关键常量和配置有注释说明含义

## 质量红线

- 以下情况 **禁止交付**：
  - `python main.py` 报错跑不起来
  - `pip install -r requirements.txt` 有依赖遗漏
  - 日志或数据文件出现中文乱码
  - Cookie/Token 硬编码在代码中
  - 没有任何异常处理
  - 核心代码没有中文注释
  - captcha_handler.py 中的 ddddocr 或 Pillow 无法导入

- 以下情况 **可以交付但需说明**：
  - Node.js helper 需要 Node 16+（在 requirements 中注明）
  - 需要配置代理（在 README 中注明）
  - Cookie 有时效性（在 README 中注明有效期和获取方式）
- captcha_handler.py 需要额外安装 ddddocr 和 Pillow（在 requirements.txt 中已包含）
