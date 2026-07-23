# CST816/CST816S/CST816T/CST816D MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

CST816 系列（CST816/CST816S/CST816T/CST816D）I2C 电容触摸控制器驱动，适用于 MicroPython 平台。通过 I2C 接口读取触摸坐标、手势类型和触摸点数，支持中断模式和轮询模式。

仅静态检查通过，未硬件验证。

## 主要功能

- 支持 CST816/CST816S/CST816T/CST816D 多个型号
- 读取触摸点坐标（X/Y）
- 手势识别：上滑、下滑、左滑、右滑、单击、双击、长按
- 触摸点数检测
- 芯片 ID 和固件版本读取
- 中断模式（IRQ）和轮询模式
- 硬件复位支持
- 简洁的 API 接口

## 硬件要求

### 推荐测试硬件

- 任意支持 MicroPython 的开发板（ESP32 / RP2040 等）
- CST816 / CST816S / CST816T / CST816D 触摸屏模块

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| RST  | 复位引脚（可选） |
| IRQ  | 中断引脚（可选） |

## 软件环境

- **固件版本**：MicroPython v1.23.0 及以上
- **驱动版本**：v1.0.0
- **依赖库**：无外部依赖，仅使用 `machine` 和 `time` 内置模块

## 文件结构

```
├── code/
│   ├── cst816.py   # 核心驱动文件
│   └── main.py     # 测试示例
├── package.json    # 包配置文件
└── README.md       # 说明文档
```

## 文件说明

- **cst816.py**：CST816 系列触摸控制器核心驱动，包含寄存器定义、手势常量、I2C 读写和触摸数据解析逻辑
- **main.py**：驱动测试示例程序，演示 I2C 初始化、设备扫描、芯片 ID 读取和触摸数据轮询

## 快速开始

### 1. 复制文件

将 `code/cst816.py` 上传到 MicroPython 设备的 `/lib/` 目录。

### 2. 接线

| CST816 模块 | 开发板 |
|-------------|--------|
| VCC         | 3.3V   |
| GND         | GND    |
| SCL         | GPIO22 |
| SDA         | GPIO21 |
| RST         | GPIO25（可选） |
| IRQ         | GPIO26（可选） |

### 3. 最小可运行代码

```python
from machine import I2C, Pin
from cst816 import CST816

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建触摸驱动实例（无中断模式）
touch = CST816(i2c, address=0x15, width=240, height=240)

# 等待设备就绪后触摸屏幕读取数据
import time
time.sleep(0.1)

# 读取触摸点
point = touch.read_point()
if point is not None:
    print("x=%d, y=%d, gesture=%d" % (point["x"], point["y"], point["gesture"]))
else:
    print("No touch detected")

# 释放资源
touch.deinit()
```

### 4. 完整测试代码

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 CST816 触摸驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time

from cst816 import CST816, GESTURE_NONE, GESTURE_UP, GESTURE_DOWN
from cst816 import GESTURE_LEFT, GESTURE_RIGHT, GESTURE_CLICK
from cst816 import GESTURE_DOUBLE_CLICK, GESTURE_LONG_PRESS

# ======================================== 全局变量 ============================================

# 引脚配置（请根据实际接线修改）
SCL_PIN = 22         # I2C 时钟引脚
SDA_PIN = 21         # I2C 数据引脚
I2C_FREQ = 400000    # I2C 频率（Hz）
RST_PIN = 25         # 复位引脚（可选，设为 None 禁用）
IRQ_PIN = 26         # 中断引脚（可选，设为 None 禁用）

# CST816 默认 I2C 地址（0x15，与 FT 系列 0x38 不同）
CST816_ADDR = 0x15

# 触摸屏分辨率
TOUCH_WIDTH = 240
TOUCH_HEIGHT = 240

# 打印间隔（ms）
PRINT_INTERVAL = 500

# 手势名称映射表
GESTURE_NAMES = {
    GESTURE_NONE: "none",
    GESTURE_UP: "up",
    GESTURE_DOWN: "down",
    GESTURE_LEFT: "left",
    GESTURE_RIGHT: "right",
    GESTURE_CLICK: "click",
    GESTURE_DOUBLE_CLICK: "double_click",
    GESTURE_LONG_PRESS: "long_press",
}

# I2C 设备扫描相关
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================

def gesture_name(gesture):
    """
    将手势常量转换为可读名称。

    Args:
        gesture (int): 手势常量值

    Returns:
        str: 手势名称
    ==========================================
    Convert gesture constant to readable name.

    Args:
        gesture (int): Gesture constant value

    Returns:
        str: Gesture name
    """
    return GESTURE_NAMES.get(gesture, "unknown(%d)" % gesture)

