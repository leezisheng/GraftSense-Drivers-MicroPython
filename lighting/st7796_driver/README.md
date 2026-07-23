# ST7796 / ST7796S MicroPython 驱动

> 仅静态检查通过，未硬件验证。

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

ST7796/ST7796S 是 Sitronix 推出的 TFT LCD 显示控制器，常用于 320x480 分辨率的 SPI 接口显示屏。
本驱动提供 ST7796 系列显示屏的基础 SPI 控制能力，包括初始化、像素绘制、矩形填充、颜色反转和背光控制等功能。
支持 16 位 RGB565 颜色格式，可配合 LVGL 等图形库在 MicroPython 环境下使用。

> 注意：ST7796 的初始化命令序列与 ST7789 不同，不可互换使用。
> 参考初始化序列来源：[lvgl_micropython 仓库](https://github.com/lvgl-micropython/lvgl_micropython/tree/main/api_drivers/common_api_drivers/display/st7796)

## 主要功能

- SPI 通信接口，4 线制（SCK, MOSI, DC, CS）+ 可选 RST/BL
- 支持硬件复位和软件复位两种方式
- 支持 0/90/180/270 度四种显示旋转
- 支持 RGB 和 BGR 两种颜色顺序
- 全屏填充、矩形填充、单像素绘制
- 缓冲区批量写入（blit_buffer），方便与图形库集成
- 显示反转、显示开关控制
- 背光独立控制
- 调试日志可开关

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| ST7796 / ST7796S TFT 显示屏 | 320x480 分辨率，SPI 接口 |
| ESP32 或 RP2040 开发板 | 支持 MicroPython SPI |
| 杜邦线若干 | 连接显示屏与开发板 |

### 引脚说明

| 显示屏引脚 | 功能描述 | 连接开发板 |
|-----------|----------|-----------|
| VCC | 电源正极（3.3V） | 3.3V |
| GND | 电源负极 | GND |
| SCK | SPI 时钟线 | GPIO18 |
| MOSI | SPI MOSI 数据输出 | GPIO23 |
| DC | 数据/命令选择 | GPIO2 |
| CS | 片选 | GPIO15 |
| RST | 复位（可选） | GPIO4 |
| BL | 背光控制（可选） | GPIO5 |

> 引脚号可根据实际接线在 `main.py` 中修改。

## 软件环境

| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.1.0 |
| 依赖 | 无外部依赖，仅使用 MicroPython 内置模块（`machine`、`struct`、`time`） |

## 文件结构

```
├── st7796.py         # 核心驱动文件
├── main.py           # 测试示例
└── README.md         # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `st7796.py` | ST7796/ST7796S SPI 显示驱动核心文件，包含 `ST7796` 类和 `color565` 辅助函数 |
| `main.py` | 测试示例程序，演示 SPI 初始化、显示驱动创建和基础绘图功能 |

## 快速开始

### 1. 复制文件到设备

将 `st7796.py` 和 `main.py` 复制到 MicroPython 设备的文件系统中。

### 2. 硬件接线

按[硬件要求](#硬件要求)中的引脚说明连接显示屏与开发板。

### 3. 运行测试

在设备上运行 `main.py`：

```python
import main
```

或通过 REPL 手动运行：

```python
from machine import SPI, Pin
from st7796 import ST7796, RED, GREEN, BLUE, WHITE, BLACK, BGR

# 初始化 SPI 总线
spi = SPI(1, baudrate=40000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))

# 初始化控制引脚
dc = Pin(2, Pin.OUT)
cs = Pin(15, Pin.OUT)
rst = Pin(4, Pin.OUT)
bl = Pin(5, Pin.OUT)

# 创建显示驱动实例
display = ST7796(spi=spi, dc=dc, cs=cs, reset=rst, backlight=bl,
                 width=320, height=480, rotation=0, color_order=BGR)

# 清屏
display.fill(BLACK)

# 绘制色块
display.fill_rect(10, 10, 100, 100, RED)
display.fill_rect(210, 370, 100, 100, BLUE)

# 绘制像素
display.pixel(160, 240, WHITE)
```

## 注意事项

| 类别 | 说明 |
|------|------|
| **色彩格式** | 仅支持 16 位 RGB565 颜色格式，使用 `color565()` 工具函数将 RGB888 转换为 RGB565 |
| **颜色顺序** | 默认为 BGR，部分屏幕可能需要 RGB，通过 `color_order` 参数配置 |
| **分辨率** | 默认 320x480，若使用不同分辨率的 ST7796 变体需修改 `width`/`height` 参数 |
| **初始化序列** | ST7796 与 ST7789 的初始化序列不同，不可混用 |
| **SPI 速率** | 默认 40MHz，若不稳定可降低至 20MHz 或 10MHz |
| **背光极性** | 默认高电平点亮背光，部分电路可能低电平有效，需根据实际硬件确认 |
| **依赖注入** | 驱动不自行创建 SPI 和 Pin 对象，必须由调用方传入 |
| **验证状态** | 仅静态检查通过，未在真实硬件上验证 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-07-23 | FreakStudio | 初始版本，基于 LVGL 开源项目初始化序列 |

## 联系方式

- 邮箱：FreakStudio@163.com
- GitHub：[FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

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
