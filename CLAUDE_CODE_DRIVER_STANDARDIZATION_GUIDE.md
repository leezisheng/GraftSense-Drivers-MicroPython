# Claude Code 驱动标准化执行指南

> 适用于 `GraftSense-Drivers-MicroPython#`
> 
> 这份文档只做仓库级执行指引，不重复完整规范。完整规则以 `upy_driver_dev_spec_summary.md` 和对应 skill 为准。

## 1. 先分类，再决定走哪条链路

### 标准硬件驱动
满足下面任一特征，就按标准驱动处理：
- 依赖 `I2C` / `SPI` / `UART` / `Pin` 等硬件接口
- 有明确可复用的公开 API
- 目标是长期复用，而不是一次性的板级初始化

标准链路：
`upy-norm-driver` -> `upy-norm-main` 或 `upy-gen-main` -> `upy-gen-readme` -> `upy-gen-pkg` -> `upy-pack-driver` -> `upy-deploy-test`

### 中间件 / 板级启动片段
满足下面任一特征，就不要直接当硬件驱动包处理：
- 导入了 `network` / `urequests` / `AsyncWebsocketClient` / `asyncio`
- 代码只做连接、初始化、启动、粘合，不提供稳定的芯片级 API
- 目标是“能跑起来”，不是“可复用的芯片驱动”

这类内容应走 middleware 分支，不要强行塞进 `communication/`、`sensors/` 这类标准驱动树里。

## 2. LAN8720 的结论

`communication/lan8720_driver/lan8720.py` 目前只有这些动作：
- `import network`
- `network.LAN(...)`
- `lan.active(True)`
- `lan.ifconfig()`

它没有类封装，没有可复用 API，没有寄存器级访问，更像 ESP32 的以太网板级初始化脚本，而不是一个独立的通信芯片驱动。

### 建议
- 默认**不需要**把它当作标准 `communication/lan8720_driver/` 驱动包
- 如果要保留，只建议作为 board bootstrap / middleware 示例保存
- 不建议把它送进 `upy-pack-driver` 作为常规硬件驱动打包

### 实操判断
如果 Claude Code 读到的文件只是在做 `network.LAN(...)` 这种初始化，就直接标记为“middleware / board init”，不要继续按硬件驱动标准化。

## 3. 命名和目录规则

### 目录
- 统一按 `<domain>/<chip>_driver/` 放
- domain 只负责仓库内的功能分组，不要被上游仓库名牵着走

### 文件
- 主驱动入口统一用小写蛇形命名：`<chip>.py`
- 如果上游是 `device.py`、`ST7735.py`、`max1704x.py` 这类名字，标准化时要改成芯片名对应的入口模块
- 运行时依赖的辅助文件要保留在同目录，或者保留为真实子包
- 不要为了“看起来单文件”把真正运行时依赖删掉

### 例子
- `device.py` -> `atecc608a.py`
- `max1704x.py` -> `max17048.py`
- `ST7735.py` -> `st7735.py`

## 4. 标准化顺序

### 4.1 先看源码属于哪类
- 硬件驱动
- middleware
- board init / glue code

### 4.2 再选 skill
- 规范化驱动文件：`upy-norm-driver`
- 已有 `main.py` 需要整理：`upy-norm-main`
- 没有可用 `main.py`，从零生成：`upy-gen-main`
- 生成 `README.md`: `upy-gen-readme`
- 生成 `package.json`: `upy-gen-pkg`
- 最后整理成标准包目录：`upy-pack-driver`
- 上设备验证：`upy-deploy-test`

### 4.3 什么时候不能跳步
- `main.py`、`README.md`、`package.json` 没稳定之前，不要先 pack
- 依赖文件没保住之前，不要删辅助模块
- 还没确认是不是 middleware 之前，不要直接套硬件驱动模板

## 5. 多文件驱动怎么处理

很多上游库不是单文件，这种情况不要硬压成单文件，原则是：
- 主入口模块负责对外 API
- 辅助模块只保留运行时依赖
- 只要运行时会 import 到，就必须跟着一起进入最终包
- 只有测试残片、示例残片、重复代码，才可以考虑剥离

### 本仓库里应视为多文件的情况
- `BMI270`: `bmi270.py` + `i2c_helpers.py` + `config_file.py`
- `LSM6DSOX`: `lsm6dsox.py` + `i2c_helpers.py`
- `HTS221`: `hts221.py` + `i2c_helpers.py`
- `SX1262`: `sx1262.py` + `sx126x.py` + `_sx126x.py`
- `ATECC608A`: `atecc608a.py` + `basic.py` + `constant.py` + `exceptions.py` + `host.py` + `packet.py` + `status.py` + `util.py`

### 单文件优先的情况
- `ST7735`
- `MPU6886`
- `MP34DT05`
- `SX1276`
- `IP5306`
- `MAX17048`

## 6. 当前仓库的建议判定表

| 芯片 | 建议路径 | 形态 | 备注 |
|---|---|---|---|
| ST7735 | `lighting/st7735_driver/` | 单文件 | 可按标准驱动链路处理 |
| BMI270 | `sensors/bmi270_driver/` | 多文件 | `config_file.py` 必须保留 |
| LSM6DSOX | `sensors/lsm6dsox_driver/` | 多文件 | `i2c_helpers.py` 必须保留 |
| MPU6886 | `sensors/mpu6886_driver/` | 单文件 | 适合直接标准化 |
| HTS221 | `sensors/hts221_driver/` | 多文件 | `i2c_helpers.py` 必须保留 |
| MP34DT05 | `sensors/mp34dt05_driver/` | 单文件 | 适合直接标准化 |
| SX1262 | `communication/sx1262_driver/` | 多文件 | 三个文件都要保留 |
| SX1276 | `communication/sx1276_driver/` | 单文件 | 适合直接标准化 |
| LAN8720 | `communication/lan8720_driver/` | 非标准驱动 | 默认不进常规驱动包 |
| ATECC608A | `misc/atecc608a_driver/` | 多文件 | 不能只留单文件壳 |
| IP5306 | `misc/ip5306_driver/` | 单文件 | 适合直接标准化 |
| MAX17048 | `sensors/max17048_driver/` | 单文件 | 源文件名要统一到芯片名 |

## 7. package.json 和 README 的边界

### package.json
- `urls` 要覆盖最终需要随包发布的 `.py` 文件
- 运行时依赖的辅助模块不能丢
- 如果某个文件只是示例或临时调试文件，不要放进 `urls`

### README.md
- 标准硬件驱动写硬件需求、接线、引脚表、快速开始
- middleware / board init 写运行环境、连接参数、占位凭证，不要硬套 I2C 接线表

## 8. 已发现的规范化错误与硬性检查项

下面是本轮整理新增驱动时实际发现过的问题。Claude Code 后续规范化驱动时，要把这些作为固定检查项，不要只依赖 `code_checker.py`。

### 8.1 MicroPython / CPython 兼容边界

