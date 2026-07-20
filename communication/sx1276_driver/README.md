# SX1276 MicroPython 驱动

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

本驱动用于通过 SPI 接口控制 SX1276 LoRa 射频收发器芯片，实现数据包的发送与接收。SX1276 是 Semtech 公司推出的低功耗长距离扩频通信芯片，支持 137-1020MHz 频段范围，广泛应用于物联网、远程遥测和无线传感器网络等场景。驱动实现了基本的数据链路层通信协议，支持 REQ/ACK 请求应答模式和 BRD 广播模式，以及 FHSS 跳频扩频功能。

## 主要功能

- 通过 SPI 接口控制 SX1276 芯片（支持模式 0，最高 10MHz）
- 支持 REQ（请求应答）、ACK（确认应答）、BRD（广播）三种数据包类型
- 支持 FHSS 跳频扩频（列表长度为 1 时自动关闭跳频）
- 通过 DIO0 接收 TxDone/RxDone 中断，DIO1 接收 FhssChangeChannel 中断
- 支持 +20dBm 功率增强选项（PA_BOOST）
- 提供用户可重写的回调接口（req_packet_handler / brd_packet_handler / after_TxDone）
- 依赖注入设计，SPI 总线和引脚由外部创建并传入
- 自动计算 SNR 和 RSSI 信号质量指标

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCK  | SPI 时钟线（GPIO5） |
| MOSI | SPI 主出从入（GPIO18） |
| MISO | SPI 主入从出（GPIO19） |
| CS   | SPI 片选（GPIO22） |
| RST  | 复位引脚（GPIO23） |
| DIO0 | 中断引脚 0 - TxDone/RxDone（GPIO25） |
| DIO1 | 中断引脚 1 - FhssChangeChannel（GPIO26） |

推荐测试硬件：
- SX1276 LoRa 模块（如 Ra-02、RFM95W）
- ESP32 / RP2040 等支持 MicroPython 的 MCU
- 至少需要两个模块才能进行完整的收发测试

## 软件环境

- MicroPython 固件版本：v1.23 或更高
- 驱动版本：v1.0.0
- 依赖库：无（仅使用 MicroPython 内置模块 `machine`、`struct`、`micropython`）

## 文件结构

```
├── sx1276.py   # 核心驱动
├── main.py     # 测试示例
└── README.md   # 说明文档
```

## 文件说明

- **sx1276.py**：SX1276 核心驱动文件，包含 `SX1276` 类，实现 SPI 通信、寄存器读写、数据包收发和中断处理
- **main.py**：测试示例程序，支持发送模式（定时广播）和接收模式（持续监听），通过 `TEST_MODE` 变量切换
- **README.md**：项目说明文档

## 快速开始

**步骤 1：复制文件**

将 `sx1276.py` 和 `main.py` 复制到 MicroPython 设备的文件系统中。

**步骤 2：接线**

按照硬件要求表格连接 SX1276 模块与 MCU 的 SPI 和控制引脚。注意 SPI 引脚需与 MCU 的硬件 SPI 通道匹配。

**步骤 3：配置参数**

在 `main.py` 中根据实际接线修改引脚配置常量（`SCK_PIN`、`MOSI_PIN`、`MISO_PIN`、`CS_PIN`、`RST_PIN`、`DIO0_PIN`、`DIO1_PIN`）和跳频频率列表（`FHSS_LIST`）。

**步骤 4：运行测试**

在发送方设备上将 `TEST_MODE` 设为 1（发送模式），在接收方设备上将 `TEST_MODE` 设为 2（接收模式），分别运行即可。

**最小可运行代码示例**：

```python
from machine import Pin, SPI
from sx1276 import SX1276

# 创建 SPI 总线（mode 0, 10MHz）
spi = SPI(0, baudrate=10_000_000, polarity=0, phase=0,
          sck=Pin(5), mosi=Pin(18), miso=Pin(19))

# 创建控制引脚
cs_pin = Pin(22, Pin.OUT)
cs_pin.on()
rst_pin = Pin(23, Pin.OUT)
dio0_pin = Pin(25, Pin.IN)
dio1_pin = Pin(26, Pin.IN)

# 初始化驱动（868MHz 单频点，关闭 FHSS）
radio = SX1276(spi, cs_pin, rst_pin, dio0_pin, dio1_pin,
               src_id=1, fhss_list=[868_000_000])

# 设置为接收模式
radio.mode = "RXCONTINUOUS"

# 发送广播消息
radio.mode = "STANDBY"
radio.send(dst_id=0, pkt_type=radio.PKT_TYPE["BRD"], msg="Hello LoRa")
```

**完整测试代码**（与 `main.py` 一致）：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 SX1276 LoRa 射频收发器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SPI
from sx1276 import SX1276

# ======================================== 全局变量 ============================================

# ==================== SPI 引脚配置（根据实际接线修改） ====================
SPI_CHANNEL = 0
SCK_PIN  = 5
MOSI_PIN = 18
MISO_PIN = 19

