# Android 逆向侦察与基础流程

> 本页是安卓逆向的**入门到基础** playbook，覆盖从拿到 APK 到定位签名函数的完整链路。
> 定位原则：**流程熟练、工具依赖 MCP/Skills 驱动，复杂算法还原依赖 AI 辅助 + 反复验证。**

## 能力边界声明

- ✅ 熟练：抓包定位签名头、Frida hook、jadx 反编译、so 定位、unidbg 跑通、字节级对拍验证
- ⚠️ 依赖工具：deep 级 so 汇编分析、VMP/加固对抗、JSVMP 深度还原 → 由 MCP/Skills 自动化 + AI 辅助完成，人工负责流程判断与结果验证
- ❌ 不做假承诺：不宣称能 100% 还原所有加固/虚拟化保护

## 逆向总流程（五步）

```
① 抓包定位签名头（在哪、长什么样、哪些参数参与）
        ↓
② 判断签名在 Java 层还是 native 层（hook 常见加密 API 试探）
        ↓
③ 反编译定位签名代码（jadx + 字符串搜索）
        ↓
④ native 定位（so 提取 + IDA/反汇编 + Frida 动态验证）
        ↓
⑤ 算法还原（unidbg 离线模拟 / 手工复现）→ 字节级验证
```

## 第一步：抓包定位签名头

```bash
# 环境准备：手机 + 电脑同一代理，安装抓包证书
# 常见工具：Charles / Fiddler / mitmproxy
# 目标：找到每个请求都带的可疑头（如 X-Sign / sign / WLL-KGSA / shield）
```

**观察要点：**
- 哪个 header 随请求变化？哪些参数参与签名？
- 签名是否带 timestamp/nonce（防重放）？
- 换参数后签名是否变化 → 确认签名依赖参数内容

## 第二步：确认签名位置（Java vs native）

```python
# Frida hook 常见加密 API，看是否有调用
# 若 hook 不到任何 Java 加密调用 → 签名大概率在 native (so)
import frida, sys

def on_message(message, data):
    print(message)

# 挂载到目标 App
session = frida.get_usb_device().attach("目标包名")
script = session.create_script("""
    // hook javax.crypto.Mac / MessageDigest
    ['javax.crypto.Mac', 'java.security.MessageDigest'].forEach(cls => {
        try {
            Java.perform(() => {
                const C = Java.use(cls);
                const methods = C.class.getDeclaredMethods();
                console.log('[hook] ' + cls + ' methods: ' + methods.length);
            });
        } catch(e) {}
    });
""")
script.on('message', on_message)
script.load()
```

**判定规则：**
- hook 到 `Mac/MsgDigest` 调用 → Java 层签名，直接看调用栈
- hook 不到 → native 层，进第四步

## 第三步：反编译定位（jadx）

```bash
# 1. 从设备拉取 APK（或用模拟器直接拿）
adb shell pm path 目标包名
adb pull /data/app/.../base.apk

# 2. jadx 反编译
jadx -d decompiled base.apk

# 3. 搜索签名头特征字符串（如 "LJAPPVA" / "shield" / 签名 key 名）
grep -r "LJAPPVA" decompiled/    # Windows 用 Grep 工具搜
```

**要点：** 签名头里的常量字符串（accessKeyId、固定前缀）是最快的定位锚点。

## 第四步：native 定位

```bash
# 1. 从 APK 提取 so（lib 目录下）
# 2. 用反汇编工具查看导出函数（IDA / Ghidra / objdump）
# 3. Frida hook so 导出函数，确认签名入口
```

```python
# Frida hook native 函数
script = session.create_script("""
    var lib = Module.findBaseAddress("libsign.so");
    var func = Module.findExportByName("libsign.so", "sign");
    if (func) {
        Interceptor.attach(func, {
            onEnter: function(args) { console.log('[native] sign called'); },
            onLeave: function(retval) { console.log('[native] ret: ' + retval); }
        });
    }
""")
```

## 第五步：算法还原与验证

- **优先 unidbg 离线模拟**：把 so 跑在 JVM 上，不依赖真机，输入相同 → 输出与真机一致
- **验证标准**：至少 3 组"真机抓包输入输出对"，unidbg/复现结果与真机**逐字节一致**才算还原成功
- 详细还原路径见 `android-sign-reverse.md`

## 常见坑

- **证书校验（SSL Pinning）**：抓不到包时先绕过（frida ssl-unpinning 脚本 / 重打包）
- **加固/脱壳**：先脱壳再反编译（frida-dexdump 等），否则 jadx 看不到业务代码
- **模拟器检测**：部分 App 检测模拟器环境，优先用真机
- **多 so 分层**：签名可能跨多个 so 协作（如 xEF4 + xyass），逐层还原

## 交付标准

- [ ] 抓包样本 ≥ 3 组（不同参数输入）
- [ ] 确认签名层（Java / native / 混合）
- [ ] 定位到签名函数
- [ ] 还原结果与真机字节级一致（或明确说明还原到哪一步）
- [ ] 输出离线签名器（Python / Java 入口）
