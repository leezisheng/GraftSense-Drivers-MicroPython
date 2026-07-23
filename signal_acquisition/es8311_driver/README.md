# ES8311 音频编解码器 MicroPython 驱动

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

ES8311 是 Everest Semiconductor 推出的低功耗音频编解码器（Codec），集成单声道 ADC 和单声道 DAC，支持 I2C 控制接口和 I2S/PCM 数字音频接口。本驱动是对 ES8311 的 I2C 寄存器配置层封装，负责通过 I2C 配置芯片的时钟方案、音频格式、采样率和音量等参数。实际的 I2S 音频数据传输由应用层的 `machine.I2S` 完成。

驱动代码参考了 M5Stack UIFlow MicroPython 开源项目（m5stack/uiflow-micropython），将原多文件模块结构合并为单文件并进行了规范化。

**仅静态检查通过，未硬件验证。**

## 主要功能

- 完整的 I2C 寄存器映射常量（寄存器地址宏定义）
- 丰富的采样率支持（8kHz / 11.025kHz / 12kHz / 16kHz / 22.05kHz / 24kHz / 32kHz / 44.1kHz / 48kHz / 64kHz / 88.2kHz / 96kHz）
- 多种 MCLK 主时钟频率适配（1.024MHz ~ 18.432MHz）
- 支持多种音频分辨率（16/18/20/24/32 位）
- MCLK / SCLK 极性配置
- MCLK 来源选择（MCLK 引脚 / BCLK 引脚）
- DAC 音量控制（0-100 级，自动钳位）
- 模拟麦克风和数字 PDM 麦克风模式切换
- I2C 通信异常自动包装为 RuntimeError
- 调试日志开关，库默认静默

## 硬件要求

| 推荐测试硬件 | 说明 |
|-------------|------|
| M5Stack CoreS3 / ATOM Echo | 集成 ES8311 的开发板 |
| ES8311 模组 + 任意 MicroPython 开发板 | I2C + I2S 接线 |

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| MCLK | I2S 主时钟（可选，也可由 BCLK 提供） |
| BCLK | I2S 位时钟 |
| LRCK | I2S 字选择（左右声道时钟） |
| DOUT | I2S 数据输出（DAC 播放） |
| DIN  | I2S 数据输入（ADC 录音） |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（仅使用 machine、time 内置模块） |

## 文件结构

```
├── code/
│   ├── es8311.py        # 核心驱动（I2C 寄存器配置）
│   └── main.py          # 测试示例（含 I2S 使用演示）
├── package.json         # 包配置文件
└── README.md            # 说明文档
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `code/es8311.py` | ES8311 I2C 配置驱动核心代码，包含寄存器映射常量、时钟系数查找表、ES8311ClockConfig 配置容器和 ES8311 驱动类 |
| `code/main.py` | 完整测试示例，演示 I2C 初始化、芯片 ID 验证、编解码器初始化和 I2S 音频接口的创建与使用 |
| `package.json` | mip 包配置文件，支持 `mip.install` 安装 |

## 快速开始

### 步骤 1：复制文件

将 `code/es8311.py` 和 `code/main.py` 复制到 MicroPython 设备的 `/` 根目录或 `/lib/` 目录。

### 步骤 2：接线

根据硬件要求表格连接 I2C 和 I2S 引脚。`main.py` 中使用的默认引脚如下（请根据实际硬件修改）：

| 引脚常量 | 默认值 | 说明 |
|---------|--------|------|
| `SCL_PIN` | 22 | I2C 时钟 |
| `SDA_PIN` | 21 | I2C 数据 |
| `I2S_BCK_PIN` | 5 | I2S 位时钟 |
| `I2S_WS_PIN` | 25 | I2S 字选择 |
| `I2S_DOUT_PIN` | 26 | I2S 数据输出 |
| `I2S_DIN_PIN` | 35 | I2S 数据输入 |

### 步骤 3：运行测试

```python
# 方式一：直接运行 main.py
import main

# 方式二：最小示例
from machine import I2C, Pin
from es8311 import ES8311, ES8311ClockConfig

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
codec = ES8311(i2c, address=0x18)

# 构建时钟配置
clk_cfg = ES8311ClockConfig(
    mclk_inverted=False,
    sclk_inverted=False,
    mclk_from_mclk_pin=False,
    mclk_frequency=0,
    sample_frequency=48000,
)

# 初始化编解码器
codec.init(clk_cfg, ES8311.ES8311_RESOLUTION_16, ES8311.ES8311_RESOLUTION_16)

# 设置音量
codec.voice_volume_set(80)

# 配置模拟麦克风
codec.microphone_config(digital_mic=False)

# 释放资源
codec.deinit()
```

## 注意事项

| 类别 | 限制与说明 |
|------|-----------|
| 驱动范围 | 本驱动仅负责 I2C 寄存器配置，**不包含 I2S 数据传输功能**。音频播放和录音由 `machine.I2S` 在应用层处理 |
| 代码来源 | 基于 M5Stack UIFlow MicroPython（MIT License）改编 |
| 验证状态 | 仅静态检查通过，**未硬件验证** |
| I2C 地址 | 默认地址 0x18，可通过 `address` 参数修改 |
| 采样率限制 | 仅支持系数表中列出的 MCLK/采样率组合，不匹配时静默跳过 |
| 音量范围 | 0-100，超出范围自动钳位，0 为静音 |
| 依赖注入 | I2C 实例由外部传入，驱动类内部不创建硬件对象 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | M5Stack Technology CO LTD, FreakStudio | 初始版本（规范化后的单文件驱动） |

## 联系方式

- GitHub: [GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 M5Stack Technology CO LTD, FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
