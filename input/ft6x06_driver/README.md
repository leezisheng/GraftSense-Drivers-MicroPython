# 简介

MicroPython I2C 驱动，用于 FT6x06 系列（FT6206/FT6306 等）电容触摸控制器芯片。该驱动基于 antirez/micropython-ft6x06 原始代码适配，仅使用 `machine.I2C` 原生接口。支持多点触摸检测、坐标读取、手势识别和中断回调功能。

# 主要功能

- 支持多点触摸检测（最多 2 点，取决于芯片型号）
- 触摸事件类型识别（按下/抬起）
- 触摸压力和面积信息读取
- 可选中断引脚配置，支持触摸事件回调
- ISR 安全设计，通过 micropython.schedule 推迟 I/O 到主循环上下文
- 纯 I2C 通信，不依赖任何显示驱动或第三方兼容层
- 内置 I2C 重试机制，增强通信可靠性
- 调试日志开关，方便开发调试

# 硬件要求

- 支持 MicroPython 的微控制器（ESP32、ESP32-S3、RP2040 等）
- FT6x06 系列电容触摸控制器（FT6206、FT6306 等）
- I2C 总线连接线
- 中断引脚连接线（可选，用于事件驱动模式）

# 软件环境

- MicroPython v1.23.0 或更高版本
- 无额外固件依赖

# 文件结构

```
ft6x06_driver/
├── code/
│   ├── ft6x06.py    # 驱动核心文件
│   └── main.py      # 测试示例文件
├── README.md        # 本文件
├── package.json     # 包描述文件
└── LICENSE          # 许可证文件
```

# 文件说明

| 文件 | 说明 |
|---|---|
| `code/ft6x06.py` | FT6x06 系列触摸驱动核心类，提供触摸点检测、坐标读取和中断回调支持 |
| `code/main.py` | 测试示例代码，演示 I2C 扫描、设备初始化和触摸数据轮询 |

# 快速开始

## I2C 接线表（轮询模式）

| FT6x06 引脚 | MCU 引脚 | 说明 |
|---|---|---|
| VCC | 3.3V | 电源正极 |
| GND | GND | 电源地 |
| SCL | GPIO 22 | I2C 时钟线 |
| SDA | GPIO 21 | I2C 数据线 |
| INT | 不接 | 触摸中断引脚（轮询模式时不需连接） |

## I2C 接线表（中断模式）

| FT6x06 引脚 | MCU 引脚 | 说明 |
|---|---|---|
| VCC | 3.3V | 电源正极 |
| GND | GND | 电源地 |
| SCL | GPIO 22 | I2C 时钟线 |
| SDA | GPIO 21 | I2C 数据线 |
| INT | GPIO 15 | 触摸中断引脚（下降沿触发） |

## 代码示例（轮询模式）

```python
from machine import I2C, Pin
from ft6x06 import FT6x06

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建 FT6x06 驱动实例
touch = FT6x06(i2c)

# 轮询触摸点数据
while True:
    points = touch.get_touch_coords()
    if points:
        print(points)
    time.sleep_ms(100)
```

## 代码示例（中断模式）

```python
from machine import I2C, Pin
from ft6x06 import FT6x06
import time

# 定义触摸回调函数
def on_touch(data):
    print("Touch event:", data)

# 初始化 I2C 总线和中断引脚
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
int_pin = Pin(15, Pin.IN)

# 创建 FT6x06 驱动实例（中断模式）
touch = FT6x06(i2c, interrupt_pin=int_pin, callback=on_touch)

# 主循环保持运行，触摸事件通过回调通知
while True:
    time.sleep_ms(100)
```

# 注意事项

- 默认 I2C 地址为 `0x38`，请确认设备地址与硬件一致
- 驱动支持轮询模式和中断模式两种使用方式
- 中断模式使用 micropython.schedule 推迟 I/O 操作到主循环上下文，确保 ISR 安全
- 本驱动为纯 I2C 触摸驱动，不包含显示功能，需配合独立的显示驱动使用
- I2C 总线频率建议不超过 400 kHz
- 不同 FT6x06 系列芯片的触摸点数上限可能不同（FT6206 通常支持 2 点）

# 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 1.0.0 | 2026-07-19 | 初始版本，基于 antirez/micropython-ft6x06 适配并规范化 |

# 联系方式

- GitHub: [https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

# 许可协议

MIT License

Copyright (C) 2024 Salvatore Sanfilippo -- All Rights Reserved

Modified and maintained by FreakStudio

详见 [LICENSE](LICENSE) 文件。