- 不要在 `main.py` 示例里为了退出流程随手写 `sys.exit(1)`。设备端示例优先用 `raise SystemExit`、`break`、`return` 或自然结束脚本；如果确实使用 `sys.exit()`，必须先确认目标 MicroPython 端口支持并显式 `import sys`。
- 不要把 CPython 模块名和 MicroPython 历史模块名写死。优先使用当前通用模块名，再做兼容 fallback，例如 `hashlib` -> `uhashlib`，`random` -> `urandom`。
- 不要裸用 `const()`。驱动文件中只要出现 `const()`，必须显式导入 `from micropython import const`，需要 CPython 静态检查或烟测时要提供安全 fallback。
- 不要把 CPython 运行环境检查通过等同于 MicroPython 可用。最终至少要做 AST 解析、`flake8 --select=E9,F63,F7,F82`、`pylint --errors-only` 和 MicroPython 分支导入烟测。

### 8.2 `main.py` 示例常见错误

- 不要在变量可能未赋值前 `del device`、`del sensor`、`del display`。需要静态占位时用 `device = None` 这类初始化。
- 全局计时变量必须先有模块级默认值，例如 `last_print_time = 0`，再在运行时赋值为 `time.ticks_ms()`。
- 示例文件可以保留硬件循环，但驱动库文件不能在 import 时初始化硬件、扫描总线、启动死循环或打印测试日志。
- 示例依赖的模块必须来自当前 `code/` 目录、MicroPython 内置模块或 `package.json.urls` 明确发布的文件。不要让示例引用被裁掉的上游测试文件。

### 8.3 多文件驱动不能被压坏

- 不能为了“单文件化”删除真实运行时依赖。`BMI270` 的 `config_file.py`、`SX1262` 的 `_sx126x.py`、`ATECC608A` 的协议辅助文件都属于必须保留项。
- `package.json.urls` 必须覆盖运行时需要发布的 `.py` 文件；示例 `main.py` 通常不要放进 `urls`，除非明确希望安装时也作为库文件下发。
- 多文件驱动内部 import 要和 `urls` 安装名一致。重命名主入口后，要同步检查所有 `import xxx` / `from xxx import ...`。

### 8.4 动态写法和静态检查

- 不要用超长 `__getattr__ if/elif` 链生成常量。优先用 `_CONSTANTS` 字典或明确的模块级常量，便于审查、补全和静态检查。
- 如果必须使用 `sys.modules[__name__] = obj` 这类模块替换技巧，必须保留 `__name__` 等基础元信息，并说明为什么不能用普通模块导出。
- MicroPython 专有优化如 `@micropython.viper`、PIO、ASM、`ptr8` 可能让 CPython 静态工具误报。应使用局部 noqa / pylint disable，并用 `mpy-cross` 针对正确架构验证；不要把默认架构下的 `invalid arch` 简单当作源码语法错误。

### 8.5 芯片型号相同不等于接口相同

- 显示屏驱动必须核对接口形态。SPI `ST7789/ST7789V` 不能直接套到 8-bit parallel / I8080 `ST7789V` 板卡上。
- 触摸、音频、PMU、LoRa 等板载外设要按芯片和接口分别判断；不能只按板卡宣传名生成驱动。
- `network.LAN(...)`、WiFi/BLE、GPIO、ADC、SDCard 这类固件或内置能力，不要包装成普通芯片驱动目录。

### 8.6 打包上传前检查

- uPyPI 上传 zip 不要再套一层 `<chip>_driver/` 外壳；zip 根层应直接包含 `package.json`、`README.md`、`LICENSE` 和 `code/`。
- zip 内不要包含 `__pycache__`、`.pyc`、临时脚本、测试残片或本地验证产物。
- 打包后必须按 zip 内的 `package.json.urls` 回查所有源文件是否存在，避免上传后 mip/upypi 安装失败。

## 9. 第一批新增驱动交给 Claude Code 规范化前的补充提示

这部分用于把第一批新增驱动交给 Claude Code “先规范化一遍”时作为上下文输入。目标是整理现有实现，不是重新选源、重新爬取或扩大范围。

### 9.1 本轮规范化范围

只处理下面 11 个新增驱动目录：

| 驱动 | 目录 | 注意事项 |
|---|---|---|
| ST7735 | `lighting/st7735_driver/` | 单文件显示驱动，保留 SPI 形态，不要和 ST7789/ST7789V 并口混用 |
| BMI270 | `sensors/bmi270_driver/` | 多文件驱动，`config_file.py` 和 `i2c_helpers.py` 属于运行时依赖 |
| LSM6DSOX | `sensors/lsm6dsox_driver/` | 多文件驱动，`i2c_helpers.py` 属于运行时依赖 |
| MPU6886 | `sensors/mpu6886_driver/` | 单文件 IMU 驱动，重点检查 `const`、I2C 错误包装、示例循环 |
| HTS221 | `sensors/hts221_driver/` | 多文件驱动，`i2c_helpers.py` 属于运行时依赖 |
| MP34DT05 | `sensors/mp34dt05_driver/` | PDM/I2S 麦克风采集类驱动，示例应体现音频采样链路，不要伪装成寄存器型传感器 |
| SX1262 | `communication/sx1262_driver/` | 多文件 LoRa 驱动，`sx1262.py`、`sx126x.py`、`_sx126x.py` 都要保留 |
| SX1276 | `communication/sx1276_driver/` | 单文件 LoRa 驱动，重点检查 SPI/Pin 依赖注入和轮询 timeout |
| ATECC608A | `misc/atecc608a_driver/` | 多文件安全芯片协议栈，不能只保留 `atecc608a.py` |
| IP5306 | `misc/ip5306_driver/` | 单文件电源管理驱动，重点检查 I2C 地址、寄存器读写、低功耗/关机行为说明 |
| MAX17048 | `sensors/max17048_driver/` | 单文件电量计驱动，源名必须统一为 `max17048.py`，不要保留 `max1704x.py` 这种泛名入口 |

明确不在本轮恢复或新增：
- `communication/lan8720_driver/`：LAN8720 属于板级 `network.LAN(...)` 初始化/固件能力，不作为标准驱动包恢复。
- 第二批候选驱动：`ST7789V_parallel`、`FT6x06`、`AXP2101`、`BMA423`、`ES7210`、`SI4732` 等另行处理，不要混入第一批规范化。
- 历史包：除非第一批驱动直接依赖，不要顺手清理旧目录。

### 9.2 规范化动作边界

Claude Code 应按现有仓库结构做“收敛式整理”：
- 保持 `<domain>/<chip>_driver/{README.md, package.json, LICENSE, code/}` 结构。
- 驱动库文件 import 时不能访问硬件、启动死循环或打印 demo 日志。
- `main.py` 只作为示例，允许包含引脚占位和简单循环，但失败退出不要随手用未确认兼容性的 `sys.exit(1)`。
- 运行时依赖文件必须同步进入 `package.json.urls`；示例 `main.py` 通常不进入 `urls`。
- 不要把多文件驱动强行压成单文件；单文件只是优先原则，不是硬性目标。
- README 可以说明“未在当前环境做真实硬件验证”，不要写成已实测通过，除非确实执行过 `mpremote` 并得到通过输出。

