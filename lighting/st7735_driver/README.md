# ST7735 TFT LCD 显示驱动 - MicroPython 版本

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

ST7735 是一款 1.8 英寸 TFT LCD 显示驱动芯片，支持 SPI 通信接口，最大分辨率 128x160 像素，16 位色（RGB565 格式）。本驱动基于 Guy Carver 的原始驱动翻译并针对 MicroPython ESP32 平台优化，支持多种屏幕版本（蓝标/红标/绿标），提供完整的绘图 API（像素、直线、矩形、圆形、文本、位图等）。

## 主要功能

- 支持 4 种屏幕初始化模式：蓝标版（initb/initb2）、红标版（initr）、绿标版（initg）
- 完整的 2D 绘图 API：像素、直线、矩形（空心/填充）、圆形（空心/填充）
- 支持 RGB565 16 位色，预置 11 种常用颜色常量
- 支持屏幕旋转（0/90/180/270 度）和 RGB/BGR 颜色顺序切换
- 支持垂直滚动区域设置
- 支持位图图像绘制（image 方法）
- 字体系统：通过字体字典支持自定义字体渲染
- 依赖注入架构：SPI 总线和控制引脚由外部传入，便于多设备共享
- 调试日志开关（debug 参数）

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| ST7735 1.8" TFT LCD 模块 | 蓝标/红标/绿标版本均可 |
| ESP32 开发板 | 主控 MCU |
| 杜邦线 | 至少 6 根（SPI + 控制引脚） |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCK  | SPI 时钟线 |
| MOSI | SPI 数据输出（主设备→从设备） |
| MISO | SPI 数据输入（可不接） |
| DC   | 数据/命令选择引脚 |
| RESET | 硬件复位引脚 |
| CS   | 片选引脚 |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无额外依赖（仅使用 MicroPython 内置模块：machine、time、math） |
| 测试平台 | ESP32 |

## 文件结构

```
├── st7735.py   # ST7735 核心驱动
├── main.py     # 测试示例
└── README.md   # 说明文档
```

## 文件说明

- **st7735.py**：ST7735 TFT LCD 核心驱动文件。包含 `TFT` 类（显示驱动）、`clamp()` 辅助函数（数值限幅）和 `tft_color()` 颜色转换函数。提供 SPI 通信底层操作、寄存器配置、初始化序列和完整的 2D 绘图 API。
- **main.py**：驱动测试示例。初始化 SPI 总线和控制引脚，创建 TFT 实例，运行颜色填充和图形绘制演示。
- **README.md**：本说明文档。

## 快速开始

### 步骤一：复制文件

将 `st7735.py` 和 `main.py` 复制到 MicroPython 设备的根目录。

### 步骤二：接线

按以下方式连接（以 ESP32 为例）：

| ST7735 | ESP32 |
|--------|-------|
| VCC    | 3.3V  |
| GND    | GND   |
| SCK    | GPIO18 |
| MOSI   | GPIO23 |
| MISO   | GPIO19（可选） |
| DC     | GPIO2  |
| RESET  | GPIO4  |
| CS     | GPIO5  |

### 步骤三：运行测试

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Guy Carver, boochow
# @File    : main.py
# @Description : 测试 ST7735 TFT LCD 显示驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, SPI
from st7735 import TFT

# ======================================== 全局变量 ============================================
# SPI 引脚配置（ESP32 为例，可根据实际接线修改）
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 23
SPI_MISO_PIN = 19
# ST7735 控制引脚配置
# ST7735 数据/命令选择引脚
TFT_DC_PIN = 2
# ST7735 复位引脚
TFT_RESET_PIN = 4
# ST7735 片选引脚
TFT_CS_PIN = 5

# 打印间隔控制
last_print_time = time.ticks_ms()
# 打印间隔（ms）
print_interval = 2000

# ======================================== 功能函数 ============================================
def run_display_demo(tft):
    """
    运行显示演示：填充颜色并绘制图形
    此函数默认注释调用，可在 REPL 中手动调用
    Args:
        tft (TFT): TFT 显示驱动实例
    """
    print("Running display demo...")
    # 填充为黑色背景
    tft.fill(TFT.BLACK)

    # 绘制填充矩形（红色）
    tft.fillrect((10, 10), (50, 30), TFT.RED)
    # 绘制空心矩形（绿色）
    tft.rect((10, 50), (50, 30), TFT.GREEN)
    # 绘制水平线（蓝色）
    tft.hline((70, 20), 40, TFT.BLUE)
    # 绘制垂直线（青色）
    tft.vline((70, 20), 40, TFT.CYAN)
    # 绘制填充圆（黄色）
    tft.fillcircle((40, 110), 15, TFT.YELLOW)
    # 绘制空心圆（白色）
    tft.circle((90, 110), 15, TFT.WHITE)
    # 绘制对角线（紫色）
    tft.line((10, 140), (120, 150), TFT.PURPLE)

    print("Display demo completed")


