# App 签名还原专项（unidbg 离线模拟）

> 目标：把 App 请求签名算法完整还原，输出**不依赖真机/Frida/抓包代理**的离线签名器。
> 本页基于实际还原过 转转（zzreqsign）、链家（WLL-KGSA）、小红书（libxyass shield）等项目沉淀。
> 能力边界：核心流程（抓包 → 定位 → unidbg 跑通 → 验证）已熟练掌握；so 深层汇编、加固对抗依赖 MCP/Skills 自动化 + AI 辅助分析。

## 还原路径总览

```
① 确定目标签名头 + 抓取输入输出对（≥3 组）
        ↓
② 判断签名层：Java / native / 混合
        ↓
③ native → 提取 so → 构建 unidbg 调用环境
        ↓
④ unidbg 离线模拟 → 输入 URL+headers → 输出签名
        ↓
⑤ 字节级验证：与真机输出完全一致（100%）
        ↓
⑥ 输出离线签名器（Python / Java 双入口）
```

## 一、unidbg 是什么 / 为什么用它

- **unidbg**：在 JVM 里直接模拟执行 Android 的 so（native 库），不需要真机/模拟器
- 优势：可调试、可打日志、可单步，**输入可控输出可对比**
- 适用：签名在 so 里、且 so 未用高强度虚拟化保护（VMP）时，这是最快还原路径

```xml
<!-- 依赖（unidbg 0.9.x + capstone + unicorn 等） -->
<dependency>
  <groupId>com.github.zhkl0228</groupId>
  <artifactId>unidbg-android</artifactId>
  <version>0.9.9</version>
</dependency>
```

## 二、unidbg 调用骨架（Java）

```java
// 核心思路：加载 so → 初始化 JNI → 调 native 方法 → 拿签名
public class AppSign {
    private final AndroidEmulator emulator;
    private final VM vm;

    public AppSign() {
        emulator = AndroidEmulatorBuilder.for32Bit().build();
        Memory memory = emulator.getMemory();
        memory.setLibraryResolver(new AndroidResolver(23));
        vm = emulator.createDalvikVM();
        vm.setJni(new MyJniCallbacks()); // 按需补 JNI 环境
        DalvikModule dm = vm.loadLibrary("libsignLib", true);
        dm.callJNI_OnLoad(emulator);
    }

    public String sign(String params) {
        // 调 native 导出函数，返回签名
        DvmObject<?> ret = vm.callStaticJniMethodObject(
            emulator, "com/app/SignUtils", "sign", params);
        return ret.getValue().toString();
    }
}
```

## 三、还原过程中的关键决策点

| 场景 | 处理方式 |
|------|----------|
| so 依赖系统库/自定义 JNI | 用 unidbg hook 掉，返回固定值 |
| 时间戳参与签名 | 传可控时间 → 与真机同时间对拍 |
| 加密套件多（AES/CFB/CBC） | 用 Frida 抓真实输入输出对 → 反推算法 |
| so 加固/壳 | 先脱壳（frida-dexdump），再提 so |

## 四、字节级验证（最重要一步）

```bash
# 对拍验证：真机输出 vs unidbg 输出
# 要求：同一输入，输出逐字节一致
python verify_pair.py \
  --truth  真机签名样本.json \
  --engine 离线签名器输出.json
```

**验证标准（硬性）：**
- [ ] 同一输入，真机 vs 离线引擎输出**完全一致**
- [ ] ≥ 3 组不同输入全部通过
- [ ] 同一输入多次运行输出稳定（无随机性泄漏）

## 五、输出离线签名器

```python
# Python 侧调用（unidbg 作为子进程 / 或纯 Python 重写算法）
def gen_sign(url, headers):
    # 方式 A：调 unidbg（Java）
    out = subprocess.run(["java", "-cp", CP, "com.app.SignMain", url, headers],
                         capture_output=True, text=True)
    return parse(out.stdout)
    # 方式 B：纯 Python 重写算法（更优，零依赖）
    #   return pure_python_sign(url, headers)
```

## 六、能力边界与免责

- **熟练**：unidbg 跑通、JNI 环境补齐、对拍验证、离线签名器落地
- **依赖工具**：复杂 so 汇编逆向、加固对抗、多 so 协作链分析 → MCP/Skills 自动化 + AI 辅助
- **不承诺**：所有 App 都能 100% 字节级还原（加固 + 虚拟化保护的另说）

## 实战案例参考（已完成的还原）

| 目标 | 签名头 | 还原深度 | 结果 |
|------|--------|----------|------|
| 转转 | zzreqsign | 全算法还原（MD5+XOR） | 3/3 样本通过，2648 请求 0 失败 |
| 链家 | WLL-KGSA | HMAC-SHA256 还原 | Python 复算与真机一致 |
| 小红书 | shield / xy-platform-info | unidbg 字节级还原 | 100/100 字节一致 |