### 9.3 MicroPython 兼容必查项

规范化时必须逐文件检查：
- `const()` 是否有 `from micropython import const`，必要时提供 CPython fallback。
- 是否写死 `uhashlib`、`urandom` 等历史模块名；优先当前通用模块名并提供 fallback。
- 所有 I2C/SPI/UART 轮询是否有 timeout，禁止无界 `while True` 等待硬件状态。
- `try/except OSError` 是否把总线异常转成有上下文的 `RuntimeError`，错误消息应包含地址/寄存器/操作。
- 重复读写缓冲区优先预分配 `bytearray`，避免在高频采样或收发路径反复分配。
- `deinit()` 只在芯片确实有低功耗/睡眠/关闭动作时实现；不要为了形式写空壳误导用户。

### 9.4 示例 `main.py` 必查项

每个示例文件至少检查：
- 顶部必须清楚列出需要用户修改的 `SCL/SDA/SCK/MOSI/MISO/CS/RST/DC/BUSY/IRQ` 等引脚。
- 可能失败的初始化要先把对象变量置为 `None`，避免 `finally` 或清理路径里删除未赋值变量。
- 不要依赖本包没有发布的上游测试文件、图片、字体或平台私有模块。
- 示例循环必须可读、可停、低频输出；不要在默认示例里做高速刷屏、无限打印二进制音频数据或长时间阻塞。
- 异常打印优先用 `sys.print_exception(exc)`；如果导入 `sys`，确认只使用 MicroPython 支持的 API。

### 9.5 建议验证命令

规范化完成后，至少跑下面几类检查，并把结果写进提交说明或工作总结：

```powershell
python -B -m py_compile <driver files>
flake8 --select=E9,F63,F7,F82 <first-batch-driver-dirs>
pylint --errors-only --disable=import-error,no-name-in-module,no-member <first-batch-driver-dirs>
mpy-cross <driver files>
```

注意：
- `mp34dt05_driver/code/mp34dt05.py` 和 `atecc608a_driver/code/packet.py` 如果默认 `mpy-cross` 架构报 `invalid arch`，再用目标板对应架构复查，例如 `-march=armv6m`；不要把这类架构限制误判为普通语法错误。
- `code_checker.py` 可以作为人工审阅辅助，但它不是规范化唯一依据，也不能替代 MicroPython 兼容性判断。

### 9.6 给 Claude Code 的上下文提示文本

可以直接把下面这段交给 Claude Code：

> 请只规范化第一批新增的 11 个驱动目录：`lighting/st7735_driver`、`sensors/bmi270_driver`、`sensors/lsm6dsox_driver`、`sensors/mpu6886_driver`、`sensors/hts221_driver`、`sensors/mp34dt05_driver`、`communication/sx1262_driver`、`communication/sx1276_driver`、`misc/atecc608a_driver`、`misc/ip5306_driver`、`sensors/max17048_driver`。不要恢复 `communication/lan8720_driver`，不要处理历史包或第二批候选驱动。请按 `upy-norm-driver`、`upy-norm-main`/`upy-gen-main`、`upy-gen-readme`、`upy-gen-pkg` 的顺序收敛现有实现；多文件驱动必须保留真实运行时依赖并同步 `package.json.urls`；示例 `main.py` 不要使用不兼容的 `sys.exit(1)`，不要删除未赋值对象；驱动库 import 时不得初始化硬件或启动循环。完成后用 AST/py_compile、flake8 关键错误项、pylint errors-only、MicroPython 分支导入烟测和 mpy-cross 做静态验证。没有真实 `mpremote` 硬件输出时，不要声明硬件已验证。

## 10. 第二批候选驱动规范化注意事项

这部分用于处理 LilyGO ESP32-S3 相关第二批候选驱动。目标是先把器件分类和路径定准，再决定是“搬运现有 MicroPython 驱动并规范化”，还是走 `upy-gen-driver` 冷门驱动生成流程。

### 10.1 候选驱动分类表

| 器件 | 建议目录 | 处理策略 | 关键注意事项 |
|---|---|---|---|
| ST7789V 并口 | `lighting/st7789v_parallel_driver/` | 使用并口/I8080 形态实现后规范化 | 必须和现有 SPI `lighting/st7789_driver/` 分开；不要把 SPI ST7789/ST7789V 驱动套到 8-bit parallel / I8080 屏上 |
| FT6x06 | `input/ft6x06_driver/` | 使用现有 MicroPython 单文件源 | 触摸控制器 I2C 驱动，示例只做坐标读取；不要把显示屏初始化塞进触摸驱动 |
| FT5336 | `input/ft5336_driver/` | 基于 FT5x06 家族驱动适配 | 若来源是 CircuitPython/Adafruit，必须移除 `adafruit_bus_device`、`adafruit_register`、`I2CDevice`、`ROBits` 等依赖或兼容壳，改为纯 `machine.I2C.readfrom_mem/readfrom_mem_into/writeto_mem` |
| FT6206 | `input/ft6206_driver/` | 使用单文件 MicroPython 源并补齐 API 边界 | FT6206/FT6x06/FT5x06 寄存器相近但型号不同，README 要写清验证型号和默认 I2C 地址 |
| AXP2101 | `misc/axp2101_driver/` | 从 XPowersLib MicroPython 部分裁剪 | PMU 寄存器较多，不能机械翻译；保留 `I2CInterface.py` 但应收敛为纯 MicroPython I2C helper，不要保留 CircuitPython/Adafruit 分支 |
| BMA423 | `sensors/bma423_driver/` | 使用现有纯 MicroPython 实现 | `bma423.py` 和 `bma423conf.bin` 同属运行时依赖；`.bin` 是 Bosch feature-engine 配置 blob，不是测试文件；`package.json.urls` 必须包含它 |
| DRV2605L | `motor_drivers/drv2605l_driver/` | 规范化现有 MicroPython 驱动 | 触觉马达驱动，不是普通 PWM 马达；保留 waveform/effect library、mode、GO 状态轮询 timeout |
| MAX98357A | 不建议建标准驱动目录 | 只作为 I2S TX 示例或板级音频链路说明 | 该器件无 I2C/SPI 寄存器配置，MicroPython 侧核心是 `machine.I2S` 输出；不要做空壳 `max98357a.py` 伪驱动 |
| ES7210 | `signal_acquisition/es7210_driver/` | 已按 `upy-gen-driver` 冷门生成思路生成 I2C 控制驱动草案 | 它是 I2C 配置 + I2S/TDM RX 数据链路；驱动只管寄存器配置，`main.py` 示例负责 `machine.I2S` 采集；未硬件验证 |
| APA102 | `lighting/apa102_driver/` | 使用现有 DotStar/APA102 MicroPython 源 | 这是 clock + data 的 SPI-like LED，不是 NeoPixel/WS2812；API 应体现像素缓冲、亮度、`show()` |
| MIA-M10Q | `sensors/mia_m10q_driver/` | 使用 NMEA/UART GPS 解析器做薄封装 | 先按 UART NMEA GNSS 模块处理；不要在没有 UBX 文档和硬件验证时伪装成完整 u-blox 二进制协议驱动 |
| MSM381A3729H9CP | 不建议建标准驱动目录 | 只作为 ADC/音频输入链路说明 | 模拟输出 MEMS 麦克风，无寄存器驱动；若接 MCU ADC 用 `machine.ADC` 示例，若接 ES7210 则归入 ES7210 音频采集链路 |
| CC1101 | `communication/cc1101_driver/` | 已生成 MicroPython SPI 驱动包并按 GPL-3.0 标记 | 参考源 `eydam-prototyping/cc1101` 是 GPL-3.0；必须保留单独 `LICENSE`，`package.json`/README 也必须写 GPL-3.0；不要混成 MIT 包；未硬件验证 |
| SI4732 | `communication/si4732_driver/` | 已按 `upy-gen-driver` 冷门生成思路生成 I2C 命令驱动草案 | 必须基于 datasheet + AN332 命令指南；第一版先做 power/tune/status/property，不要一次性承诺完整 RDS/seek 功能；未硬件验证 |