# ==================== 控制和中断引脚配置（根据实际接线修改） ====================
CS_PIN   = 22
RST_PIN  = 23
DIO0_PIN = 25
DIO1_PIN = 26

# ==================== 设备配置常量 ====================
SRC_ID = 1
# 跳频频率列表（Hz），单元素关闭 FHSS 跳频
FHSS_LIST = [868_000_000]

# ==================== 测试模式配置 ====================
# 测试模式：1=发送模式 / 2=接收模式
TEST_MODE = 1

# 打印间隔
last_print_time = time.ticks_ms()
PRINT_INTERVAL_MS = 5000

# 发送消息计数
send_count = 0

# ======================================== 功能函数 ============================================

def print_device_status():
    """打印设备状态（低频查询，自动执行）"""
    mode = device.mode if device.mode else "INIT"
    avail = "yes" if device.is_available else "no"
    print("Mode: %s | Available: %s" % (mode, avail))

def broadcast_message():
    """发送广播消息（低频，默认自动执行）"""
    global send_count
    msg = "Hello LoRa #%d" % send_count
    print("Sending broadcast: %s" % msg)
    device.send(dst_id=0, pkt_type=device.PKT_TYPE["BRD"], msg=msg, timeout=5)
    send_count += 1

def send_req_message():
    """发送请求消息并等待 ACK（交互模式，默认注释，可 REPL 手动调用）"""
    msg = "REQ test message"
    print("Sending REQ: %s" % msg)
    device.send(dst_id=2, pkt_type=device.PKT_TYPE["REQ"], msg=msg, retry=3, timeout=5, debug=True)
    if device._pkt_id == 0:
        print("ACK received successfully")
    else:
        print("ACK not received (timeout)")

# ======================================== 自定义类 ============================================

class CustomRadioHandler:
    """自定义数据包处理器（继承自驱动回调方法）"""
    pass

# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing SX1276 LoRa radio driver...")

# 初始化 SPI 引脚
print("Initializing SPI pins...")
cs_pin = Pin(CS_PIN, Pin.OUT)
cs_pin.on()

rst_pin = Pin(RST_PIN, Pin.OUT)

# 初始化中断引脚
dio0_pin = Pin(DIO0_PIN, Pin.IN)
dio1_pin = Pin(DIO1_PIN, Pin.IN)

# 初始化 SPI 总线
# SX1276 支持 SPI mode 0（polarity=0, phase=0），最高 10MHz
print("Initializing SPI bus (baudrate=10MHz, mode 0)...")
spi = SPI(SPI_CHANNEL, baudrate=10_000_000, polarity=0, phase=0,
          sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))

# 初始化 SX1276 驱动实例
print("Initializing SX1276 driver...")
device = SX1276(spi, cs_pin, rst_pin, dio0_pin, dio1_pin,
                src_id=SRC_ID, fhss_list=FHSS_LIST, debug=True)

print("SX1276 initialized successfully.")

# 设置设备到接收模式（准备接收数据）
device.mode = "RXCONTINUOUS"
print("Device set to RXCONTINUOUS mode (listening)...")

# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间
        current_time = time.ticks_ms()

        if TEST_MODE == 1:
            # 发送模式：定时广播消息
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:

                # 发送方需要先切换到待机模式再发送
                device.mode = "STANDBY"
                time.sleep_ms(10)

                broadcast_message()

                # 发送完成后恢复到接收模式
                time.sleep_ms(100)
                device.mode = "RXCONTINUOUS"

                last_print_time = current_time

            # 交互式发送，默认注释，可 REPL 手动调用
            # send_req_message()

        elif TEST_MODE == 2:
            # 接收模式：定时打印状态
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                print_device_status()
                last_print_time = current_time

        # 主循环延时
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

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作条件 | 供电电压 3.3V（不可直接使用 5V），SPI 电平需与 MCU 兼容 |
| 频率限制 | 驱动默认配置为 868MHz ISM 频段，需根据当地法规和模块型号调整 FHSS_LIST |
| 通信距离 | 实际通信距离受天线、环境遮挡、扩频因子和带宽配置影响 |
| 半双工 | SX1276 为半双工芯片，不能同时收发 |
| 中断处理 | 驱动在 ISR 上下文中执行 SPI 通信，违反标准 ISR 安全规范；实际使用中应使用 micropython.schedule() 将处理延迟到主循环 |
| 功率限制 | 2dBm 默认输出功率，可通过 PA_BOOST 提升至 +20dBm（需遵守当地法规） |
| SPI 时钟 | 最高支持 10MHz SPI 时钟，mode 0（CPOL=0, CPHA=0） |
| 双设备需求 | 完整收发测试需要至少两个 SX1276 模块 |
| FHSS | 跳频频率列表长度由用户定义，单元素列表自动关闭跳频功能 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | FreakStudio | 初始版本，规范化改写 |

## 联系方式

- GitHub: [https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
