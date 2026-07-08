#!/usr/bin/env python3
"""scaffold_project.py - 一键生成爬虫项目脚手架"""

import argparse
import os
import sys
from pathlib import Path

TEMPLATE_MAIN = '''"""{project_name} - 主入口"""

import logging
from config import Config
from collector.client import APIClient
from collector.parser import DataParser
from collector.pipeline import DataPipeline


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    logger = setup_logging()
    logger.info("Starting {project_name}")

    config = Config()
    client = APIClient(config)
    parser = DataParser()
    pipeline = DataPipeline()

    for page in range(1, config.MAX_PAGE + 1):
        try:
            raw = client.fetch_page(page)
            items = parser.parse(raw)
            pipeline.save(items)
            logger.info(f"Page {{page}}: {{len(items)}} items")
        except Exception as e:
            logger.error(f"Page {{page}} failed: {{e}}")

    logger.info("{project_name} finished")


if __name__ == "__main__":
    main()
'''

TEMPLATE_CONFIG = '''"""{project_name} - 配置文件"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_URL = "{base_url}"
    API_URL = f"{{BASE_URL}}/api/list"
    HEADERS = {{
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": BASE_URL,
    }}
    COOKIE = os.getenv("COOKIE", "")
    MAX_PAGE = 50
    DELAY = 1.0
    TIMEOUT = 30
    RETRY = 3
'''

TEMPLATE_CLIENT = '''"""{project_name} - HTTP 请求客户端"""

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
        retry = Retry(
            total=self.config.RETRY,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.config.HEADERS)
        if self.config.COOKIE:
            for item in self.config.COOKIE.split("; "):
                if "=" in item:
                    k, v = item.split("=", 1)
                    session.cookies.set(k, v)
        return session

    def fetch_page(self, page):
        params = self._build_params(page)
        resp = self.session.get(
            self.config.API_URL,
            params=params,
            timeout=self.config.TIMEOUT
        )
        resp.raise_for_status()
        time.sleep(self.config.DELAY)
        return resp.json()

    def _build_params(self, page):
        # TODO: 根据目标构造请求参数
        # 如有加密参数，在此调用 helper
        return {{"page": page, "size": 20}}
'''

TEMPLATE_PARSER = '''"""{project_name} - 数据解析器"""


class DataParser:
    def parse(self, raw_data):
        """从原始响应中提取结构化数据

        Args:
            raw_data: API 返回的原始 dict

        Returns:
            结构化数据列表
        """
        items = []
        # TODO: 根据实际响应结构提取字段
        for item in raw_data.get("data", raw_data.get("list", [])):
            items.append({{
                "id": item.get("id"),
                "title": item.get("title", ""),
                "date": item.get("publish_date", item.get("date", "")),
                # 按需添加更多字段
            }})
        return items
'''

TEMPLATE_PIPELINE = '''"""{project_name} - 数据存储管道"""

import json
import os
from datetime import datetime


class DataPipeline:
    def __init__(self, output_dir="storage/data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.filename = f"{{output_dir}}/data.jsonl"

    def save(self, items):
        """保存数据为 JSONL 格式"""
        with open(self.filename, "a", encoding="utf-8") as f:
            for item in items:
                item["_collected_at"] = datetime.now().isoformat()
                f.write(json.dumps(item, ensure_ascii=False) + "\\n")
'''