### 10.2 不要单独封装的器件

`MAX98357A` 和 `MSM381A3729H9CP` 默认不要生成标准 `<chip>_driver` 包。

- `MAX98357A` 是 I2S 数字功放，控制主要来自硬件引脚和 I2S 时钟/数据流。MicroPython 侧应写 `machine.I2S(..., mode=I2S.TX)` 示例，而不是写空驱动类。
- `MSM381A3729H9CP` 是模拟输出 MEMS 麦克风。若接 ADC，示例应放在 ADC/音频采样链路；若接 ES7210，驱动责任在 ES7210，不在麦克风。
- 这两类器件可以在 README 或板级示例中出现，但不要进入 `upy-pack-driver` 作为普通寄存器型驱动发布。

### 10.3 冷门生成类驱动

`ES7210` 和 `SI4732` 没有足够成熟的纯 MicroPython 标准驱动时，按 `G:\MicroPython_Skills\upy-gen-driver\SKILL.md` 处理。

硬性要求：
- 先找 datasheet / programming guide / 官方或成熟 C/C++ 源码。
- 先用 `extract_pdf.py` 或 `convert_arduino.py` 提取理解材料，形成 `{chip}_understanding.json` 这类中间理解文件。
- 先生成 `{chip}_debug.py` 单文件调试版，包含 I2C scan、ID/状态/已知寄存器验证、初始化序列、功能自检。
- 没有 `mpremote` 硬件验证输出 `SELF_TEST_PASS` 前，不得声称驱动已硬件验证或生产可用。
- 最终准备上传的驱动包目录只保留运行时文件：`README.md`、`package.json`、`LICENSE` 和 `code/` 下的驱动/示例文件。`SOURCE_*.cpp/.h`、`SOURCE_LICENSE`、`*_understanding.json` 这类中间材料不要放进待上传包目录。

ES7210 额外注意：
- 目录用 `signal_acquisition/es7210_driver/`，不要放 `misc/`。
- 驱动 API 聚焦 I2C 寄存器配置：复位、时钟、采样率、通道、增益、TDM/I2S 格式、静音/电源状态。
- `main.py` 示例负责展示 `machine.I2S(..., mode=I2S.RX)` 采集，不要把 I2S 对象在驱动类内部创建成硬依赖。

SI4732 额外注意：
- 目录用 `communication/si4732_driver/`。
- 命令型芯片必须实现 CTS/ERR/STC 等状态等待，所有等待都要 timeout。
- 第一版建议 API 控制范围：`power_up()`、`power_down()`、`get_revision()`、`set_property()`、`get_property()`、`fm_tune_freq()`、`am_tune_freq()`、`get_tune_status()`。
- RDS、seek、SW/LW 细节可以后续扩展，不要在 README 中写成完整功能已覆盖。

### 10.4 现有源规范化类驱动

下面这些可以先抓取现有 MicroPython 或接近 MicroPython 的源，再按标准链路整理：

- `FT6x06` / `FT5336` / `FT6206`：统一先确认 I2C 地址、中断引脚、触点数量、坐标寄存器和屏幕方向映射。触摸驱动不要依赖显示屏驱动。若从 CircuitPython/Adafruit 移植，不能保留 `adafruit_bus_device`、`adafruit_register` 或本地仿造的 `I2CDevice`/`ROBits` 壳；应直接使用 MicroPython 官方 `machine.I2C` 的 `readfrom_mem()`、`readfrom_mem_into()`、`writeto_mem()`。
- `AXP2101`：PMU 驱动要把电源 rail、充电、电池、电压/电流读取分成清晰 API。setter 只能修改自己负责的寄存器位和 shadow state。`I2CInterface.py` 可以作为多文件运行时依赖保留，但只保留 MicroPython I2C helper，不保留 CircuitPython 分支。
- `BMA423`：`bma423conf.bin` 是运行时资产，不是测试文件。它用于 `load_features_config()` 上传 Bosch feature-engine 配置，涉及 step/activity/tilt 等功能；打包 zip 和 `package.json.urls` 必须保留它，并确认运行时 `open("bma423conf.bin", "rb")` 能找到该文件。
- `DRV2605L`：I2C motor/触觉驱动，`play_effect()` 这类方法要等待 GO 位清除或提供非阻塞选项。
- `APA102`：优先单文件，避免动态依赖字体、图片或板卡 demo。
- `MIA-M10Q`：若使用通用 NMEA parser，应说明这是 MIA-M10Q 的 UART/NMEA 封装，不是完整 u-blox 配置驱动。
- `CC1101`：当前包接受 GPL-3.0 前提；如果上游 GPL 后续不可接受，必须替换来源或重新生成 clean-room 实现，不能只改 license 字段规避。

### 10.5 给 Claude Code 的上下文提示文本

可以直接把下面这段交给 Claude Code：

