# GraftSense-APA102/DotStar LED 灯带模块（MicroPython）

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本项目是 **FreakStudio GraftSense APA102/DotStar LED 灯带模块** 的 MicroPython 驱动库。APA102（又称 DotStar）是一种通过 SPI 协议控制的 2 线可寻址 RGB LED 灯带，每个像素内置 PWM 控制器，支持全局和独立亮度调节，适用于灯光装饰、状态指示器、可穿戴设备等场景。

---

## 主要功能

- **SPI 高速通信**: 通过标准 SPI 接口驱动灯带，仅需 SCK 和 MOSI 两根信号线
- **可寻址控制**: 每个 LED 像素可独立设置 RGB 颜色，支持级联多像素
- **全局亮度**: 支持 0.0-1.0 范围的全局亮度调节，通过 5 位硬件 PWM 实现
- **独立像素亮度**: 每个像素可设置独立的亮度值，实现精细的灯光层次
- **自动/手动刷新**: 支持 auto_write 模式（每次设置后自动刷新）和手动 show() 模式（批量更新）
- **颜色顺序适配**: 支持 RGB/RBG/GRB/GBR/BRG/BGR 六种颜色通道顺序，兼容不同制造商
- **缓冲区优化**: 内部预分配帧缓冲区，包含起始帧和结束帧，亮度调节时按需创建副本
- **上下文管理**: 支持 with 语句，退出时自动释放 SPI 资源

---

## 硬件要求

- **核心模块**: APA102/DotStar LED 灯带（5050 封装，内置 SK9822 或兼容控制器）
- **开发环境**: MicroPython v1.23.0 及以上版本（ESP32、Raspberry Pi Pico 等开发板均可）
- **连接方式**: SPI 接口（仅需 SCK 和 MOSI 引脚，MISO 不使用）
- **电源规格**: 灯带需独立供电，单个像素全白最大电流约 60mA，多像素级联时需确保电源容量充足

---

## 文件说明

| 文件名      | 功能描述                                                                 |
|-------------|--------------------------------------------------------------------------|
| `apa102.py` | 核心驱动库，定义 `DotStar` 类，封装像素控制、亮度调节与 SPI 通信功能     |
| `main.py`   | 测试与示例代码，包含颜色填充、彩虹循环、亮度调节等功能演示                |

---

## 软件设计核心思想

1. **SPI 直接驱动**: 利用 hardware SPI 外设实现高速数据传输，避免软件模拟时钟造成的时序不准
2. **帧缓冲区管理**: 内部维护完整的 APA102 帧（起始帧 + Nx4 字节像素数据 + 结束帧），减少发送时的拼接开销
3. **亮度独立计算**: 亮度调整时创建缓冲区副本而非修改原始数据，避免精度损失累积
4. **Pythonic API**: 实现 `__getitem__`/`__setitem__`/`__len__` 使得 LED 灯带可以像列表一样操作，简化编程
5. **工程化设计**: 提供完整的参数校验、类型注解、异常处理和中英文文档，降低使用门槛

---

## 使用说明

### 1. 环境准备

- 安装 MicroPython v1.23.0 到目标开发板
- 将 `apa102.py` 上传至开发板文件系统

### 2. 硬件连接

| 开发板引脚 | APA102 模块引脚 | 说明               |
|-----------|----------------|-------------------|
| SCK (GPIO) | CI / CLK       | 时钟信号线          |
| MOSI (GPIO) | DI / DATA     | 数据信号线          |
| GND        | GND            | 共地               |
| 外部 5V    | VCC / 5V       | 独立供电（大电流）   |

### 3. 初始化驱动

```python
from machine import Pin, SPI
from apa102 import DotStar, BGR

# 初始化 SPI
spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))

# 创建灯带实例（8 像素，亮度 20%，BGR 颜色顺序）
leds = DotStar(spi, 8, brightness=0.2, auto_write=False, pixel_order=BGR)
```

### 4. 基础操作

```python
# 设置单个像素为红色
leds[0] = (255, 0, 0)
leds.show()

# 批量设置多个像素
leds[0:3] = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
leds.show()

# 设置全部像素
leds.fill((128, 64, 0))
leds.show()

# 调节亮度
leds.brightness = 0.5  # 自动刷新（若 auto_write=True）

# 读取像素颜色
r, g, b = leds[0]

# 使用 with 语句自动释放资源
with DotStar(spi, 8) as leds:
    leds[0] = (255, 255, 255)
    leds.show()
```

---

## 示例程序

### 颜色填充特效

```python
def color_wipe(leds, color, delay=0.1):
    for i in range(len(leds)):
        leds[i] = color
        time.sleep(delay)
    leds.fill((0, 0, 0))

# 调用示例
color_wipe(leds, (255, 0, 0), delay=0.05)
```

### 彩虹循环

```python
def rainbow_cycle(leds, delay=0.05):
    n = len(leds)
    for j in range(256):
        for i in range(n):
            pixel_index = (i * 256 // n) + j
            r = _wheel((pixel_index & 255))
            g = _wheel(((pixel_index + 85) & 255))
            b = _wheel(((pixel_index + 170) & 255))
            leds[i] = (r, g, b)
        time.sleep(delay)

rainbow_cycle(leds, delay=0.02)
```

### 0xRRGGBB 颜色格式

```python
# 支持整型颜色值
leds[0] = 0xFF0000  # 红色
leds[1] = 0x00FF00  # 绿色
leds.show()
```

---

## 注意事项

1. **独立供电**: 灯带在大电流（多个像素全白）时功耗较高，务必使用外部 5V 供电，不可仅靠开发板 3.3V 引脚供电
2. **信号电平**: APA102 信号线通常兼容 3.3V 逻辑电平，但建议使用电平转换器（3.3V 到 5V）确保长距离传输可靠性
3. **结束帧长度**: 每 16 个像素需要额外 1 字节结束帧，对于大量像素的灯带，结束帧字节数 = ceil(N/16)
4. **颜色顺序**: 不同制造商生产的 APA102 灯带可能使用不同的颜色通道顺序（常见为 BGR），若颜色显示异常请调整 pixel_order 参数
5. **POV 应用**: 独立像素亮度通过 PWM 实现，该 PWM 频率较低，可能影响视觉暂留（POV）应用的效果
6. **自动刷新性能**: auto_write=True 时每次像素设置都会触发 SPI 写入，批量更新时建议设为 False 并手动调用 show()
7. **SPI 频率**: 推荐使用 1-8MHz 的 SPI 频率，过高的频率可能导致信号质量下降

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:  
📧 **邮箱**: <liqinghsui@freakstudio.cn>  
💻 **GitHub**: [https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---

## 许可协议

本项目采用 **MIT License** 开源协议。

```text
MIT License

Copyright (c) 2016 Damien P. George
Copyright (c) 2017 Adafruit Industries
Copyright (c) 2019 Matt Trentini
Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
