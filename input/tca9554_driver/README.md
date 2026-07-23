# TCA9554 8位 I2C GPIO 扩展器 MicroPython 驱动

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

TCA9554 是一款 8 位 I2C GPIO 扩展芯片，可通过 I2C 总线扩展 8 个通用 IO 引脚。本驱动基于 MicroPython I2C 接口实现，支持单引脚和端口级的输入/输出读写、方向配置以及极性反转功能。适用于 MCU IO 资源不足、需要扩展按键、LED、继电器等场景。

驱动逻辑参考 RobTillaart Arduino TCA9554 库实现。

## 主要功能

- 支持单引脚方向配置（输入/输出）和端口级批量方向配置
- 支持单引脚电平读写和端口级批量读写
- 支持输入极性反转（单引脚和端口级）
- 支持 I2C 连接状态探测（is_connected）
- I2C 总线实例由外部注入，不占用固定引脚，适配多种平台
- 完整的参数校验和异常处理（ValueError / RuntimeError）
- 支持调试日志开关（debug 参数）
- deinit() 安全释放资源，所有引脚恢复输入模式（高阻态）

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| TCA9554 / TCA9554A 模块 | 8位 I2C GPIO 扩展芯片 |
| MicroPython 开发板 | ESP32 / RP2040 / 其他支持 I2C 的平台 |
| 杜邦线 | 连接 I2C 和电源 |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（2.3V-5.5V） |
| GND | 电源负极 |
| SCL | I2C 时钟线（示例: GPIO22） |
| SDA | I2C 数据线（示例: GPIO21） |
| A0 | 地址选择位0（接 GND 或 VCC） |
| A1 | 地址选择位1（接 GND 或 VCC） |
| A2 | 地址选择位2（接 GND 或 VCC） |
| P0~P7 | 8 个通用 IO 引脚 |

### I2C 地址

地址由 A0/A1/A2 引脚电平决定，范围 0x20-0x27（默认 0x20，A0/A1/A2 全部接 GND）。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无第三方依赖（仅使用 machine.I2C） |

## 文件结构

```
├── code/
│   ├── tca9554.py       # 核心驱动文件
│   └── main.py          # 测试示例文件
├── package.json         # 包配置文件
└── README.md            # 说明文档
```

## 文件说明

- **code/tca9554.py**: TCA9554 核心驱动类，包含完整的寄存器操作 API 和 I2C 通信封装。由外部注入 I2C 实例，不创建硬件对象。
- **code/main.py**: 完整的硬件测试程序，包含 I2C 扫描、设备验证、输出/输入/极性反转演示和主循环周期性读取。

## 快速开始

### 步骤一：复制文件

将 `code/tca9554.py` 和 `code/main.py` 上传到 MicroPython 设备的 `/` 或 `/lib/` 目录。

### 步骤二：接线

参考引脚说明表格，连接 VCC、GND、SCL、SDA。如果使用默认 I2C 地址 0x20，将 A0/A1/A2 全部接 GND。

### 步骤三：运行测试

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 TCA9554 8位 I2C GPIO 扩展器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from tca9554 import TCA9554, TCA9554_INPUT, TCA9554_OUTPUT, TCA9554_HIGH, TCA9554_LOW

# ======================================== 全局变量 ============================================

# 请替换为你的实际引脚配置
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
TCA9554_ADDR = 0x20

# TCA9554 无标准芯片 ID 寄存器，使用地址扫描验证
TCA9554_EXPECTED_ADDR = TCA9554_ADDR

# 打印间隔（ms）
PRINT_INTERVAL = 2000

# 上次打印时间戳
last_print_time = 0

# ======================================== 功能函数 ============================================

def demo_output_mode(io_expander):
    """
    演示输出模式：配置引脚为输出，写入高低电平（低频，自动执行）
    """
    print("")
    print("=== Demo: Output Mode ===")
    # 配置引脚0为输出模式
    io_expander.pin_mode(0, TCA9554_OUTPUT)
    print("Pin 0 configured as OUTPUT")
    # 写入高电平
    io_expander.write(0, TCA9554_HIGH)
    # 读取输出寄存器验证写入值
    out_val = io_expander.read_output8()
    print("Output register after writing HIGH to pin 0: 0x%02X" % out_val)
    # 延时等待，便于观察
    time.sleep(0.5)
    # 写入低电平
    io_expander.write(0, TCA9554_LOW)
    out_val = io_expander.read_output8()
    print("Output register after writing LOW to pin 0: 0x%02X" % out_val)


def demo_input_mode(io_expander):
    """
    演示输入模式：配置引脚为输入，读取引脚电平（低频，自动执行）
    """
    print("")
    print("=== Demo: Input Mode ===")
    # 配置引脚0为输入模式
    io_expander.pin_mode(0, TCA9554_INPUT)
    print("Pin 0 configured as INPUT")
    # 读取全部8个引脚的输入寄存器
    in_val = io_expander.read_input8()
    print("Input register: 0x%02X" % in_val)
    # 读取单个引脚的电平
    pin_val = io_expander.read(0)
    print("Pin 0 level: %d" % pin_val)


