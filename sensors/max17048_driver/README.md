# MAX17048 锂电池电量计 MicroPython 驱动

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

MAX17048/MAX17049 是一款高精度单节锂电池电量计芯片，采用 Maxim 的 ModelGauge 算法，无需外部检流电阻即可测量电池电压和荷电状态（SOC）。本驱动为其提供 MicroPython 的 I2C 接口封装，支持电池电压读取、SOC 百分比读取、报警阈值设置与检测、快速启动等功能。

适用于电池供电的物联网设备、便携式仪器仪表、可穿戴设备等需要电池电量监测的场景。

## 主要功能

- 读取电池电压（VCELL），分辨率 1.25mV
- 读取电池荷电状态（SOC），精度 1/256%
- 获取芯片版本号
- 获取/设置报警阈值（0%~32%）
- 报警状态检测与清除
- 设备复位与快速启动
- 依赖注入设计：I2C 总线由外部传入，灵活复用
- 支持 I2C 通信重试机制，提高可靠性
- 复用全局缓冲区，降低内存分配

## 硬件要求

### 推荐测试硬件

- 任意支持 MicroPython 的开发板（ESP32、RP2040 等）
- MAX17048/MAX17049 电量计模块
- 单节锂电池（3.7V LiPo）

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.5V~4.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| ALT  | 报警输出（开漏，可选） |
| QSTRT| 快速启动输入（可选） |

## 软件环境

- 固件版本：MicroPython v1.23.0+
- 驱动版本：v1.0.0
- 依赖库：无外部依赖（仅使用 machine、micropython、time 内置模块）

## 文件结构

```
├── max17048.py        # 核心驱动文件
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明

- **max17048.py**：MAX17048/MAX17049 电量计核心驱动，包含 I2C 通信、寄存器读写、电压/SOC 计算、报警管理等功能
- **main.py**：驱动测试程序，演示 I2C 总线扫描、设备初始化、电压和 SOC 实时读取

## 快速开始

### 1. 复制文件

将 `max17048.py` 和 `main.py` 复制到 MicroPython 设备的文件系统中。

### 2. 硬件接线

| MAX17048 | ESP32 |
|----------|-------|
| VCC      | 3.3V  |
| GND      | GND   |
| SCL      | GPIO22 |
| SDA      | GPIO21 |

### 3. 运行测试

将以下代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Andre Peeters
# @File    : main.py
# @Description : 测试 MAX17048 电量计驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from micropython import const
from machine import Pin, I2C
from max17048 import MAX17048

# ======================================== 全局变量 ============================================
# MAX17048 默认 I2C 地址
_MAX17048_ADDR = const(0x36)

# 数据打印间隔（ms）
print_interval = 2000
# 上次打印时间戳（ms）
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================
def do_reset():
    """复位设备（模式切换，默认注释调用，可 REPL 手动触发）"""
    device.reset()
    print("Device reset completed")

def do_quick_start():
    """快速启动设备（模式切换，默认注释调用，可 REPL 手动触发）"""
    device.quickStart()
    print("Quick start completed")

def do_clear_alert():
    """清除报警状态（模式切换，默认注释调用，可 REPL 手动触发）"""
    device.clearAlert()
    print("Alert cleared")

def do_set_threshold():
    """设置报警阈值为 20%（边界参数，默认注释调用，可 REPL 手动调用）"""
    device.setAlertThreshold(20)
    print("Alert threshold set to 20%%")

# ======================================== 自定义类 ============================================
# 无自定义类，全部逻辑在主程序中

# ======================================== 初始化配置 ==========================================
# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing MAX17048 LiPo fuel gauge driver...")

# 初始化 I2C 总线（ESP32 默认引脚：SCL=22, SDA=21）
# 若使用其他开发板，请修改引脚号
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# I2C 设备扫描，验证 MAX17048 在线
print("Scanning I2C bus...")
devices = i2c.scan()
# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 查找目标地址设备
if _MAX17048_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X" % _MAX17048_ADDR
    )
print("MAX17048 found at address 0x%02X" % _MAX17048_ADDR)

# 创建 MAX17048 驱动实例
device = MAX17048(i2c)

# 读取 VERSION 寄存器，确认设备可通信
version = device.getVersion()
print("MAX17048 version register: 0x%04X" % version)

# 初始化时打印设备完整状态
print("--- Device Status ---")
print(str(device))
print("---------------------")

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频读取：保留自动执行
            # 读取电池电压
            voltage = device.getVCell()
            # 读取电池荷电状态
            soc = device.getSoc()
            # 检查报警状态
            alert = device.inAlert()

            print("Voltage: %.3f V | SOC: %.2f %% | Alert: %s"
                  % (voltage, soc, alert))
            last_print_time = current_time

        # 以下为高频/模式切换/边界函数，默认注释执行，可 REPL 手动调用
        # 复位设备，REPL 手动触发
        # do_reset()
        # 快速启动，REPL 手动触发
        # do_quick_start()
        # 清除报警，REPL 手动触发
        # do_clear_alert()
        # 设置阈值 20%，REPL 手动调用
        # do_set_threshold()

        # 短延时降低 CPU 占用
        time.sleep_ms(100)

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

### 4. 最小代码示例

```python
from machine import Pin, I2C
from max17048 import MAX17048

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
device = MAX17048(i2c)

print("Voltage: %.3f V" % device.getVCell())
print("SOC: %.2f %%" % device.getSoc())
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作条件 | 供电电压 2.5V~4.5V，I2C 通信速率建议 100kHz~400kHz |
| 测量精度 | 电压精度 7.5mV，SOC 精度取决于 ModelGauge 算法和电池特性 |
| SOC 初始值 | 首次上电或更换电池后，SOC 需要一定时间稳定，建议使用 quickStart() 强制重新估算 |
| I2C 地址 | 默认地址 0x36（7-bit），与 MAX17043/MAX17044 兼容 |
| 报警阈值 | 阈值范围 0~32（%），32 表示禁用报警 |
| 芯片兼容 | 同时支持 MAX17048 和 MAX17049，引脚和寄存器完全兼容 |
| I2C 总线共享 | deinit() 会调用 I2C 的 deinit()，若总线被其他设备共享需注意 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Andre Peeters | 初始版本，基于 GraftSense 规范重写 |

## 联系方式

- 邮箱：freakstudio@example.com
- GitHub：[https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 Andre Peeters

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
