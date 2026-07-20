# BMI270 MicroPython 驱动

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
BMI270 是 Bosch 公司推出的超低功耗 6 轴惯性测量单元 (IMU)，集成 3 轴加速度计和 3 轴陀螺仪。本驱动提供 I2C 接口下对 BMI270 的完整支持，包括传感器初始化、配置加载、数据读取和量程切换。

## 主要功能
- 三轴加速度数据读取 (m/s^2)
- 三轴陀螺仪角速度数据读取 (dps)
- 加速度量程可调: +/-2G, +/-4G, +/-8G, +/-16G
- 陀螺仪量程可调: +/-125, +/-250, +/-500, +/-1000, +/-2000 dps
- 加速度计使能/禁用控制
- 错误代码诊断
- 软件复位功能
- 调试日志开关

## 硬件要求
| 推荐测试硬件 | 说明 |
|-------------|------|
| ESP32 开发板 | 主控 MCU |
| BMI270 模块 | 6 轴 IMU 传感器 |
| 杜邦线若干 | I2C 接线 |

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极 (3.3V) |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

## 软件环境
| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| 依赖模块 | i2c_helpers.py (I2C 辅助类), config_file.py (配置文件) |

## 文件结构
```
├── bmi270.py          # 核心驱动
├── i2c_helpers.py     # I2C 通信辅助类 (CBits, RegisterStruct)
├── config_file.py     # 传感器初始化配置文件
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明
| 文件 | 说明 |
|------|------|
| `bmi270.py` | BMI270 核心驱动类，提供加速度/陀螺仪数据读取、量程设置、初始化等功能 |
| `i2c_helpers.py` | I2C 通信辅助类，提供 CBits（位段操作）和 RegisterStruct（寄存器结构体）描述符，基于 Adafruit Register 库 |
| `config_file.py` | BMI270 上电初始化所需的 8192 字节配置数据，由 Bosch 官方配置工具生成 |
| `main.py` | 测试示例程序，演示 I2C 设备扫描、传感器初始化、数据读取循环 |

## 快速开始

1. 将 `bmi270.py`、`i2c_helpers.py`、`config_file.py` 复制到 MicroPython 设备的 `/lib/` 目录或项目根目录
2. 按接线表连接 BMI270 到 MCU
3. 将 `main.py` 复制到设备并运行

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 BMI270 六轴IMU驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
from bmi270 import BMI270

# ======================================== 全局变量 ============================================
# BMI270 默认 I2C 地址
BMI270_I2C_ADDR = 0x68
# BMI270 WHO_AM_I 期望值
BMI270_CHIP_ID = 0x24
# BMI270 WHO_AM_I 寄存器地址
BMI270_WHO_AM_I_REG = 0x00
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================
def print_error_codes():
    """
    打印错误代码（调试功能，默认注释调用，可 REPL 手动调用）
    Print error codes (debug function, commented by default, can be called from REPL).
    """
    bmi270.error_code()


def switch_gyro_range():
    """
    切换陀螺仪量程到 ±1000 dps（模式切换，默认注释调用，可 REPL 手动触发）
    Switch gyro range to +/-1000 dps (mode switch, commented by default, can be triggered from REPL).
    """
    bmi270.gyro_range = bmi270.GYRO_RANGE_1000
    print("Gyro range switched to GYRO_RANGE_1000")


def switch_accel_range():
    """
    切换加速度量程到 ±8g（模式切换，默认注释调用，可 REPL 手动触发）
    Switch acceleration range to +/-8g (mode switch, commented by default, can be triggered from REPL).
    """
    bmi270.acceleration_range = bmi270.ACCEL_RANGE_8G
    print("Accel range switched to ACCEL_RANGE_8G")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 bmi270.BMI270

# ======================================== 初始化配置 ==========================================
# 等待硬件就绪
time.sleep(3)
print("FreakStudio: Testing BMI270 6-axis IMU driver")

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
if BMI270_I2C_ADDR not in devices:
    raise RuntimeError(
        "BMI270 not found at expected address 0x%02X" % BMI270_I2C_ADDR
    )
print("BMI270 found at 0x%02X" % BMI270_I2C_ADDR)

# 读取并验证 WHO_AM_I 芯片 ID
chip_id = i2c.readfrom_mem(BMI270_I2C_ADDR, BMI270_WHO_AM_I_REG, 1)[0]
if chip_id != BMI270_CHIP_ID:
    raise RuntimeError(
        "Unexpected BMI270 chip ID: expected 0x%02X, got 0x%02X"
        % (BMI270_CHIP_ID, chip_id)
    )
print("BMI270 chip ID verified: 0x%02X" % chip_id)

# 创建 BMI270 传感器实例
bmi270 = BMI270(i2c, address=BMI270_I2C_ADDR, debug=False)
print("BMI270 initialized successfully")

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取加速度值（低频核心 API，保留自动执行）
            acc_x, acc_y, acc_z = bmi270.acceleration
            print(
                "Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z)
            )

            # 读取陀螺仪值（低频核心 API，保留自动执行）
            gyro_x, gyro_y, gyro_z = bmi270.gyro
            print(
                "Gyro (dps): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z)
            )

            # 打印当前量程设置（低频状态查询，保留自动执行）
            print(
                "Range: accel=%s, gyro=%s"
                % (bmi270.acceleration_range, bmi270.gyro_range)
            )
            print(
                "Accel mode: %s" % bmi270.acceleration_operation_mode
            )
            print("---")
            last_print_time = current_time

        # 调试功能，注释默认执行，可 REPL 手动调用
        # print_error_codes()
        # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_gyro_range()
        # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_accel_range()
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    bmi270.deinit()
    del bmi270
    print("Program exited")
```

## 注意事项
| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V（部分模块支持 1.8V-3.6V） |
| 通信接口 | I2C（默认地址 0x68） |
| 配置文件 | 首次上电必须加载 config_file.py 中的数据，否则传感器无法正常工作 |
| 初始化时间 | 加载配置文件约需 8 秒，请耐心等待 |
| 加速度量程 | 默认 +/-2G，最大 +/-16G |
| 陀螺仪量程 | 默认 +/-250 dps，最大 +/-2000 dps |

## 版本记录
| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Jose D. Montoya | 初始规范化版本 |

## 联系方式
- GitHub: [https://github.com/jposada202020/MicroPython_BMI270](https://github.com/jposada202020/MicroPython_BMI270)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
