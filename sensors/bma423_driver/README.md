# BMA423 加速度传感器 MicroPython 驱动

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

BMA423 是 Bosch 推出的三轴加速度传感器，支持加速度数据读取和 Bosch 特征引擎（计步、活动识别、倾斜检测等）。本驱动提供 MicroPython I2C 接口，支持加速度数据采集、芯片温度读取、特征检测配置和中断事件映射。

## 主要功能

- 三轴加速度数据读取（x, y, z），单位为 g
- 加速度量程可配置：2g / 4g / 8g / 16g
- 采样频率可配置：25Hz ~ 1600Hz
- 平均模式可配置（性能模式开关下行为不同）
- 高级省电模式（ADP）支持
- 芯片内部温度传感器读取
- Bosch 特征引擎支持：计步器、活动识别、倾斜检测等
- 中断引脚配置与事件映射（支持 INT1/INT2 双引脚）
- I2C 通信自动重试机制

## 硬件要求

### 推荐测试硬件

- 支持 MicroPython 的微控制器开发板（ESP32 / RP2040 等）
- BMA423 传感器模块

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线 |
| SDA | I2C 数据线 |
| INT1 | 中断引脚 1（可选） |
| INT2 | 中断引脚 2（可选） |
| SDO | I2C 地址选择（接 GND = 0x18，接 VCC = 0x19） |

## 软件环境

| 环境 | 版本要求 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |

## 文件结构

```
bma423_driver/
├── code/
│   ├── bma423.py         # 核心驱动文件
│   ├── bma423conf.bin    # Bosch 特征引擎二进制配置文件
│   └── main.py           # 测试示例代码
├── package.json          # 包描述文件
├── LICENSE               # MIT 许可证
└── README.md             # 本说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/bma423.py` | BMA423 加速度传感器核心驱动类，提供加速度读取、特征引擎配置、中断映射等 API |
| `code/bma423conf.bin` | Bosch 官方特征引擎二进制配置文件（6144 字节），用于启用计步器、活动识别、倾斜检测等高级功能。由 `load_features_config()` 方法通过 I2C 写入芯片 ASIC 存储器 |
| `code/main.py` | 测试示例代码，演示加速度数据读取、特征引擎加载和计步器数据获取 |

## 快速开始

### 1. 复制文件

将 `code/bma423.py` 和 `code/bma423conf.bin` 上传到 MicroPython 设备文件系统根目录。

### 2. 硬件接线

| BMA423 | 开发板 (ESP32 示例) |
|--------|---------------------|
| VCC | 3.3V |
| GND | GND |
| SCL | GPIO 22 |
| SDA | GPIO 21 |

### 3. 运行示例代码

```python
import time
from machine import I2C, Pin
from bma423 import BMA423

I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000
I2C_BUS_ID = 0

device = None

time.sleep(3)
print("FreakStudio: Using BMA423 accelerometer driver ...")

i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

device = BMA423(i2c, acc_range=4, debug=False)

try:
    device.load_features_config()
    device.enable_features_detection("step-count")
    print("Feature engine: step counting enabled")
except (OSError, RuntimeError) as e:
    print("Feature engine load failed: %s" % str(e))
    print("Basic acceleration reading still available")

try:
    while True:
        accel = device.get_xyz()
        temp = device.get_temperature()
        steps = device.get_steps()
        print(
            "accel(x,y,z)=(%.3f, %.3f, %.3f)g temp=%.1fC steps=%d" %
            (accel[0], accel[1], accel[2], temp if temp is not None else -999.0, steps)
        )
        time.sleep_ms(500)

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
| I2C 地址 | 默认地址为 0x18（SDO 接 GND）或 0x19（SDO 接 VCC），驱动自动扫描两个地址 |
| 特征引擎配置 | `load_features_config()` 依赖 `bma423conf.bin` 文件，该文件必须与驱动文件位于同一目录 |
| ADP 与计步精度 | 启用高级省电模式（ADP）可能降低计步器精度，实时性要求高的场景建议关闭 ADP |
| 复位等待 | 执行 `reset()` 后需等待约 1 秒完成 ASIC 初始化，不可缩短等待时间 |
| 中断模式 | 特征检测中断仅支持电平触发模式（latch mode），数据就绪中断支持边缘触发 |
| 量程与精度 | 量程越大相对精度越低，12 位 ADC 分辨率固定，2g 量程精度最高约 0.001g |
| 温度传感器 | 内部温度传感器精度有限，仅作参考，不适用于精密温度测量 |
| 硬件验证状态 | 源代码源自 antirez/bma423-pure-mp，本仓库未记录硬件验证结果 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Salvatore Sanfilippo, FreakStudio | 初始版本，支持加速度读取、特征引擎、中断映射 |

## 联系方式

- GitHub: [FreakStudioCN](https://github.com/FreakStudioCN)
- 作者: Salvatore Sanfilippo, FreakStudio

## 许可协议

MIT License

Copyright (c) 2024 Salvatore Sanfilippo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