> 请处理第二批候选驱动时先分类，不要一律建 `<chip>_driver`。`MAX98357A` 和 `MSM381A3729H9CP` 不要作为标准驱动封装，只写 I2S/ADC 或音频链路示例说明。`ES7210` 和 `SI4732` 走 `upy-gen-driver` 冷门驱动流程，先基于 datasheet/programming guide 生成理解清单和 debug 自检版；最终待上传包目录不要保留 `SOURCE_*.cpp/.h`、`SOURCE_LICENSE`、`*_understanding.json` 等中间材料。`ST7789V_parallel` 必须独立于现有 SPI `st7789_driver`，不要混用接口。`FT5336`、`FT6206`、`FT6x06` 这类触摸驱动如果从 CircuitPython/Adafruit 移植，必须改成纯 `machine.I2C.readfrom_mem/readfrom_mem_into/writeto_mem`，不要保留 `adafruit_bus_device`、`adafruit_register`、`I2CDevice`、`ROBits` 或本地兼容壳。`AXP2101` 可以保留 `I2CInterface.py`，但该 helper 必须是纯 MicroPython I2C helper。`BMA423` 的 `bma423conf.bin` 是 Bosch feature-engine 运行时配置 blob，必须保留并写入 `package.json.urls`。`CC1101` 当前按 GPL-3.0 包处理，必须保留 LICENSE 并在 package/README 中明确 GPL-3.0。所有规范化继续遵守 `upy-norm-driver`、`upy-gen-main`/`upy-norm-main`、`upy-gen-readme`、`upy-gen-pkg`、`upy-pack-driver` 顺序；示例 `main.py` 只能作为硬件接线和最小读写演示，驱动库 import 时不得初始化硬件或进入循环。

### 10.6 第二批当前已生成状态

当前仓库中已经按第二批策略生成/暂存了下面这些目录。Claude Code 后续工作应基于这些目录继续规范化，不要重新爬取同名驱动，除非发现许可证或运行时依赖确实有问题。

| 驱动 | 当前目录 | 当前状态 | 后续重点 |
|---|---|---|---|
| ST7789V 并口 | `lighting/st7789v_parallel_driver/` | 已放入并口驱动、README、package、main | 继续检查 Pin API、并口写时序、不要改成 SPI 驱动 |
| FT6x06 | `input/ft6x06_driver/` | 已放入驱动、README、package、main | 去掉 import 时打印；中断回调和轮询示例分清 |
| FT5336 | `input/ft5336_driver/` | 已适配为纯 `machine.I2C` 版本，并同步 `FT5336` 类名、`touches()` 示例 API | 不要恢复 `adafruit_bus_device` / `adafruit_register` / `I2CDevice` / `ROBits` 依赖或兼容壳 |
| FT6206 | `input/ft6206_driver/` | 已解除对 display 对象的硬依赖，并修正方向映射兜底返回 | 后续可进一步统一 API 为 `touches()` / `point()` |
| AXP2101 | `misc/axp2101_driver/` | 已保留 `axp2101.py` + `I2CInterface.py`，并把 `I2CInterface.py` 收敛为纯 MicroPython I2C helper | PMU 方法很多，规范化时优先保守修兼容，不要重写电源策略；不要恢复 CircuitPython 分支 |
| BMA423 | `sensors/bma423_driver/` | 已保留 `bma423.py` + `bma423conf.bin` | `.bin` 是 6144 字节 Bosch feature-engine 配置 blob，必须保留并进入 `package.json.urls` |
| DRV2605L | `motor_drivers/drv2605l_driver/` | 已放入驱动、README、package、main | 补 GO 状态轮询 timeout 或说明 `play()` 为非阻塞 |
| APA102 | `lighting/apa102_driver/` | 已放入 DotStar/APA102 驱动、README、package、main | 保持 SPI-like buffer/show API，不要和 NeoPixel 混用 |
| MIA-M10Q | `sensors/mia_m10q_driver/` | 已放入 NMEA parser、README、package、main，并修正 `utime/time` fallback | README 必须说明不是完整 UBX 配置驱动 |
| ES7210 | `signal_acquisition/es7210_driver/` | 已生成冷门 I2C 控制驱动草案；`SOURCE_*` 和 understanding 中间材料已从包目录清理 | 未硬件验证；驱动只管 I2C 配置，I2S 采样放在 main 示例/应用层 |
| SI4732 | `communication/si4732_driver/` | 已生成冷门 I2C 命令驱动草案；`SOURCE_*` 和 understanding 中间材料已从包目录清理 | 未硬件验证；第一版只承诺 power/property/tune/status，不承诺完整 RDS/seek |
| CC1101 | `communication/cc1101_driver/` | 已生成单文件 MicroPython SPI 驱动、README、package、main，并保留 GPL-3.0 `LICENSE` | 未硬件验证；配置寄存器、包格式和地区合法频点必须由使用者确认 |

明确仍未创建：
- `misc/max98357a_driver/`
- `sensors/msm381a3729h9cp_driver/`

这两个不是遗漏，而是刻意避免伪驱动封装。

### 10.7 第二批已做过的静态验证

当前第二批有效驱动已做过以下静态检查：
- AST 解析：25 个 `.py`，0 错误
- `flake8 --select=E9,F63,F7,F82`：通过
- `pylint --errors-only --disable=import-error,no-name-in-module,no-member`：通过
- `package.json` JSON 解析：12 个包，0 错误
- `package.json.urls` 文件存在性：0 缺失
- CPython 导入烟测：12 个驱动模块，0 错误
- `mpy-cross`：25 个 `.py` 逐文件编译通过，输出到临时 `.mpy`，未在驱动目录留下验证产物

注意：
- 这些检查只能说明语法、基础导入和打包引用没有明显错误。
- 没有真实 `mpremote` 硬件验证输出，所以 README、总结和包描述都不得写“已实测通过”。
- Claude Code 后续规范化时可以重复这些检查，但不要把 `code_checker.py` 当作唯一依据。

### 10.8 给 Claude Code 的当前规范化提示文本

可以直接把下面这段交给 Claude Code：

> 请基于当前仓库中已经生成的第二批目录继续规范化，不要重新爬取同名驱动，也不要新增 `max98357a_driver` 或 `msm381a3729h9cp_driver`。本轮只处理这些目录：`lighting/st7789v_parallel_driver`、`input/ft6x06_driver`、`input/ft5336_driver`、`input/ft6206_driver`、`misc/axp2101_driver`、`sensors/bma423_driver`、`motor_drivers/drv2605l_driver`、`lighting/apa102_driver`、`sensors/mia_m10q_driver`、`signal_acquisition/es7210_driver`、`communication/si4732_driver`、`communication/cc1101_driver`。`FT5336` 当前应保持纯 `machine.I2C` 实现：主类为 `FT5336`，示例 API 为 `touches()`，不得恢复 `adafruit_bus_device`、`adafruit_register`、`I2CDevice`、`ROBits` 或本地兼容壳；读写寄存器直接使用 `readfrom_mem()`、`readfrom_mem_into()`、`writeto_mem()`。`AXP2101` 必须保留 `I2CInterface.py`，但该 helper 只保留 MicroPython I2C 分支，不要恢复 CircuitPython/Adafruit 逻辑。`BMA423` 必须保留 `bma423conf.bin`，它是 Bosch feature-engine 运行时配置 blob，不是测试文件。`CC1101` 当前按 GPL-3.0 包处理，必须保留 `LICENSE`，不得改成 MIT；如果仓库后续不能接受 GPL，请先替换来源或重做 clean-room 实现。`MAX98357A` 和 `MSM381A3729H9CP` 不是遗漏，不要生成空壳驱动。`ES7210/SI4732` 的最终包目录不要保留冷门生成中间材料，只保留运行时驱动、示例、README、package、LICENSE。重点检查 MicroPython 兼容 fallback、`const`、`ustruct/struct`、无界轮询 timeout、驱动库 import 时不得初始化硬件或进入循环、`main.py` 不得使用不兼容的 `sys.exit(1)`。没有真实 `mpremote` 输出 `SELF_TEST_PASS` 前，不要声明任何第二批驱动已硬件验证或生产可用。

