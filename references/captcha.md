# 验证码处理方案

## 概述

SpiderMind 的验证码处理采用 **截图 → AI 预处理增强 → ddddocr 识别** 的三步流水线。
目标是让简单验证码自动通过，复杂验证码自动预处理后尝试通过，极端情况才介入人工。

## 总体流程

```
采集流程中触发验证码
        ↓
Playwright 定位验证码图片元素
        ↓
截图保存验证码图片（PNG，无损）
        ↓
AI 图像预处理（锐化 + 放大 + 对比度增强 + 去噪）
        ↓
ddddocr 识别
        ↓
   ┌────┴────┐
   ↓         ↓
识别成功    识别失败
   ↓         ↓
填入结果    重试 3 次仍失败 → 降级处理
继续采集    （更换策略/人工介入/记录跳过）
```

## 第一步：Playwright 截图定位

```python
# 验证码截图脚本 — 使用 Playwright 精确定位验证码元素
from playwright.sync_api import sync_playwright

def capture_captcha(page, captcha_selector="img.captcha"):
    """
    定位验证码元素并截图保存
    
    Args:
        page: Playwright page 对象
        captcha_selector: 验证码图片的 CSS 选择器（需根据目标网站调整）
    
    Returns:
        截图文件路径
    """
    # 定位验证码图片元素
    captcha_element = page.locator(captcha_selector).first
    
    # 等待元素可见
    captcha_element.wait_for(state="visible", timeout=5000)
    
    # 截图（仅截取该元素区域，而非整个页面）
    captcha_path = "captcha_raw.png"
    captcha_element.screenshot(path=captcha_path)
    
    print(f"[captcha] 验证码截图已保存: {captcha_path}")
    return captcha_path
```

## 第二步：AI 图像预处理

```python
# AI 图像预处理 — 增强验证码可读性
# 通过锐化、放大、对比度增强等操作，大幅提升 ddddocr 识别率

from PIL import Image, ImageEnhance, ImageFilter

def preprocess_captcha(input_path, output_path="captcha_enhanced.png", scale=3):
    """
    对验证码图片进行 AI 辅助预处理
    
    处理流程：
    1. 放大图片（3 倍，增加像素密度）
    2. 转为灰度图（去除颜色干扰）
    3. 锐化（增强边缘和笔画）
    4. 增强对比度（让文字更突出）
    5. 二值化（转为纯黑白，去除背景噪点）
    
    Args:
        input_path: 原始截图路径
        output_path: 增强后输出路径
        scale: 放大倍数（默认 3 倍）
    
    Returns:
        预处理后的图片路径
    """
    # 打开原始截图
    img = Image.open(input_path)
    
    # 第一步：放大图片（Lanczos 算法，高质量放大）
    # 放大可以增加像素信息，帮助 OCR 识别细微笔画
    w, h = img.size
    img = img.resize((w * scale, h * scale), Image.LANCZOS)
    
    # 第二步：转为灰度图
    # 彩色验证码的颜色干扰是常见的混淆手段
    img = img.convert("L")
    
    # 第三步：锐化处理
    # 使用 UnsharpMask 增强边缘，让模糊的字符笔画变得清晰
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    # 第四步：增强对比度
    # 让文字与背景的区分更加明显
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)  # 对比度增强 2 倍
    
    # 第五步：二值化
    # 将灰度图转为纯黑白，彻底去除背景噪点
    # 阈值 128：灰度 > 128 为白，< 128 为黑
    img = img.point(lambda x: 255 if x > 128 else 0, "1")
    
    # 保存增强后的图片
    img.save(output_path)
    print(f"[captcha] 预处理完成: {output_path}")
    
    return output_path
```

**预处理参数说明**：

| 参数 | 默认值 | 作用 | 调优建议 |
|------|--------|------|----------|
| `scale` | 3 | 放大倍数 | 图片原始太小（<100px）可调到 4-5 |
| `radius` | 2 | 锐化半径 | 字符边缘模糊可增大到 3 |
| `percent` | 150 | 锐化强度 | 谨慎调节，过大产生噪点 |
| `contrast` | 2.0 | 对比度倍数 | 背景杂乱可增大到 2.5-3.0 |
| `threshold` | 128 | 二值化阈值 | 文字颜色浅可降低到 100 |

## 第三步：ddddocr 识别

