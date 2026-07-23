# SI4732 MicroPython 驱动

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

本驱动用于通过 I2C 接口控制 SI4732 AM/FM/SW/LW 收音机接收器芯片，实现电源管理、属性配置、固件版本查询和基本 AM/FM 调谐功能。SI4732 是 Silicon Labs 推出的全波段数字收音机接收器，支持 FM（64-108MHz）、AM（520-1710kHz）、SW（2.3-26.1MHz）和 LW（153-279kHz）频段。

**状态：本驱动为冷生成草案，尚未经过硬件验证。** RDS、Seek、SSB 和 NBFM 功能不在此版本中声明支持。

## 主要功能

- 通过 I2C 接口控制 SI4732 芯片（默认地址 0x63）
- 电源管理（上电/掉电），支持模拟和数字音频输出
- 固件版本和部件号查询
- 属性读写（PROPERTY 命令模型）
- 中断状态查询
- FM 和 AM 频段调谐（支持快速调谐和冻结模式）
- 调谐状态读取（有效标志、频率、RSSI、SNR、频率偏移）
- CTS 状态轮询与超时保护
- I2C 通信失败自动重试机制
- 自检流程（I2C 扫描 + 上电 + 版本 + 掉电）
- 依赖注入设计，I2C 总线和引脚由外部创建并传入
- 预分配 I/O 缓冲区

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（GPIO22） |
| SDA  | I2C 数据线（GPIO21） |
| RST  | 复位引脚（GPIO4，可选） |
| SEN  | I2C 地址选择（拉高=0x63，拉低=0x11） |

推荐测试硬件：
- SI4732 收音机模块（如 SI4732-D60）
- ESP32 / RP2040 等支持 MicroPython 的 MCU
- FM/AM 天线（模块通常集成或需外接）

## 软件环境

- MicroPython 固件版本：v1.23 或更高
- 驱动版本：v1.0.0
- 依赖库：无（仅使用 MicroPython 内置模块 `machine`、`time`、`micropython`）

## 文件结构

```
├── code/
│   ├── si4732.py   # 核心驱动
│   └── main.py     # 测试示例
├── package.json    # 包配置
├── LICENSE         # MIT 许可协议
└── README.md       # 说明文档
```

## 文件说明

- **si4732.py**：SI4732 核心驱动文件，包含 `SI4732` 类，实现 I2C 命令通信、电源管理、属性访问、固件版本查询和 FM/AM 调谐
- **main.py**：测试示例程序，演示 I2C 设备扫描、芯片身份验证、FM 调谐和状态读取
- **package.json**：upypi 包管理器配置文件
- **LICENSE**：MIT 许可协议

## 快速开始

**步骤 1：复制文件**

将 `si4732.py` 和 `main.py` 复制到 MicroPython 设备的文件系统中。

**步骤 2：接线**

按照硬件要求表格连接 SI4732 模块与 MCU 的 I2C 引脚。注意：
- SDA 和 SCL 需接上拉电阻（通常 4.7k 欧姆，部分模块已集成）
- SEN 引脚决定 I2C 地址（拉高为 0x63，拉低为 0x11）
- RST 引脚为可选，若不使用则传入 None

**步骤 3：配置参数**

在 `main.py` 中根据实际接线修改引脚配置常量（`SCL_PIN`、`SDA_PIN`、`RESET_PIN`）和 I2C 地址（`DEVICE_ADDRESS`）。

**步骤 4：运行测试**

运行 `main.py`，确认 I2C 扫描能找到设备地址，芯片身份验证通过，FM 调谐返回有效状态。

**代码示例**：

```python
from machine import I2C, Pin
from si4732 import SI4732

# 创建 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# 创建复位引脚
reset_pin = Pin(4, Pin.OUT)
reset_pin.value(1)

# 初始化驱动
radio = SI4732(i2c, address=0x63, reset_pin=reset_pin)

# 上电（FM 模式）
radio.reset()
radio.power_up(SI4732.FUNC_FM)

# 读取版本信息
rev = radio.get_revision()
print("Firmware: %d.%d" % (rev["firmware_major"], rev["firmware_minor"]))

# FM 调谐到 101.7 MHz
radio.fm_tune_freq(101700)
status = radio.get_tune_status()
print("Valid:", status["valid"], "RSSI:", status["rssi"], "SNR:", status["snr"])

# 释放资源
radio.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 硬件验证 | **本驱动为冷生成草案，尚未经过硬件验证。** 使用前请在实际硬件上充分测试 |
| 工作条件 | 供电电压 3.3V，I2C 电平需与 MCU 兼容 |
| I2C 上拉 | SDA 和 SCL 需 4.7k 欧姆上拉电阻，部分模块已集成 |
| 频率范围 | 请根据当地无线电法规和模块规格使用合法频率 |
| 天线连接 | 需连接匹配天线才能正常接收 |
| 命令时序 | 驱动自动处理 CTS 等待，每条命令前确保芯片就绪 |
| RDS/Seek | 此版本不支持 RDS 解码和自动搜台功能 |
| SSB/NBFM | 此版本不支持单边带和窄带 FM 模式 |
| 初始化顺序 | 掉电状态下芯片不响应 I2C，需先复位再上电 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | FreakStudio | 初始版本，规范化改写（冷生成，未硬件验证） |

## 联系方式

- GitHub: [https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