### 10.9 本次复查新增硬性项

- 分支内赋值后返回的函数必须有兜底 `return` 或 `raise`，例如触摸方向映射不能让 `point` 只在部分 rotation 分支里赋值。
- 避免 `from xxx import *` 让静态检查和后续维护无法确认真实依赖；多文件驱动应显式导入运行时需要的辅助类或常量。
- 类型注解不要依赖只在 MicroPython 分支中存在的名字，例如 `I2C` 只在 `machine` 可用时才存在；可省略注解或用通用占位，避免 CPython 静态检查误报。
- `utime/time` fallback 要显式使用模块别名和条件判断，不要依赖 `except NameError` 去捕获可能不存在的模块名。
- 冷门驱动生成材料和上游源码分析材料属于工作区材料，不属于最终 uPyPI 上传包内容；待上传目录应只保留运行时文件。
- 从 CircuitPython/Adafruit 移植来的驱动，不能把 `adafruit_bus_device` / `adafruit_register` 依赖替换成本地仿造的兼容壳后就算完成。MicroPython 驱动应直接使用目标端口官方 API，例如 `machine.I2C.readfrom_mem()`、`readfrom_mem_into()`、`writeto_mem()`。
- 重命名主类或公共 API 后，必须同步检查 `main.py`、README、`package.json.urls` 和兼容 alias。例如 `FT5336` 不能只保留上游 `Adafruit_FT5336` 类名导致示例导入失败。
- 二进制运行时资产必须当作包内容处理。`bma423conf.bin` 这类文件要写入 `package.json.urls`，README 要说明用途，并确认驱动运行时能按当前打开路径找到。
- `upy-pack-driver` 的默认 MIT LICENSE 模板不能机械套用到所有包。若上游或参考源是 GPL-3.0（例如当前 `CC1101`），必须保留对应许可证并同步 `package.json` / README，不得只改字段规避。

### 10.10 第三批候选驱动当前状态

本轮新增了第三批候选目录，均为“源码候选/冷生成候选”，未硬件验证。Claude Code 后续应基于这些目录继续规范化，不要重新爬取同名驱动，除非发现许可证、寄存器或运行时依赖确实有问题。

| 驱动/芯片 | 当前目录 | 当前状态 | 后续重点 |
|---|---|---|---|
| ST7789T3 / ST7789V2 | 复用 `lighting/st7789_driver/` | 不新建目录 | 作为 ST7789 面板变体处理；只需在 README/main 中确认尺寸、offset、RGB/BGR、rotation 和初始化差异 |
| ST7796 / ST7796S | `lighting/st7796_driver/` | 已生成单文件 SPI 候选驱动 | 初始化序列参考 `lvgl_micropython`，但不得引入 `lvgl`/`display_driver_framework`；必须确认屏幕尺寸、MADCTL、RGB/BGR、背光极性 |
| CST328 | `input/cst328_driver/` | 已生成无 GUI 基类的单文件候选驱动 | 参考 Peter Hinch `micropython-touch`；I2C 地址默认 `0x1A`；16-bit register 访问；触摸数据从 `0xD000` 读取 |
| CST816 / CST816S / CST816T / CST816D | `input/cst816_driver/` | 已生成单文件候选驱动 | 参考 Peter Hinch + NeoStormer；默认地址 `0x15`；注意该类芯片可能未触摸时不响应 I2C，`main.py` 不要把 scan/ID 当成唯一通过条件 |
| FT6336 / FT6336U | `input/ft6336_driver/` | 已生成单文件候选驱动 | 参考 Waveshare FT6336U 和 `micropython-ft6x36`；默认地址 `0x38`，Waveshare 示例 chip id `0x64`；当前只读 touch1，后续决定是否扩多点 |
| QMI8658 / QMI8658C | `sensors/qmi8658_driver/` | 已生成单文件 IMU 候选驱动 | 参考 Waveshare `test_imu.py`；默认地址 `0x6B`，WHO_AM_I `0x05`；默认配置 acc 8g、gyro 512 dps、ODR 1000 Hz |
| PCF85063 / PCF85063ATL | `misc/pcf85063_driver/` | 已生成单文件 RTC 候选驱动 | 参考 Waveshare `test_rtc.py`；默认地址 `0x51`；当前覆盖 datetime 和基础 alarm，不承诺完整 timer/clock output |
| TCA9554 | `input/tca9554_driver/` | 已按 RobTillaart Arduino 逻辑冷生成单文件候选驱动 | 地址范围 `0x20..0x27`；寄存器为 input `0x00`、output `0x01`、polarity `0x02`、config `0x03` |
| ES8311 | `signal_acquisition/es8311_driver/` | 已将 M5Stack `__init__.py + reg.py` 机械合并为单文件候选 | 仍需深度规范化；I2C 配置 codec，音频流由板级 `machine.I2S` 负责；不要把 I2S 对象硬编码进驱动类 |

明确仍不建议生成标准寄存器驱动：

- `PCM5101APWR`：I2S DAC，通常由 `machine.I2S(..., mode=I2S.TX)` 输出数据，芯片本身无 I2C/SPI 寄存器配置；可写板级 I2S 示例，不要生成空壳驱动。
- `APA2068KAI-TRG`：模拟/功放类器件，通常由音频模拟链路、使能脚或外围电路决定；没有标准 I2C/SPI 驱动接口时不要包化。
- `NS4150B`：音频功放，常见用法是 I2S/PWM/模拟音频输入加使能脚；若板卡只有 enable/mute GPIO，可写板级示例，不要伪装成复杂驱动。

### 10.11 第三批规范化新增注意事项