def demo_polarity_mode(io_expander):
    """
    演示极性反转功能（模式切换，默认注释调用，可REPL手动触发）
    """
    print("")
    print("=== Demo: Polarity Inversion ===")
    # 反转引脚0的输入极性
    io_expander.set_polarity(0, True)
    print("Pin 0 polarity inverted")
    # 读取输入验证极性反转效果
    in_val = io_expander.read(0)
    print("Pin 0 level after polarity inversion: %d" % in_val)
    # 恢复正常极性
    io_expander.set_polarity(0, False)
    print("Pin 0 polarity restored to normal")


def demo_port_operations(io_expander):
    """
    演示端口级批量操作（批量操作，封装为独立函数供REPL调用）
    """
    print("")
    print("=== Demo: Port-Level Operations ===")
    # 配置所有8个引脚为输出（0x00 = 全部输出）
    io_expander.pin_mode8(0x00)
    print("All pins configured as OUTPUT (mask=0x00)")
    # 批量写入端口数据（0x55 = 01010101）
    io_expander.write_port(0x55)
    out_val = io_expander.read_output8()
    print("Output register after write_port(0x55): 0x%02X" % out_val)
    # 配置所有8个引脚为输入（0xFF = 全部输入）
    io_expander.pin_mode8(0xFF)
    print("All pins configured as INPUT (mask=0xFF)")
    # 读取全部输入状态
    in_val = io_expander.read_input8()
    print("Input register: 0x%02X" % in_val)


# ======================================== 初始化配置 ==========================================

# 上电延时，等待硬件稳定
time.sleep(3)

print("FreakStudio: Testing TCA9554 8-bit I2C GPIO Expander Driver")
print("")

# 初始化 I2C 总线
print("Initializing I2C bus...")
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C bus initialized: SCL=%d, SDA=%d, freq=%d" % (SCL_PIN, SDA_PIN, I2C_FREQ))

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

# 检查目标设备是否在扫描列表中
if TCA9554_EXPECTED_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % TCA9554_EXPECTED_ADDR)
print("Device found at expected address: 0x%02X" % TCA9554_EXPECTED_ADDR)

# 实例化 TCA9554 驱动（I2C 实例外部注入）
print("Initializing TCA9554 driver...")
io_expander = TCA9554(i2c, address=TCA9554_ADDR)

# 验证设备连接（I2C 探测读取）
if io_expander.is_connected():
    print("TCA9554 connected and responding")
else:
    raise RuntimeError("TCA9554 not responding at address 0x%02X" % TCA9554_ADDR)

# ========================================  主程序  ===========================================

try:
    # 低频自动执行：基础演示
    demo_output_mode(io_expander)
    demo_input_mode(io_expander)

    # 模式切换：注释自动调用，可REPL手动触发
    # demo_polarity_mode(io_expander)

    # 批量操作：封装为独立函数，可REPL调用
    # demo_port_operations(io_expander)

    print("")
    print("Basic demo completed. Use REPL to call additional functions:")
    print("  demo_polarity_mode(io_expander)")
    print("  demo_port_operations(io_expander)")
    print("")

    # 主循环：周期性读取输入寄存器
    last_print_time = time.ticks_ms()
    while True:
        current_time = time.ticks_ms()
        # 按间隔打印输入状态
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取全部8个引脚的输入状态
            in_val = io_expander.read_input8()
            print("Input register: 0x%02X" % in_val)
            last_print_time = current_time
        # 短延时避免 CPU 占用过高
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放资源，所有引脚恢复输入模式
    io_expander.deinit()
    del io_expander
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 方向寄存器语义 | **1 = 输入 (INPUT), 0 = 输出 (OUTPUT)**。与部分其他 IO 扩展器方向定义相反，使用时务必注意，严禁对调。 |
| 地址范围 | 0x20-0x27，由 A0/A1/A2 引脚电平决定。超出此范围将触发 ValueError。 |
| 输出驱动能力 | IO 引脚为推挽输出，单引脚最大驱动电流有限，驱动大负载需加三极管/MOSFET。 |
| 输入状态 | 配置为输出的引脚，其输入寄存器读回的是输出锁存值而非实际引脚电平。 |
| 初始化行为 | 默认 config=0xFF（全部输入），output=0x00。可在构造时自定义。 |
| 验证状态 | 仅静态检查通过，未硬件验证。 |
| I2C 总线注入 | 驱动不创建 I2C 实例，必须由外部传入。 |
| 兼容性 | 与 TCA9554A / PCA9554 / PCA9554A 兼容（同系列芯片）。 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | FreakStudio | 初始版本，基于 RobTillaart Arduino TCA9554 逻辑 |

## 联系方式

- Email: support@freakstudio.cn
- GitHub: https://github.com/FreakStudioCN

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
