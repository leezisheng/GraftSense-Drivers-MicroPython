# ES7210 四通道音频 ADC MicroPython 驱动

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

ES7210 是 Everest Semiconductor 推出的四通道音频 ADC 芯片。本驱动为 MicroPython I2C 控制驱动程序，仅通过 I2C 总线配置 ES7210 的工作寄存器（时钟、采样率、位深、增益等）。音频 I2S 数据流由应用层使用 `machine.I2S(mode=I2S.RX)` 独立处理，不包含在本驱动内部。

**重要提示：本驱动为冷生成草稿代码，未经过硬件验证，不可直接用于生产环境。**

## 主要功能

- I2C 寄存器读写，带自动重试机制
- 完整设备配置流程：复位 → 时钟 → 高通滤波 → I2S 格式 → 采样率 → 增益 → 电源
- 采样率配置：支持 8000 / 16000 / 24000 / 32000 / 44100 / 48000 / 96000 Hz
- 采样位深配置：16 / 18 / 20 / 24 / 32 位
- 麦克风增益配置：0 ~ 37.5 dB，四通道独立设置
- TDM 模式支持（多通道时分复用）
- 静音控制
- 电源管理与资源释放
- I2C 通信自检功能

## 硬件要求

### 推荐测试硬件

- 支持 MicroPython 的微控制器开发板（ESP32 / RP2040 等）
- ES7210 音频 ADC 模块

### 引脚说明

**I2C 配置接口（控制寄存器）：**

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线 |
| SDA | I2C 数据线 |

**I2S 音频接口（数据流，由应用层单独配置）：**

| 引脚 | 功能描述 |
|------|----------|
| BCK | I2S 位时钟 |
| WS | I2S 字选（左右通道） |
| SD | I2S 数据输入 |

## 软件环境

| 环境 | 版本要求 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.1.0 |

## 文件结构

```
es7210_driver/
├── code/
│   ├── es7210.py         # 核心驱动文件（I2C 寄存器控制）
│   └── main.py           # 测试示例代码
├── package.json          # 包描述文件
├── LICENSE               # MIT 许可证
└── README.md             # 本说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/es7210.py` | ES7210 I2C 控制驱动类，负责所有寄存器配置操作（时钟、位深、采样率、增益、电源管理等）。不创建 `machine.I2S` 对象 |
| `code/main.py` | 测试示例代码，演示 I2C 初始化、设备自检和 I2S 数据流配置参考 |

## 快速开始

### 1. 复制文件

将 `code/es7210.py` 上传到 MicroPython 设备文件系统。

### 2. 硬件接线

**I2C 配置接口：**

| ES7210 | 开发板 (ESP32 示例) |
|--------|---------------------|
| VCC | 3.3V |
| GND | GND |
| SCL | GPIO 22 |
| SDA | GPIO 21 |

**I2S 音频接口（可选）：**

| ES7210 | 开发板 (ESP32 示例) |
|--------|---------------------|
| BCK | GPIO 26 |
| WS | GPIO 25 |
| SD | GPIO 33 |

### 3. 运行示例代码

```python
import time
from machine import I2C, Pin
from es7210 import ES7210, DEFAULT_ADDRESS

I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000
I2C_BUS_ID = 0

I2S_BCK_PIN = 26
I2S_WS_PIN = 25
I2S_SD_PIN = 33
I2S_ID = 0

device = None

time.sleep(3)
print("FreakStudio: Using ES7210 audio ADC I2C control driver ...")
print("NOTE: This driver is cold-generated and NOT hardware verified")

i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])
if DEFAULT_ADDRESS not in devices:
    raise RuntimeError("ES7210 not found at expected address 0x%02X" % DEFAULT_ADDRESS)
print("ES7210 found at I2C address 0x%02X" % DEFAULT_ADDRESS)

device = ES7210(i2c, sample_rate=16000, bits_per_sample=16, mic_gain_db=24, tdm=False, debug=False)

try:
    device.self_test()
    print("ES7210 I2C self-test passed")
except RuntimeError as e:
    print("ES7210 I2C self-test failed: %s" % str(e))
    print("Continuing with configuration anyway (cold-generated code)")

print("ES7210 I2C configuration completed")
print("Audio I2S data stream should be set up separately with machine.I2S(mode=I2S.RX)")

try:
    from machine import I2S
    audio_in = I2S(
        I2S_ID,
        sck=Pin(I2S_BCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_SD_PIN),
        mode=I2S.RX,
        bits=16,
        format=I2S.STEREO,
        rate=16000,
        ibuf=4096,
    )
    print("I2S audio input initialized")
except ImportError:
    print("machine.I2S not available on this platform")

try:
    while True:
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if device is not None:
        device.deinit()
    device = None
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 架构说明 | 本驱动仅处理 I2C 寄存器配置，不创建 `machine.I2S` 对象。音频 I2S 数据流由应用层单独使用 `machine.I2S(mode=I2S.RX)` 实现。I2C 配置总线和 I2S 数据总线是独立的物理接口，不可混淆 |
| 硬件验证状态 | **未硬件验证**：本驱动为冷生成草稿代码，寄存器配置值来源于数据手册笔记和 ESPHome C++ 参考代码，未在实际硬件上通过 `mpremote` 或其他方式验证。标记为"已硬件验证"或用于生产环境前必须完成实际硬件测试 |
| I2C 地址 | 默认 I2C 地址为 0x40 |
| 采样率支持 | 仅支持系数表中列出的采样率（8000/16000/24000/32000/44100/48000/96000 Hz），其他采样率可能导致配置失败 |
| 增益精度 | 增益步进为 3dB，非连续调节 |
| 自检限制 | `self_test()` 方法仅验证 I2C 通信是否正常（寄存器回读），不验证 I2S 音频数据输出是否正常 |
| 平台兼容性 | `machine.I2S` 在不同 MicroPython 端口（ESP32 / RP2040）上的引脚限制和行为差异较大，I2S 配置需根据具体平台调整 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-07-19 | FreakStudio | 冷生成初始版本，I2C 寄存器配置驱动，未硬件验证 |

## 联系方式

- GitHub: [FreakStudioCN](https://github.com/FreakStudioCN)
- 作者: FreakStudio

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