def test_screen_rotation(tft):
    """
    测试屏幕旋转功能（模式切换，默认注释调用，可 REPL 手动触发）
    Args:
        tft (TFT): TFT 显示驱动实例
    """
    # 依次测试 4 个旋转方向
    for rot in range(4):
        tft.rotation(rot)
        tft.fill(TFT.BLACK)
        tft.text((10, 50), "Rot %d" % rot, TFT.WHITE,
                 {'Start': 32, 'End': 126, 'Width': 8, 'Height': 16, 'Data': []})

    # 恢复默认方向
    tft.rotation(0)
    tft.fill(TFT.BLACK)
    print("Rotation test completed")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 st7735.TFT

# ======================================== 初始化配置 ===========================================
# 等待设备就绪
time.sleep(3)
print("FreakStudio: ST7735 TFT LCD display driver test")

# 创建 SPI 总线实例
spi = SPI(1, sck=Pin(SPI_SCK_PIN), mosi=Pin(SPI_MOSI_PIN), miso=Pin(SPI_MISO_PIN),
          baudrate=20000000, polarity=0, phase=0)

# 创建控制引脚实例
dc = Pin(TFT_DC_PIN, Pin.OUT, Pin.PULL_DOWN)
reset = Pin(TFT_RESET_PIN, Pin.OUT, Pin.PULL_DOWN)
cs = Pin(TFT_CS_PIN, Pin.OUT, Pin.PULL_DOWN)

# 创建 TFT 驱动实例
tft = TFT(spi, dc, reset, cs, debug=False)
print("TFT driver instance created")

# 初始化显示（选择适合你屏幕版本的初始化方法）
# 可选：tft.initb(), tft.initr(), tft.initb2(), tft.initg()
print("Initializing display (green tab version)...")
tft.initg()
print("Display initialized")

# 填充黑色背景
tft.fill(TFT.BLACK)

# 设置 RGB 颜色顺序并填充测试颜色
tft.rgb(True)
print("Color order set to RGB")

# 填充蓝色背景测试
tft.fill(TFT.BLUE)
time.sleep_ms(500)

# 填充红色测试
tft.fill(TFT.RED)
time.sleep_ms(500)

# 填充绿色测试
tft.fill(TFT.GREEN)
time.sleep_ms(500)

# 填充黑色（恢复正常）
tft.fill(TFT.BLACK)

# 运行显示演示（低频核心 API，保留自动执行）
run_display_demo(tft)


# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        # 定时打印状态信息
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            size = tft.size()
            rotation_idx = tft.get_rotation()
            rgb_mode = tft.get_rgb()
            print("Screen: %dx%d, Rotation: %d, RGB: %s" %
                  (size[0], size[1], rotation_idx, str(rgb_mode)))
            last_print_time = current_time

        # 模式切换，注释默认执行，可 REPL 手动触发
        # test_screen_rotation(tft)

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    tft.deinit()
    del tft
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V，不得使用 5V 供电，否则可能损坏模块 |
| 初始化方法 | 必须根据屏幕型号选择正确的 init 方法（initb/initb2/initr/initg），错误的初始化会导致花屏或黑屏 |
| SPI 速度 | 建议波特率 20MHz，过高的速率可能导致数据错乱 |
| 颜色顺序 | 不同版本屏幕默认颜色顺序可能不同，可通过 `rgb()` 方法切换 |
| 屏幕旋转 | 旋转会交换屏幕宽高，使用 `size()` 方法获取当前尺寸 |
| 字体系统 | 文本绘制依赖字体字典（包含 Start/End/Width/Height/Data 字段），需自行提供或使用已有字体 |
| 资源释放 | 使用完毕后调用 `deinit()` 关闭显示以降低功耗 |
| 引脚类型 | DC/Reset/CS 引脚必须传入 `machine.Pin` 实例，不接受原始引脚号 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Guy Carver, boochow | 初始版本（GraftSense 规范化） |

## 联系方式

- 原作者：Guy Carver（原始 C 代码翻译）
- MicroPython 移植：boochow
- GraftSense 规范化：GraftSense 团队

## 许可协议

MIT License

Copyright (c) 2026 Guy Carver, boochow

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
