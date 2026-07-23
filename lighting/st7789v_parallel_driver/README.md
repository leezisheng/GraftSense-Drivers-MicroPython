# ST7789V Parallel MicroPython Driver

## 简介

8-bit 并行接口 / I8080 总线 ST7789/ST7789V TFT LCD 显示驱动，适用于 MicroPython 平台。

此驱动专为 **8-bit 并行接口** 设计，不可与 SPI 版本的 `lighting/st7789_driver` 混用。如果您的硬件通过 SPI 连接 ST7789，请使用 SPI 版本驱动。

## 主要功能

- 8-bit 并行 (I8080) 总线通信
- 支持 135x240、170x320、240x240、320x240 分辨率
- 显示旋转（0/90/180/270 度）
- 基本图形绘制：像素、直线、矩形、填充矩形
- 位图字体文本渲染（8 位宽和 16 位宽）
- TrueType 转换字体绘制
- 位图图像显示
- 硬件垂直滚动
- 睡眠模式和反转模式控制
- 依赖注入设计，引脚由外部传入

## 硬件要求

- 支持 MicroPython 的开发板（ESP32、RP2040 等）
- ST7789/ST7789V TFT LCD 显示屏（8-bit 并行接口版本）
- 接线要求：

| 引脚 | 说明 |
|------|------|
| D0-D7 | 8 位并行数据总线（D7=MSB, D0=LSB） |
| WR | 写选通信号 |
| RD | 读选通信号 |
| DC (RS) | 数据/命令选择 |
| CS | 片选信号 |
| RST | 复位信号 |
| BL | 背光控制 |

## 软件环境

- MicroPython v1.23+
- 无需额外固件依赖

## 文件结构

```
st7789v_parallel_driver/
├── code/
│   ├── st7789v_parallel.py    # 驱动核心代码
│   └── main.py                # 测试示例代码
├── README.md                  # 本文件
├── package.json               # 包配置信息
└── LICENSE                    # MIT 许可证
```

## 文件说明

- `code/st7789v_parallel.py`：ST7789/ST7789V 8-bit 并行接口驱动程序，包含完整的图形绘制、文本渲染和滚动控制 API。
- `code/main.py`：驱动测试示例，演示并行引脚配置、初始化和基本图形绘制。

## 快速开始

```python
from machine import Pin
from st7789v_parallel import ST7789, color565, BLACK, WHITE

# 配置数据总线引脚（D7..D0）
DATA_PINS = (7, 6, 5, 4, 3, 2, 1, 0)
data = [Pin(pin, Pin.OUT) for pin in DATA_PINS]

# 创建显示器实例
display = ST7789(
    data[0], data[1], data[2], data[3],
    data[4], data[5], data[6], data[7],
    Pin(8, Pin.OUT),   # WR
    Pin(9, Pin.OUT),   # RD
    170,                # 宽度
    320,                # 高度
    reset=Pin(12, Pin.OUT),
    dc=Pin(10, Pin.OUT),
    cs=Pin(11, Pin.OUT),
    backlight=Pin(13, Pin.OUT),
    rotation=0,
)

# 清屏并绘制测试图形
display.fill(BLACK)
display.fill_rect(20, 20, 60, 20, color565(0, 160, 255))
display.rect(10, 10, 80, 40, WHITE)
```

## 注意事项

- 此驱动仅适用于 **8-bit 并行/I8080 接口** 的 ST7789/ST7789V 显示屏，不可与 SPI 接口版本混用。
- SPI 版本的 ST7789 驱动位于 `lighting/st7789_driver/`。
- 所有引脚必须作为 `machine.Pin` 实例从外部传入，驱动内部不创建 Pin 对象。
- 绘制大量像素时，驱动使用分块写入以控制内存占用。
- 直线绘制算法包含超时保护，防止异常坐标导致死循环。

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-07-19 | 规范化版本，源自 russhughes/t-display-s3 |

## 联系方式

- 作者：Russ Hughes, FreakStudio
- 仓库：[GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License. 详见 LICENSE 文件。
基于 devbis/st7789py_mpy 和 russhughes/st7789py_mpy 的工作。
