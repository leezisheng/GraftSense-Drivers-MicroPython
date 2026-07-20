# HTS221 MicroPython 驱动

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
HTS221 是 ST 公司推出的电容式数字温湿度传感器，集成温度和相对湿度传感元件。本驱动提供 I2C 接口下对 HTS221 的完整支持，包括传感器初始化、校准数据加载、温湿度数据读取和测量模式切换。

## 主要功能
- 温度数据读取 (摄氏度)
- 相对湿度数据读取 (%rH)
- 数据速率可调: 单次测量, 1 Hz, 7 Hz, 12.5 Hz
- 单次测量触发模式 (ONE_SHOT)
- 块数据更新保护 (BDU)，防止数据撕裂
- 内置出厂校准数据自动加载
- 传感器使能/禁用控制

## 硬件要求
| 推荐测试硬件 | 说明 |
|-------------|------|
| ESP32 开发板 | 主控 MCU |
| HTS221 模块 | 温湿度传感器 |
| 杜邦线若干 | I2C 接线 |

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极 (1.7V-3.6V) |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

## 软件环境
| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| 依赖模块 | i2c_helpers.py (I2C 辅助类) |

## 文件结构
```
├── hts221.py          # 核心驱动
├── i2c_helpers.py     # I2C 通信辅助类 (CBits, RegisterStruct)
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明
| 文件 | 说明 |
|------|------|
| `hts221.py` | HTS221 核心驱动类，提供温湿度数据读取、数据速率设置、单次测量等功能 |
| `i2c_helpers.py` | I2C 通信辅助类，提供 CBits（位段操作）和 RegisterStruct（寄存器结构体）描述符，基于 Adafruit Register 库 |
| `main.py` | 测试示例程序，演示 I2C 设备扫描、传感器初始化、温湿度数据读取循环 |

## 快速开始

1. 将 `hts221.py`、`i2c_helpers.py` 复制到 MicroPython 设备的 `/lib/` 目录或项目根目录
2. 按接线表连接 HTS221 到 MCU
3. 将 `main.py` 复制到设备并运行

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 HTS221 温湿度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
from hts221 import HTS221

# ======================================== 全局变量 ============================================
# HTS221 默认 I2C 地址
HTS221_I2C_ADDR = 0x5F
# HTS221 WHO_AM_I 期望值
HTS221_CHIP_ID = 0xBC
# HTS221 WHO_AM_I 寄存器地址
HTS221_WHO_AM_I_REG = 0x0F
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================
def switch_data_rate():
    """
    切换数据速率到 1 Hz（模式切换，默认注释调用，可 REPL 手动触发）
    Switch data rate to 1 Hz (mode switch, commented by default, can be triggered from REPL).
    """
    hts.data_rate = hts.RATE_1_HZ
    print("Data rate switched to RATE_1_HZ")


def single_measurement():
    """
    单次手动测量（仅在 ONE_SHOT 模式下有效，默认注释调用，可 REPL 手动调用）
    Single manual measurement (only valid in ONE_SHOT mode, commented by default, can be called from REPL).
    """
    hts.take_measurements()
    print("Single measurement triggered")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 hts221.HTS221

# ======================================== 初始化配置 ==========================================
# 等待硬件就绪
time.sleep(3)
print("FreakStudio: Testing HTS221 temperature and humidity sensor driver")

# 初始化 I2C 总线
# ESP32 示例引脚: scl=Pin(22), sda=Pin(21)
# Raspberry Pi Pico 示例引脚: scl=Pin(5), sda=Pin(4)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 验证目标设备是否存在
if HTS221_I2C_ADDR not in devices:
    raise RuntimeError(
        "HTS221 not found at expected address 0x%02X" % HTS221_I2C_ADDR
    )
print("HTS221 found at 0x%02X" % HTS221_I2C_ADDR)

# 读取并验证 WHO_AM_I 芯片 ID
chip_id = i2c.readfrom_mem(HTS221_I2C_ADDR, HTS221_WHO_AM_I_REG, 1)[0]
if chip_id != HTS221_CHIP_ID:
    raise RuntimeError(
        "Unexpected HTS221 chip ID: expected 0x%02X, got 0x%02X"
        % (HTS221_CHIP_ID, chip_id)
    )
print("HTS221 chip ID verified: 0x%02X" % chip_id)

# 创建 HTS221 传感器实例
hts = HTS221(i2c, address=HTS221_I2C_ADDR, debug=False)
print("HTS221 initialized successfully")

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取温度值（低频核心 API，保留自动执行）
            temp = hts.temperature
            print("Temperature: %.2f C" % temp)

            # 读取湿度值（低频核心 API，保留自动执行）
            hum = hts.relative_humidity
            print("Humidity: %.2f %%rH" % hum)

            # 打印当前配置状态（低频状态查询，保留自动执行）
            print(
                "Data rate: %s, BDU: %s"
                % (hts.data_rate, hts.block_data_update)
            )
            print("---")
            last_print_time = current_time

        # switch_data_rate()      # 模式切换，注释默认执行，可 REPL 手动触发
        # single_measurement()    # 单次测量，注释默认执行，可 REPL 手动调用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    hts.deinit()
    del hts
    print("Program exited")
```

## 注意事项
| 类别 | 说明 |
|------|------|
| 工作电压 | 1.7V - 3.6V |
| 通信接口 | I2C（默认地址 0x5F） |
| 温度范围 | -40℃ 至 +120℃ |
| 湿度范围 | 0% 至 100% rH |
| 校准数据 | 初始化时自动从传感器内置 NVM 加载，无需手动配置 |
| BDU 模式 | 推荐启用 BDU_ENABLED 以防止读取时数据不一致 |
| 最大速率 | 12.5 Hz ODR |

## 版本记录
| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Jose D. Montoya | 初始规范化版本 |

## 联系方式
- GitHub: [https://github.com/jposada202020/MicroPython_HTS221](https://github.com/jposada202020/MicroPython_HTS221)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