```python
# ddddocr 识别 — 调用 MCP 服务进行 OCR
import ddddocr

def recognize_captcha(image_path):
    """
    使用 ddddocr 识别验证码
    
    Args:
        image_path: 预处理后的验证码图片路径
    
    Returns:
        识别结果字符串，如果置信度低则返回 None
    """
    # 初始化 ddddocr（带 OCR 检测器）
    ocr = ddddocr.DdddOcr(det=False, ocr=True, show_ad=False)
    
    # 读取图片并识别
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    
    result = ocr.classification(img_bytes)
    
    if result:
        print(f"[captcha] 识别结果: {result}")
    else:
        print(f"[captcha] 识别失败，返回空结果")
    
    return result if result else None
```

## 完整流水线

```python
# 验证码处理主流程 — 三步走完
def solve_captcha(page, captcha_selector="img.captcha", max_retries=3):
    """
    完整的验证码识别流水线
    
    Args:
        page: Playwright page 对象
        captcha_selector: 验证码元素选择器
        max_retries: 最大重试次数
    
    Returns:
        识别成功返回验证码字符串，失败返回 None
    """
    for attempt in range(1, max_retries + 1):
        print(f"[captcha] 第 {attempt}/{max_retries} 次尝试...")
        
        # 第一步：截图
        raw_path = f"captcha_raw_{attempt}.png"
        captcha_element = page.locator(captcha_selector).first
        captcha_element.screenshot(path=raw_path)
        
        # 第二步：预处理增强
        enhanced_path = f"captcha_enhanced_{attempt}.png"
        preprocess_captcha(raw_path, enhanced_path)
        
        # 第三步：识别
        result = recognize_captcha(enhanced_path)
        
        if result and len(result) >= 4:  # 验证码通常 ≥4 字符
            # 填入验证码并提交
            input_selector = "input.captcha-input"
            page.locator(input_selector).fill(result)
            page.locator("button.submit").click()
            
            # 等待响应，检查是否通过
            page.wait_for_timeout(2000)
            if not page.locator(captcha_selector).is_visible():
                print(f"[captcha] ✅ 验证码通过!")
                return result
            else:
                print(f"[captcha] ❌ 验证码错误，刷新重试...")
                # 点击刷新验证码
                page.locator("img.captcha-refresh").click()
                page.wait_for_timeout(1000)
        else:
            print(f"[captcha] 识别结果异常，刷新重试...")
            page.locator("img.captcha-refresh").click()
            page.wait_for_timeout(1000)
    
    print(f"[captcha] 已重试 {max_retries} 次，全部失败")
    return None
```

## 降级策略

如果 ddddocr + 预处理 连续 3 次失败，按以下优先级尝试：

| 优先级 | 方案 | 适用场景 |
|--------|------|----------|
| 1 | 调整预处理参数（增大 scale、提高对比度） | 字符模糊但形状完整 |
| 2 | 更换验证码类型识别（ddddocr 支持滑块、点选等） | 非传统文本验证码 |
| 3 | 将预处理后的图片传给 AI 视觉模型识别 | ddddocr 无法识别的扭曲字符 |
| 4 | 保存截图和增强结果，请求人工介入 | 识别率极低且采集价值高 |
| 5 | 跳过当前任务，记录日志，继续下一项 | 非关键数据 |

## 常见验证码类型处理

| 验证码类型 | 识别方法 | 预处理要点 |
|-----------|----------|------------|
| 数字+字母（4 位） | ddddocr | 放大 3x + 二值化 |
| 纯数字（4-6 位） | ddddocr | 二值化即可，识别率最高 |
| 中文验证码 | ddddocr | 需要更大放大倍数（4-5x） |
| 滑块验证 | Playwright 模拟拖拽 | 不需要 OCR，计算滑块距离 |
| 点选验证 | ddddocr 目标检测 | 需要 `det=True` 模式 |
| 极验/顶象等商业验证 | 不直接处理 | 分析是否有绕过方案，否则降级 |

## 注意事项

- 验证码截图务必用元素级别截图（`element.screenshot()`），而非整页截图后裁剪
- 原始截图保存为 PNG 格式，避免 JPEG 压缩引入额外噪点
- 预处理后的图片也保留下来，方便后续分析识别失败原因
- 不要用 Python requests 下载验证码图片——URL 中的 Cookie 与登录态绑定
- 如果目标使用极验等商业验证码，不要死磕，优先找 API 绕过方案