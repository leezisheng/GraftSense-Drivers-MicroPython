# LSM6DSOX MicroPython 驱动

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
LSM6DSOX 是 ST 公司推出的高性能 6 轴惯性测量单元 (IMU)，集成 3 轴加速度计和 3 轴陀螺仪，并内置温度传感器。本驱动提供 I2C 接口下对 LSM6DSOX 的完整支持，包括传感器初始化、数据读取、量程切换、速率配置和高通滤波器设置。

## 主要功能
- 三轴加速度数据读取 (m/s^2)
- 三轴陀螺仪角速度数据读取 (rad/s)
- 内置温度传感器数据读取 (摄氏度)
- 加速度量程可调: +/-2G, +/-4G, +/-8G, +/-16G
- 陀螺仪量程可调: +/-250, +/-500, +/-1000, +/-2000 dps
- 加速度数据速率可调: 1.6 Hz ~ 6.66 kHz
- 陀螺仪数据速率可调: 1.6 Hz ~ 6.66 kHz
- 高通滤波器模式可选 (8 种模式)
- 传感器软件复位
- 块数据更新保护 (BDU)

## 硬件要求
| 推荐测试硬件 | 说明 |
|-------------|------|
| ESP32 开发板 | 主控 MCU |
| LSM6DSOX 模块 | 6 轴 IMU 传感器 |
| 杜邦线若干 | I2C 接线 |

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极 (1.71V-3.6V) |
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
├── lsm6dsox.py        # 核心驱动
├── i2c_helpers.py     # I2C 通信辅助类 (CBits, RegisterStruct)
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明
| 文件 | 说明 |
|------|------|
| `lsm6dsox.py` | LSM6DSOX 核心驱动类，提供加速度/陀螺仪/温度数据读取、量程设置、速率配置、高通滤波器等功能 |
| `i2c_helpers.py` | I2C 通信辅助类，提供 CBits（位段操作）和 RegisterStruct（寄存器结构体）描述符，基于 Adafruit Register 库 |
| `main.py` | 测试示例程序，演示 I2C 设备扫描、传感器初始化、多维度数据读取循环 |

## 快速开始

1. 将 `lsm6dsox.py`、`i2c_helpers.py` 复制到 MicroPython 设备的 `/lib/` 目录或项目根目录
2. 按接线表连接 LSM6DSOX 到 MCU
3. 将 `main.py` 复制到设备并运行

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 LSM6DSOX 六轴IMU驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
from lsm6dsox import LSM6DSOX

# ======================================== 全局变量 ============================================
# LSM6DSOX 默认 I2C 地址
LSM6DSOX_I2C_ADDR = 0x6A
# LSM6DSOX WHO_AM_I 期望值
LSM6DSOX_CHIP_ID = 0x6C
# LSM6DSOX WHO_AM_I 寄存器地址
LSM6DSOX_WHO_AM_I_REG = 0x0F
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================
def switch_gyro_range():
    """
    切换陀螺仪量程到 ±2000 dps（模式切换，默认注释调用，可 REPL 手动触发）
    Switch gyro range to +/-2000 dps (mode switch, commented by default, can be triggered from REPL).
    """
    lsm.gyro_range = lsm.RANGE_2000_DPS
    print("Gyro range switched to RANGE_2000_DPS")


def switch_accel_range():
    """
    切换加速度量程到 ±16g（模式切换，默认注释调用，可 REPL 手动触发）
    Switch acceleration range to +/-16g (mode switch, commented by default, can be triggered from REPL).
    """
    lsm.acceleration_range = lsm.RANGE_16G
    print("Accel range switched to RANGE_16G")


def switch_hpf():
    """
    切换高通滤波器模式（模式切换，默认注释调用，可 REPL 手动触发）
    Switch high-pass filter mode (mode switch, commented by default, can be triggered from REPL).
    """
    lsm.high_pass_filter = lsm.HPF_DIV100
    print("High-pass filter switched to HPF_DIV100")


def print_high_rate_data():
    """
    打印高频实时数据（高频，默认注释调用，可 REPL 手动调用）
    Print high-rate realtime data (high frequency, commented by default, can be called from REPL).
    """
    acc_x, acc_y, acc_z = lsm.acceleration
    print("Accel: x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))
    temp = lsm.temperature
    print("Temp: %.2f C" % temp)


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 lsm6dsox.LSM6DSOX

# ======================================== 初始化配置 ==========================================
# 等待硬件就绪
time.sleep(3)
print("FreakStudio: Testing LSM6DSOX 6-axis IMU driver")

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
if LSM6DSOX_I2C_ADDR not in devices:
    raise RuntimeError(
        "LSM6DSOX not found at expected address 0x%02X" % LSM6DSOX_I2C_ADDR
    )
print("LSM6DSOX found at 0x%02X" % LSM6DSOX_I2C_ADDR)

# 读取并验证 WHO_AM_I 芯片 ID
chip_id = i2c.readfrom_mem(LSM6DSOX_I2C_ADDR, LSM6DSOX_WHO_AM_I_REG, 1)[0]
if chip_id != LSM6DSOX_CHIP_ID:
    raise RuntimeError(
        "Unexpected LSM6DSOX chip ID: expected 0x%02X, got 0x%02X"
        % (LSM6DSOX_CHIP_ID, chip_id)
    )
print("LSM6DSOX chip ID verified: 0x%02X" % chip_id)

# 创建 LSM6DSOX 传感器实例
lsm = LSM6DSOX(i2c, address=LSM6DSOX_I2C_ADDR, debug=False)
print("LSM6DSOX initialized successfully")

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取加速度值（低频核心 API，保留自动执行）
            acc_x, acc_y, acc_z = lsm.acceleration
            print(
                "Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z)
            )

            # 读取陀螺仪值（低频核心 API，保留自动执行）
            gyro_x, gyro_y, gyro_z = lsm.gyro
            print(
                "Gyro (rad/s): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z)
            )

            # 读取温度值（低频核心 API，保留自动执行）
            temp = lsm.temperature
            print("Temperature: %.2f C" % temp)

            # 打印当前配置状态（低频状态查询，保留自动执行）
            print(
                "Range: accel=%s, gyro=%s"
                % (lsm.acceleration_range, lsm.gyro_range)
            )
            print(
                "Data rate: accel=%s, gyro=%s"
                % (lsm.acceleration_data_rate, lsm.gyro_data_rate)
            )
            print("HPF: %s" % lsm.high_pass_filter)
            print("---")
            last_print_time = current_time

        # print_high_rate_data()   # 高频函数，注释默认执行，可 REPL 手动调用
        # switch_gyro_range()      # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_accel_range()     # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_hpf()             # 模式切换，注释默认执行，可 REPL 手动触发
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    lsm.deinit()
    del lsm
    print("Program exited")
```

## 注意事项
| 类别 | 说明 |
|------|------|
| 工作电压 | 1.71V - 3.6V |
| 通信接口 | I2C（默认地址 0x6A） |
| 加速度量程 | 默认 +/-4G，最大 +/-16G |
| 陀螺仪量程 | 默认 +/-250 dps，最大 +/-2000 dps |
| BDU 模式 | 初始化时默认启用，防止读取数据不一致 |
| 数据速率 | 默认 104 Hz，最高 6.66 kHz |
| 高通滤波器 | 默认 SLOPE 模式，仅影响加速度计数据 |

## 版本记录
| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Jose D. Montoya | 初始规范化版本 |

## 联系方式
- GitHub: [https://github.com/jposada202020/MicroPython_LSM6DSOX](https://github.com/jposada202020/MicroPython_LSM6DSOX)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