- `ST7796/ST7796S` 不能直接复用 `lighting/st7789_driver`；虽然都是 SPI TFT，但初始化序列、默认尺寸和部分寄存器不同。可以复用绘图 API 设计，不要复用 ST7789 初始化表。
- `ST7789T3/ST7789V2` 优先复用现有 `lighting/st7789_driver`。除非明确需要特殊 init sequence，否则不要新建 `st7789t3_driver` 或 `st7789v2_driver`。
- CST 系列触摸驱动不得依赖 `peterhinch` 的 GUI `ABCTouch` 基类，也不得保留 CircuitPython `adafruit_bus_device.i2c_device`。必须改成纯 `machine.I2C` 单文件。
- `CST816/CST816S/CST816T/CST816D` 的 I2C 地址和响应行为要写清楚：地址通常是 `0x15`，并且部分实现说明未触摸时可能不响应 I2C。示例 `main.py` 应允许“第一次触摸后再读 ID/版本”的路径。
- `FT6336/FT6336U` 与现有 `FT6x06/FT5336` API 应尽量统一为 `touches()` / `point()` / `get_touch_count()` 这类形式，但不要盲目合并包，避免 chip id 和手势寄存器差异被隐藏。
- `QMI8658/QMI8658C` 规范化时必须保留 WHO_AM_I 校验、量程/ODR shadow state 和 raw-to-unit 转换公式；不要在 `__init__` 内创建 I2C 或硬编码 Waveshare 引脚。
- `PCF85063/PCF85063ATL` 使用 BCD 时间格式，年份基准当前候选按 Waveshare 示例 `1970 + reg_year`，如目标板期望 `2000 + reg_year`，必须在 README/main 中明确并可配置。
- `TCA9554` 的方向寄存器语义是 `1=input, 0=output`，不要写反；`deinit()` 可把全部 pin 恢复 input。
- `ES8311` 是 codec 配置驱动，不是 I2S 数据收发驱动。驱动只负责 I2C 寄存器配置、采样率、格式、音量、mic/dac power；音频 TX/RX 示例放在 `main.py` 或板级应用层。
- 来自 Waveshare 的 `FT6336/QMI8658/PCF85063` 包当前按 Apache-2.0 处理；来自 Peter Hinch、NeoStormer、M5Stack、RobTillaart 的候选按其上游 MIT/兼容许可证处理。不要机械套用 MIT。

### 10.12 第三批给 Claude Code 的提示文本

可以直接把下面这段交给 Claude Code：

> 请规范化第三批候选驱动时只处理这些目录：`lighting/st7796_driver`、`input/cst328_driver`、`input/cst816_driver`、`input/ft6336_driver`、`sensors/qmi8658_driver`、`misc/pcf85063_driver`、`input/tca9554_driver`、`signal_acquisition/es8311_driver`。`ST7789T3/ST7789V2` 不要新建目录，优先复用 `lighting/st7789_driver`，只在 README/main 中补充 panel variant、尺寸、offset、rotation、RGB/BGR 和 init 差异。`ST7796/ST7796S` 可以复用 ST7789 的绘图 API 形状，但不能复用 ST7789 初始化序列；当前候选参考 `lvgl_micropython` 初始化序列，但最终驱动不得依赖 `lvgl` 或 `display_driver_framework`。CST 系列不得依赖 Peter Hinch GUI `ABCTouch` 或 CircuitPython `adafruit_bus_device`，必须是纯 `machine.I2C` 单文件；`CST816` 系列要说明默认地址 `0x15` 和“未触摸时可能不响应 I2C”的风险。`FT6336/FT6336U` 默认地址 `0x38`，Waveshare 示例 chip id `0x64`，后续决定是否扩多点触控并尽量与 FT6x06/FT5336 API 对齐。`QMI8658/QMI8658C` 保留 WHO_AM_I `0x05`、量程/ODR shadow state 和 raw-to-unit 转换，不要在类内创建 I2C 或硬编码 Waveshare 引脚。`PCF85063/PCF85063ATL` 注意 BCD 和年份基准，必要时让 `year_base` 可配置。`TCA9554` 地址范围 `0x20..0x27`，方向寄存器 `1=input, 0=output`，不要写反。`ES8311` 是 I2C codec 配置驱动，音频数据流由 `machine.I2S` 的板级示例负责，驱动类内部不要创建 I2S。`PCM5101APWR`、`APA2068KAI-TRG`、`NS4150B` 不要生成空壳标准驱动；如果需要，只写 I2S/GPIO 使能板级示例。所有候选均未硬件验证，README 和 package 不得写“已验证/生产可用”；按 `upy-norm-driver`、`upy-gen-main`、`upy-norm-main`、`upy-gen-readme`、`upy-gen-pkg`、`upy-pack-driver` 顺序处理，并检查 MicroPython 兼容语法、无 CircuitPython 依赖、无 `sys.exit()`、无无限轮询、import 时不初始化硬件或进入循环。

### 10.13 第三批交给 Claude Code 前的强制上下文

把第三批交给 Claude Code 规范化时，不要只说“帮我规范化这些驱动”。必须同时给出 skill 路径、处理范围、当前目录状态和不允许做的事，避免它重新爬取、误删依赖、误写硬件验证结论或生成空壳驱动。

必须显式要求 Claude Code 先阅读这些 skill：
- `G:/MicroPython_Skills/upy-norm-driver/SKILL.md`：规范化驱动 `.py`，重点是依赖注入、MicroPython 兼容、`const`、异常包装、timeout、import 时无硬件副作用。
- `G:/MicroPython_Skills/upy-gen-main/SKILL.md`：没有 `main.py` 时从驱动 API 生成示例。
- `G:/MicroPython_Skills/upy-norm-main/SKILL.md`：已有 `main.py` 时规范化示例。
- `G:/MicroPython_Skills/upy-gen-readme/SKILL.md`：根据驱动和示例生成/修正 README。
- `G:/MicroPython_Skills/upy-gen-pkg/SKILL.md`：生成/修正 `package.json`，确保 `urls` 覆盖运行时文件。
- `G:/MicroPython_Skills/upy-pack-driver/SKILL.md`：整理标准包目录，但不得机械套用 MIT；许可证以候选来源为准。
- `G:/MicroPython_Skills/upy-deploy-test/SKILL.md`：只有用户提供真实 MicroPython 设备和 COM 口时才做硬件验证；没有 `SELF_TEST_PASS` 不得写“已验证”。

第三批当前只处理这些目录：
- `lighting/st7796_driver/`
- `input/cst328_driver/`
- `input/cst816_driver/`
- `input/ft6336_driver/`
- `sensors/qmi8658_driver/`
- `misc/pcf85063_driver/`
- `input/tca9554_driver/`
- `signal_acquisition/es8311_driver/`

第三批当前包目录是候选状态，通常为：`LICENSE`、`README.md`、`package.json`、`code/<chip>.py`。如果目录内没有 `code/main.py`，应使用 `upy-gen-main` 基于实际驱动 API 生成最小示例；不要凭空写板卡固定引脚，所有引脚用清晰占位常量，并在 README 中说明需要用户按目标板修改。

本批明确不要新增这些标准驱动目录：
- `st7789t3_driver` / `st7789v2_driver`：优先复用 `lighting/st7789_driver/`，只补充 panel variant、尺寸、offset、rotation、RGB/BGR、init 差异。
- `pcm5101apwr_driver`：PCM5101APWR 通常由 `machine.I2S(..., mode=I2S.TX)` 输出音频，不是寄存器驱动。
- `apa2068kai_trg_driver`：APA2068KAI-TRG 更偏模拟/功放链路或 enable 脚控制，无标准总线寄存器驱动时不要包化。
- `ns4150b_driver`：NS4150B 更偏音频功放/enable 或 mute GPIO，适合板级示例，不适合空壳标准驱动。

