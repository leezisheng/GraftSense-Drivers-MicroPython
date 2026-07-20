# IP5306 MicroPython 驱动

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

本驱动用于通过 I2C 接口读取 IP5306 多功能电源管理 SOC 的电池电量信息。IP5306 集成了升压转换器、充电管理、电量指示和按键控制等功能，广泛应用于移动电源和便携设备中。本驱动仅实现电池电量百分比读取功能，以 25% 步进精度返回结果。

## 主要功能

- 通过 I2C 接口读取电池电量百分比（0%/25%/50%/75%/100%）
- 支持外部 I2C 实例注入，可与其他 I2C 设备共享总线
- 提供上下文管理器（`with` 语句）支持，自动释放资源
- 轻量级实现，适合资源受限的 MicroPython 环境

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V-5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（GPIO5） |
| SDA  | I2C 数据线（GPIO4） |

推荐测试硬件：
- 任意搭载 IP5306 芯片的电路板（如 M5Stack 系列）
- ESP32 / ESP8266 / RP2040 等支持 MicroPython 的 MCU

## 软件环境

- MicroPython 固件版本：v1.23 或更高
- 驱动版本：v0.1.0
- 依赖库：无（仅使用 MicroPython 内置模块 `machine`、`ustruct`）

## 文件结构

```
├── ip5306.py   # 核心驱动
├── main.py     # 测试示例
└── README.md   # 说明文档
```

## 文件说明

- **ip5306.py**：IP5306 核心驱动文件，包含 `IP5306` 类，实现 I2C 通信和电池电量读取功能
- **main.py**：测试示例程序，演示 I2C 总线扫描、设备验证和周期性电量读取
- **README.md**：项目说明文档

## 快速开始

**步骤 1：复制文件**

将 `ip5306.py` 和 `main.py` 复制到 MicroPython 设备的文件系统中。

**步骤 2：接线**

按照硬件要求表格连接 IP5306 芯片与 MCU 的 I2C 引脚。

**步骤 3：运行测试**

```python
import time
from machine import I2C, Pin
from ip5306 import IP5306

# 延时等待上电稳定
time.sleep(3)

# 创建 I2C 实例
i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# 初始化驱动
device = IP5306(i2c)

# 读取电池电量
print("Battery level: %d%%" % device.level)

# 释放资源
device.deinit()
```

**完整测试代码**（与 `main.py` 一致）：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Mika Tuupola
# @File    : main.py
# @Description : 测试 IP5306 电源管理驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from ip5306 import IP5306

# ======================================== 全局变量 ============================================

# I2C 总线引脚配置（根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4

# 设备 I2C 地址
IP5306_I2C_ADDR = 0x75

# 打印间隔常量
last_print_time = time.ticks_ms()
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing IP5306 battery level driver...")

# 初始化 I2C 总线实例
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))

# I2C 总线扫描验证
print("Scanning I2C bus...")
devices = i2c.scan()
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")
print("Found I2C devices at: %s" % str([hex(d) for d in devices]))

# 验证目标设备地址
if IP5306_I2C_ADDR not in devices:
    raise RuntimeError("IP5306 not found at expected address 0x%02X" % IP5306_I2C_ADDR)
print("IP5306 device found at address 0x%02X" % IP5306_I2C_ADDR)

# 初始化驱动实例
device = IP5306(i2c, address=IP5306_I2C_ADDR)

# 读取电量状态寄存器，确认设备可通信
initial_level = device.level
print("IP5306 initial battery level: %d%%" % initial_level)

# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间
        current_time = time.ticks_ms()

        # 按周期打印电池电量
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            # 读取电池电量百分比
            battery_level = device.level
            print("Battery level: %d%%" % battery_level)
            last_print_time = current_time

        # 主循环延时
        time.sleep_ms(500)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    device.deinit()
    del device
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作条件 | 供电电压 3.3V-5V，I2C 通信电平需与 MCU 兼容 |
| 精度限制 | 电池电量以 25% 为步进精度（0/25/50/75/100），不支持精确到 1% 的读数 |
| 使用限制 | 仅实现电量读取功能，不支持充电控制、按键检测等其他 IP5306 高级特性 |
| 兼容性 | 支持 ESP32 / ESP8266 / RP2040 等常见 MicroPython 平台 |
| I2C 地址 | 默认 I2C 地址为 0x75，部分硬件可能使用其他地址 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-07-19 | Mika Tuupola | 初始版本，规范化改写 |

## 联系方式

- GitHub: [https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2019 Mika Tuupola

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