# ======================================== 自定义类 ============================================

# （本测试文件不需要自定义类）

# ======================================== 初始化配置 ==========================================

# 等待设备就绪
time.sleep(3)

print("FreakStudio: CST816/CST816S/CST816T/CST816D touch driver test")
print("")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: scl=%d, sda=%d, freq=%d" % (SCL_PIN, SDA_PIN, I2C_FREQ))

# I2C 设备扫描
# 注意：CST816 在屏幕未触摸时可能不响应 I2C，扫描列表中可能找不到设备
# 触摸屏幕后再运行扫描可提高发现几率
print("Scanning I2C bus...")
devices = i2c.scan()
if devices:
    print("I2C devices found: %s" % [hex(d) for d in devices])
else:
    print("No I2C devices found in scan")
    print("Note: CST816 may not respond to I2C when screen is untouched")
    print("Try touching the screen and re-run the scan")

# 检查目标地址
if CST816_ADDR in devices:
    print("CST816 found at address 0x%02X" % CST816_ADDR)
else:
    print("CST816 not found at expected address 0x%02X" % CST816_ADDR)
    print("This is expected if screen is untouched - CST816 may not appear in scan")

# 初始化复位引脚（若配置）
rst_pin = None
if RST_PIN is not None:
    rst_pin = Pin(RST_PIN, Pin.OUT, value=1)
    print("Reset pin configured: GPIO%d" % RST_PIN)

# 初始化中断引脚（若配置）
irq_pin = None
if IRQ_PIN is not None:
    irq_pin = Pin(IRQ_PIN, Pin.IN)
    print("Interrupt pin configured: GPIO%d" % IRQ_PIN)

# 创建 CST816 驱动实例
touch = CST816(
    i2c,
    address=CST816_ADDR,
    reset_pin=rst_pin,
    irq_pin=irq_pin,
    width=TOUCH_WIDTH,
    height=TOUCH_HEIGHT,
    debug=False,
)
print("CST816 driver initialized")
print("")

# 尝试读取芯片信息
# CST816 在未触摸时可能不响应 I2C，读取结果可能为 None
# 触摸屏幕后再读取可提高成功率
try:
    chip_id = touch.read_chip_id()
    if chip_id is not None:
        print("Chip ID: 0x%02X" % chip_id)
    else:
        print("Chip ID: read failed (screen may be untouched)")
except Exception as e:
    print("Chip ID read error: %s" % str(e))

try:
    revision = touch.read_revision()
    if revision is not None:
        print("Firmware revision: 0x%02X (%d)" % (revision, revision))
    else:
        print("Firmware revision: read failed (screen may be untouched)")
except Exception as e:
    print("Firmware revision read error: %s" % str(e))

print("")
print("Touch polling started. Touch the screen to see data.")
print("Press Ctrl+C to exit.")
print("")

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 读取触摸点数据
        point = touch.read_point()

        # 定时打印状态信息
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            if point is not None:
                # 有触摸数据，打印坐标和手势
                g_name = gesture_name(point["gesture"])
                print("Touch: x=%d, y=%d, gesture=%s, event=%d, count=%d" %
                      (point["x"], point["y"], g_name, point["event"],
                       touch.get_touch_count()))
            else:
                # 无触摸数据
                is_touched = touch.touched()
                print("Touch: idle, touched=%s, count=%d" %
                      (str(is_touched), touch.get_touch_count()))

            last_print_time = current_time

        # 短暂延时，降低 CPU 占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    touch.deinit()
    del touch
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | 默认地址为 0x15，与常见 FT 系列触摸芯片的 0x38 不同 |
| 未触摸时 I2C 不响应 | CST816 系列在屏幕未触摸时可能不响应 I2C。I2C 扫描可能找不到设备，芯片 ID 和固件版本读取可能返回 None。触摸屏幕后重试可提高成功率 |
| 中断模式 | 若使用中断引脚，需在构造时传入 Pin 实例。中断触发条件默认为下降沿 |
| 坐标精度 | X/Y 坐标精度取决于寄存器位宽（12 位），范围 0 ~ 4095 |
| 手势检测 | 支持单击、双击、长按和四方向滑动。单击抬手事件（event=1）时 read_point() 返回 None |
| 通信接口 | 仅支持 I2C 通信，不支持 SPI 模式 |
| 硬件验证 | 仅静态检查通过，未硬件验证 |
| 兼容性 | 代码兼容 MicroPython v1.23+，不依赖 CircuitPython 或 Adafruit 库 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | FreakStudio | 初始版本 |

## 联系方式

- GitHub: [FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
