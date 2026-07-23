# 简介

MicroPython I2C 驱动，用于 FT5336 电容触摸控制器芯片。该驱动基于 Adafruit CircuitPython FT5336 驱动改编，移除了 CircuitPython 专用依赖，仅使用 `machine.I2C` 原生接口。支持多点触摸检测、坐标变换（翻转/交换）和芯片 ID 校验功能。

# 主要功能

- 支持最多 5 个触摸点同时检测
- X/Y 轴独立翻转和交换
- 芯片厂商 ID 和芯片 ID 自校验
- 纯 I2C 通信，不依赖任何显示驱动或第三方兼容层
- 内置 I2C 重试机制，增强通信可靠性
- 调试日志开关，方便开发调试

# 硬件要求

- 支持 MicroPython 的微控制器（ESP32、ESP32-S3、RP2040 等）
- FT5336 电容触摸控制器（如 Adafruit 3.5" TFT 320x480 触摸屏 breakout）
- I2C 总线连接线

# 软件环境

- MicroPython v1.23.0 或更高版本
- 无额外固件依赖

# 文件结构

```
ft5336_driver/
├── code/
│   ├── ft5336.py    # 驱动核心文件
│   └── main.py      # 测试示例文件
├── README.md        # 本文件
├── package.json     # 包描述文件
└── LICENSE          # 许可证文件
```

# 文件说明

| 文件 | 说明 |
|---|---|
| `code/ft5336.py` | FT5336 触摸驱动核心类，提供触摸点检测、坐标读取和坐标变换功能 |
| `code/main.py` | 测试示例代码，演示 I2C 扫描、设备初始化和触摸数据轮询 |

# 快速开始

## I2C 接线表

| FT5336 引脚 | MCU 引脚 | 说明 |
|---|---|---|
| VCC | 3.3V / 5V | 电源正极 |
| GND | GND | 电源地 |
| SCL | GPIO 22 | I2C 时钟线 |
| SDA | GPIO 21 | I2C 数据线 |
| INT | GPIO 15（可选） | 触摸中断引脚（本驱动不使用中断） |

## 代码示例

```python
from machine import I2C, Pin
from ft5336 import FT5336

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建 FT5336 驱动实例
touch = FT5336(i2c, width=320, height=480)

# 轮询触摸点数据
while True:
    points = touch.touches()
    if points:
        print(points)
    time.sleep_ms(100)
```

# 注意事项

- 默认 I2C 地址为 `0x38`，请确认设备地址与硬件一致
- 初始化时默认校验芯片 ID（0x79）和厂商 ID（0x11），若不需要可设置 `verify=False`
- 坐标变换（翻转/交换）在读取触摸数据时实时执行，设置后立即生效
- 本驱动为纯 I2C 触摸驱动，不包含显示功能，需配合独立的显示驱动使用
- I2C 总线频率建议不超过 400 kHz

# 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 1.0.0 | 2026-07-19 | 初始版本，基于 Adafruit CircuitPython FT5336 适配 MicroPython |

# 联系方式

- GitHub: [https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

# 许可协议

MIT License

Copyright (c) 2023 Liz Clark for Adafruit Industries

Modified and maintained by FreakStudio

详见 [LICENSE](LICENSE) 文件。
