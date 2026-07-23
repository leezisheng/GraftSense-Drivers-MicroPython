# CC1101 MicroPython 驱动

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

本驱动用于通过 SPI 接口控制 TI CC1101 sub-GHz 无线收发器芯片，实现寄存器配置、状态查询和数据包的发送与接收。CC1101 是 Texas Instruments 推出的低功耗 sub-1GHz 射频收发器，支持 315/433/868/915MHz ISM 频段，广泛应用于物联网、无线传感器网络和远程遥控等场景。

驱动基于 CC1101 数据手册命令模型，参考了 eydam-prototyping/cc1101 的寄存器/API 结构。源项目使用 GPL-3.0 许可，本驱动保持相同许可。

## 主要功能

- 通过 SPI 接口控制 CC1101 芯片（mode 0，最高 10MHz）
- 完整的配置寄存器读写 API（单寄存器 + 批量读写）
- 命令选通和状态寄存器查询
- 芯片身份验证（部件号 + 版本号）
- 载波频率配置（FREQ2/FREQ1/FREQ0 寄存器）
- 功率放大器功率表（PATABLE）配置
- 可变长度和固定长度数据包发送/接收
- 带超时保护的状态机等待机制
- RX/TX FIFO 溢出/下溢自动检测与恢复
- RSSI 信号强度计算（原始值 + dBm）
- 电源管理（空闲/接收/发送/掉电模式）
- 依赖注入设计，SPI 总线和引脚由外部创建并传入
- 预分配 I/O 缓冲区，避免热路径重复内存分配

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V，注意部分模块电压范围 1.8-3.6V） |
| GND  | 电源负极 |
| SCK  | SPI 时钟线（GPIO18） |
| MOSI | SPI 主出从入（GPIO23） |
| MISO | SPI 主入从出（GPIO19） |
| CSN  | SPI 片选（GPIO5） |
| GDO0 | 通用数字输出 0（GPIO4，可选） |
| GDO2 | 通用数字输出 2（可选，未在示例中使用） |

推荐测试硬件：
- CC1101 无线模块（如 E07-M1101D、CC1101-PA-LNA）
- ESP32 / RP2040 等支持 MicroPython 的 MCU
- 需根据模块规格和当地法规配置天线和射频参数

## 软件环境

- MicroPython 固件版本：v1.23 或更高
- 驱动版本：v1.0.0
- 依赖库：无（仅使用 MicroPython 内置模块 `machine`、`time`、`micropython`）

## 文件结构

```
├── code/
│   ├── cc1101.py   # 核心驱动
│   └── main.py     # 测试示例
├── package.json    # 包配置
├── LICENSE         # GPL-3.0 许可协议
└── README.md       # 说明文档
```

## 文件说明

- **cc1101.py**：CC1101 核心驱动文件，包含 `CC1101` 类，实现 SPI 通信、寄存器读写、芯片配置、数据包收发和电源管理
- **main.py**：测试示例程序，演示芯片初始化、身份验证和频率配置
- **package.json**：upypi 包管理器配置文件
- **LICENSE**：GPL-3.0 许可协议全文

## 快速开始

**步骤 1：复制文件**

将 `cc1101.py` 和 `main.py` 复制到 MicroPython 设备的文件系统中。

**步骤 2：接线**

按照硬件要求表格连接 CC1101 模块与 MCU 的 SPI 和控制引脚。注意：
- 供电电压必须与模块规格匹配（通常为 3.3V）
- SPI 引脚需与 MCU 的硬件 SPI 通道匹配

**步骤 3：配置参数**

在 `main.py` 中根据实际接线修改引脚配置常量（`SCK_PIN`、`MOSI_PIN`、`MISO_PIN`、`CS_PIN`、`GDO0_PIN`）和测试频率（`TEST_FREQ_HZ`）。

**步骤 4：运行测试**

运行 `main.py`，确认芯片身份验证通过（part=0x00, version 非 0x00/0xFF）。

**代码示例**：

```python
from machine import Pin, SPI
from cc1101 import CC1101

# 创建 SPI 总线（mode 0）
spi = SPI(
    1,
    baudrate=4000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(23),
    miso=Pin(19),
)

# 创建控制引脚
cs_pin = Pin(5, Pin.OUT)
cs_pin.value(1)
gdo0_pin = Pin(4, Pin.IN)

# 初始化驱动
radio = CC1101(spi, cs_pin, gdo0=gdo0_pin)

# 验证芯片身份
part, version = radio.verify()
print("part=0x%02X version=0x%02X" % (part, version))

# 配置频率（433.92 MHz）
radio.set_frequency(433920000)

# 发送数据包
radio.send_packet(b"Hello CC1101")

# 读取数据包
data = radio.read_packet(timeout_ms=5000)
if data:
    print("Received:", data)

# 释放资源
radio.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作条件 | 供电电压需与模块规格匹配（通常 1.8-3.6V），SPI 电平需与 MCU 兼容 |
| 频率限制 | 发送前必须根据当地无线电法规和模块型号配置正确的频率和发射功率 |
| 调制配置 | 驱动仅提供基础 API；实际通信需根据应用需求配置调制解调器寄存器（MDMCFG0-4、DEVIATN 等） |
| 天线连接 | 必须在模块天线端口连接匹配的天线或 50 欧姆负载，否则可能损坏发射电路 |
| 半双工 | CC1101 为半双工芯片，不能同时收发 |
| SPI 时钟 | 最高支持 10MHz SPI 时钟，mode 0（CPOL=0, CPHA=0） |
| 硬件验证 | 本仓库未记录硬件验证结果 |
| 许可协议 | 本驱动基于 GPL-3.0 许可，使用前请确认符合项目许可要求 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | FreakStudio | 初始版本，规范化改写 |

## 联系方式

- GitHub: [https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

GNU General Public License v3.0 (GPL-3.0)

Copyright (C) 2026 FreakStudio

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