TEMPLATE_CAPTCHA_HANDLER = '''"""{project_name} - 验证码处理模块"""

from PIL import Image, ImageEnhance, ImageFilter
import ddddocr


class CaptchaHandler:
    """验证码自动识别流水线
    三步走：Playwright 元素级截图 → PIL 预处理增强 → ddddocr 识别
    """

    def preprocess(self, image_path, output_path=None, scale=3):
        """AI 辅助图像预处理增强
        处理流程：放大(Lanczos 3x) → 灰度 → 锐化 → 对比度增强(2x) → 二值化
        """
        if output_path is None:
            base = image_path.rsplit(".", 1)[0]
            output_path = f"{{base}}_enhanced.png"
        img = Image.open(image_path)
        w, h = img.size
        img = img.resize((w * scale, h * scale), Image.LANCZOS)
        img = img.convert("L")
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.point(lambda x: 255 if x > 128 else 0, "1")
        img.save(output_path)
        return output_path

    def recognize(self, image_path):
        """使用 ddddocr 识别验证码"""
        ocr = ddddocr.DdddOcr(det=False, ocr=True, show_ad=False)
        with open(image_path, "rb") as f:
            result = ocr.classification(f.read())
        return result if result else ""

    def solve(self, page, captcha_selector="img.captcha",
              input_selector="input.captcha-input",
              submit_selector="button.submit", max_retries=3):
        """完整验证码处理流水线"""
        for attempt in range(1, max_retries + 1):
            raw_path = f"captcha_raw_{{attempt}}.png"
            page.locator(captcha_selector).first.screenshot(path=raw_path)
            enhanced_path = self.preprocess(raw_path)
            result = self.recognize(enhanced_path)
            if result and len(result) >= 4:
                page.locator(input_selector).fill(result)
                page.locator(submit_selector).click()
                page.wait_for_timeout(2000)
                if not page.locator(captcha_selector).is_visible():
                    return result
            page.locator("img.captcha-refresh").click()
            page.wait_for_timeout(1000)
        return None
'''

TEMPLATE_DOTENV = """# {project_name} 环境变量
# 复制此文件为 .env 并填入真实值

COOKIE=
"""

TEMPLATE_REQUIREMENTS = """requests>=2.28
python-dotenv>=1.0
ddddocr>=1.0
Pillow>=10.0
"""

TEMPLATE_GITIGNORE = """venv/
.venv/
env/
.env
__pycache__/
*.pyc
storage/data/
logs/
"""


def create_init(path):
    (path / "__init__.py").write_text('"""collector"""\n', encoding="utf-8")


def scaffold(project_dir, base_url="https://example.com"):
    project_name = project_dir.name
    print(f"Creating project: {project_name}")
    print(f"Location: {project_dir}")

    dirs = [
        project_dir / "collector",
        project_dir / "helper",
        project_dir / "storage" / "data",
        project_dir / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {d.relative_to(project_dir)}")

    files = {
        project_dir / "main.py": TEMPLATE_MAIN.format(project_name=project_name),
        project_dir / "config.py": TEMPLATE_CONFIG.format(
            project_name=project_name, base_url=base_url
        ),
        project_dir / "collector" / "__init__.py": '"""collector"""\n',
        project_dir / "collector" / "client.py": TEMPLATE_CLIENT.format(project_name=project_name),
        project_dir / "collector" / "parser.py": TEMPLATE_PARSER,
        project_dir / "collector" / "pipeline.py": TEMPLATE_PIPELINE,
        project_dir / "collector" / "captcha_handler.py": TEMPLATE_CAPTCHA_HANDLER.format(project_name=project_name),
        project_dir / ".env.example": TEMPLATE_DOTENV.format(project_name=project_name),
        project_dir / "requirements.txt": TEMPLATE_REQUIREMENTS,
        project_dir / ".gitignore": TEMPLATE_GITIGNORE,
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        print(f"  [OK] {path.relative_to(project_dir)}")

    print(f"\nDone! Next steps:")
    print(f"  cd {project_dir}")
    print(f"  python -m venv venv")
    print(f"  venv\\Scripts\\pip install -r requirements.txt")
    print(f"  copy .env.example .env")
    print(f"  python main.py")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new scraping project")
    parser.add_argument("name", help="Project name (lowercase, hyphens allowed)")
    parser.add_argument(
        "--path", default=".",
        help="Parent directory for the project [default: current directory]"
    )
    parser.add_argument(
        "--base-url",
        default="https://example.com",
        help="Target website base URL"
    )
    args = parser.parse_args()

    project_dir = Path(args.path).resolve() / args.name
    if project_dir.exists():
        print(f"Error: {project_dir} already exists", file=sys.stderr)
        sys.exit(1)

    scaffold(project_dir, args.base_url)


if __name__ == "__main__":
    main()
