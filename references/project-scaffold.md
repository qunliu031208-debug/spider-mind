# Project Scaffold

使用此文件规范最终交付的爬虫项目结构。

## 核心原则

交付的不是一个脚本，是一个项目。任何人都能拿到目录后 `pip install -r requirements.txt && python main.py` 跑起来。

## 标准目录结构

```
{project_name}/
├── main.py                 # 主入口：调度采集流程
├── config.py               # 配置文件
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板（cookie、key 等敏感信息）
├── collector/
│   ├── __init__.py
│   ├── client.py           # HTTP 请求封装（session、headers、重试）
│   ├── parser.py           # 数据解析提取
│   └── pipeline.py         # 数据清洗和存储
├── helper/                 # Node.js helper（如果有的话）
│   ├── env.js              # 补环境代码
│   ├── encrypt.js          # 加密核心逻辑
│   └── test.js             # helper 自测脚本
├── storage/                # 数据输出目录
│   └── data/               # JSON/CSV 文件
├── logs/                   # 日志目录
│   └── app.log
└── README.md               # 项目说明：目标、使用方法、注意事项
```

## 各文件职责

### main.py

```python
"""项目主入口"""
import logging
from config import Config
from collector.client import APIClient
from collector.parser import DataParser
from collector.pipeline import DataPipeline

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    client = APIClient(Config())
    parser = DataParser()
    pipeline = DataPipeline()

    for page in range(1, Config.MAX_PAGE + 1):
        raw = client.fetch_page(page)
        items = parser.parse(raw)
        pipeline.save(items)
        logging.info(f"Page {page}: {len(items)} items")

if __name__ == "__main__":
    main()
```

### config.py

```python
"""项目配置"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_URL = "https://target.com"
    API_URL = f"{BASE_URL}/api/list"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 ...",
        "Referer": BASE_URL,
    }
    COOKIE = os.getenv("COOKIE", "")
    MAX_PAGE = 50
    DELAY = 1.0  # 请求间隔（秒）
    TIMEOUT = 30
    RETRY = 3
```

### collector/client.py

```python
"""HTTP 请求封装"""
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class APIClient:
    def __init__(self, config):
        self.config = config
        self.session = self._build_session()

    def _build_session(self):
        session = requests.Session()
        retry = Retry(total=self.config.RETRY, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.config.HEADERS)
        if self.config.COOKIE:
            session.cookies.update(
                dict(item.split("=", 1) for item in self.config.COOKIE.split("; "))
            )
        return session

    def fetch_page(self, page):
        """获取一页数据"""
        params = self._build_params(page)
        resp = self.session.get(self.config.API_URL, params=params, timeout=self.config.TIMEOUT)
        resp.raise_for_status()
        time.sleep(self.config.DELAY)
        return resp.json()

    def _build_params(self, page):
        """构造请求参数（如有加密参数，在此调用 helper）"""
        raise NotImplementedError
```

### collector/parser.py

```python
"""数据解析和提取"""
class DataParser:
    def parse(self, raw_data):
        """从原始响应中提取结构化数据"""
        items = []
        for item in raw_data.get("data", []):
            items.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "date": item.get("publish_date"),
            })
        return items
```

### collector/pipeline.py

```python
"""数据清洗和存储"""
import json
import csv
import os

class DataPipeline:
    def __init__(self, output_dir="storage/data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save(self, items):
        # JSON 存储
        with open(f"{self.output_dir}/data.json", "a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
```

### helper/ 目录（如有 Node.js helper）

```
helper/
├── env.js        # 补环境：mock 浏览器对象
├── encrypt.js    # 扣下来的加密代码
├── test.js       # 自测：固定输入验证
└── bridge.js     # Python 调用入口：接收 stdin JSON，输出 stdout JSON
```

bridge.js 模板：

```javascript
// bridge.js - Python 通过 subprocess 调用的入口
require("./env.js");
const { encrypt } = require("./encrypt.js");

// 从 stdin 读取 JSON 参数
let input = "";
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
    const data = JSON.parse(input);
    const result = encrypt(data);
    process.stdout.write(JSON.stringify(result));
});
```

### requirements.txt

```
requests>=2.28
python-dotenv>=1.0
# 按需添加：
# beautifulsoup4>=4.12
# lxml>=4.9
# parsel>=1.8
# httpx>=0.24
```


## 代码注释规范

所有交付的 Python 文件必须包含中文注释：

- **文件头**：`# -*- coding: utf-8 -*-` + 模块说明 docstring
- **函数**：每个函数有 docstring（用途、参数、返回值、加密流程说明）
- **关键逻辑**：加密/签名/请求构造的每一步有注释解释"为什么"
- **常量**：扣取来源标注（从哪个 JS 文件的第几行扣的）
- **补环境**：`env.js` 中每个 mock 注明用途

注释示例见 `stage-2-env-patch.md` 的"注释要求"章节。


## 代码注释规范

所有交付的 Python 文件必须包含中文注释：

- **文件头**：`# -*- coding: utf-8 -*-` + 模块说明 docstring
- **函数**：每个函数有 docstring（用途、参数、返回值、加密流程说明）
- **关键逻辑**：加密/签名/请求构造的每一步有注释解释"为什么"
- **常量**：扣取来源标注（从哪个 JS 文件的第几行扣的）
- **补环境**：`env.js` 中每个 mock 注明用途

注释示例见 `stage-2-env-patch.md` 的"注释要求"章节。

## 验证清单

项目交付前必须确认：

- [ ] `pip install -r requirements.txt` 无报错
- [ ] `python main.py` 可运行并输出数据
- [ ] 日志正常写入 `logs/` 目录
- [ ] 数据正常写入 `storage/` 目录
- [ ] 至少两条数据验证通过（不同的 page/参数）
- [ ] Node.js helper（如有）独立自测通过：`node helper/test.js`
- [ ] Cookie 等敏感信息在 `.env` 中，不在代码里
- [ ] README 写了目标站点、使用方法、注意事项
- [ ] 没有硬编码的绝对路径

## 常见陷阱

- 不要把所有逻辑塞进一个 main.py——拆成 client/parser/pipeline
- 不要把 Cookie 硬编码在 config.py 里——用 .env
- 不要忘了写 README——两周后你自己也看不懂了
- 不要在 storage 里提交数据到 Git——加 .gitignore
- 不要把虚拟环境 venv/ 提交到 Git
- 不要在日志里打印敏感信息（Cookie、Token）