第三批逐项注意：
- `ST7796/ST7796S`：可复用 ST7789 绘图 API 形状，但不能复用 ST7789 初始化表；不得依赖 `lvgl` 或 `display_driver_framework`；确认尺寸、MADCTL、RGB/BGR、背光极性。
- `CST328`：纯 `machine.I2C`；默认地址 `0x1A`；16-bit register 访问；触摸数据从 `0xD000` 读取；不要依赖 Peter Hinch GUI `ABCTouch`。
- `CST816/CST816S/CST816T/CST816D`：纯 `machine.I2C`；默认地址 `0x15`；部分实现未触摸时可能不响应 I2C，`main.py` 不要把 `i2c.scan()` 或 ID 读取作为唯一成功条件。
- `FT6336/FT6336U`：纯 `machine.I2C`；默认地址 `0x38`；Waveshare 示例 chip id `0x64`；API 尽量和 `FT6x06/FT5336` 对齐，如 `touches()`、`point()`、`get_touch_count()`。
- `QMI8658/QMI8658C`：保留 WHO_AM_I `0x05` 校验、量程/ODR shadow state、raw-to-unit 转换；不要在驱动类内部创建 I2C 或硬编码 Waveshare 引脚。
- `PCF85063/PCF85063ATL`：BCD 时间格式；年份基准要可解释，必要时提供 `year_base` 参数；不要承诺完整 timer/clock output，除非代码确实实现。
- `TCA9554`：地址范围 `0x20..0x27`；寄存器 input `0x00`、output `0x01`、polarity `0x02`、config `0x03`；方向语义是 `1=input, 0=output`，不要写反。
- `ES8311`：这是 I2C codec 配置驱动，不是 I2S 数据驱动；驱动只负责寄存器配置、采样率、格式、音量、mic/dac power；音频数据 TX/RX 放在 `main.py` 或板级应用层，类内部不要创建 `machine.I2S`。

第三批规范化完成后至少执行这些静态检查，并在总结中说明“仅静态检查通过，未硬件验证”：
```powershell
python -B -m py_compile <third-batch .py files>
flake8 --select=E9,F63,F7,F82 <third-batch dirs>
pylint --errors-only --disable=import-error,no-name-in-module,no-member <third-batch dirs>
mpy-cross <third-batch .py files>
```

附加硬性检查：不得出现 `typing`、PEP604 `| None`、`raise ... from exc`、未导入的 `const()`、`sys.exit()`、无 timeout 的无限轮询、import 时硬件初始化、CircuitPython/Adafruit 依赖或本地仿造兼容壳。`package.json.urls` 必须指向真实存在的运行时文件；如果后续要上传 uPyPI zip，zip 根目录直接包含 `package.json`、`README.md`、`LICENSE`、`code/`，不要再套一层 `<chip>_driver/`。

可直接发给 Claude Code 的完整指令：

> 请在 `G:/GraftSense-Drivers-MicroPython#` 中只规范化第三批候选驱动。开始前必须完整阅读并遵守这些 skill：`G:/MicroPython_Skills/upy-norm-driver/SKILL.md`、`G:/MicroPython_Skills/upy-gen-main/SKILL.md`、`G:/MicroPython_Skills/upy-norm-main/SKILL.md`、`G:/MicroPython_Skills/upy-gen-readme/SKILL.md`、`G:/MicroPython_Skills/upy-gen-pkg/SKILL.md`、`G:/MicroPython_Skills/upy-pack-driver/SKILL.md`；如果要真实上板验证，再读 `G:/MicroPython_Skills/upy-deploy-test/SKILL.md`。本轮只处理 `lighting/st7796_driver`、`input/cst328_driver`、`input/cst816_driver`、`input/ft6336_driver`、`sensors/qmi8658_driver`、`misc/pcf85063_driver`、`input/tca9554_driver`、`signal_acquisition/es8311_driver`。不要重新爬取同名驱动，除非发现许可证、寄存器定义或运行时依赖有明确错误。不要新增 `st7789t3_driver`、`st7789v2_driver`、`pcm5101apwr_driver`、`apa2068kai_trg_driver`、`ns4150b_driver`；`ST7789T3/ST7789V2` 复用 `lighting/st7789_driver`，PCM5101APWR/APA2068KAI-TRG/NS4150B 只适合 I2S/GPIO/板级示例，不要生成空壳标准驱动。当前第三批通常只有 `code/<chip>.py`、`README.md`、`package.json`、`LICENSE`，如果没有 `code/main.py`，请用 `upy-gen-main` 基于实际 API 生成最小示例，引脚全部用可修改常量，不要硬编码某块板。规范化时保持纯 MicroPython：I2C 使用 `machine.I2C.readfrom_mem/readfrom_mem_into/writeto_mem`，SPI/Pin/I2S 也必须外部注入；不得保留 CircuitPython/Adafruit 依赖或本地兼容壳；不得使用 `typing`、`| None`、`sys.exit()`、无 timeout 无限轮询；驱动 import 时不得初始化硬件、扫描总线、打印 demo 或进入循环。逐项注意：ST7796 不得复用 ST7789 初始化表且不得依赖 lvgl；CST328 默认 `0x1A`、16-bit register、触摸数据 `0xD000`；CST816 系列默认 `0x15` 且可能未触摸不响应 I2C；FT6336 默认 `0x38`、chip id `0x64`，API 尽量和 FT6x06/FT5336 对齐；QMI8658 保留 WHO_AM_I `0x05`、量程/ODR shadow state 和单位转换；PCF85063 使用 BCD，年份基准需可解释或可配置；TCA9554 方向寄存器语义 `1=input, 0=output`；ES8311 只做 I2C codec 配置，音频流由 `machine.I2S` 示例负责。完成后运行 `py_compile`、`flake8 --select=E9,F63,F7,F82`、`pylint --errors-only --disable=import-error,no-name-in-module,no-member`、`mpy-cross`，并检查 `package.json.urls` 文件存在。没有真实设备和 `mpremote` 输出 `SELF_TEST_PASS` 前，README、package 和总结都只能写“静态检查通过/未硬件验证”，不得写“已验证/生产可用”。

## 11. 对 Claude Code 的执行要求

- 先输出分类结论，再动文件
- 如果是 `LAN8720`，先拦住，不要直接按硬件驱动包化
- 如果是多文件驱动，先列出必须保留的辅助文件，再决定 `main.py`、`README.md`、`package.json`
- 不要为了“看起来整齐”删掉真实依赖
- 不要把板级初始化脚本伪装成标准芯片驱动

## 12. 结论

`LAN8720` 默认不建议作为 `communication/lan8720_driver/` 的标准驱动包处理。它更像 middleware / board bootstrap。其余驱动按“单文件可归一则归一，真实依赖文件必须保留”的原则进入规范化链路。
