# DRV2605L MicroPython Driver

## 简介

MicroPython I2C 驱动，适用于 TI DRV2605/DRV2605L 触觉反馈电机控制器。

通过 I2C 总线控制触觉振动电机，支持多种操作模式、内置波形效果库、实时播放和序列编辑功能。可驱动 ERM（偏心旋转质量）电机和 LRA（线性谐振执行器）电机。

## 主要功能

- I2C 通信接口（默认地址 0x5A）
- 芯片 ID 自动检测（DRV2605 或 DRV2605L）
- 8 种操作模式：内部触发、外部触发（边沿/电平）、PWM/模拟、音频转振动、实时播放、诊断、自动校准
- 6 种波形效果库（TS2200 A-E + LRA 专用库）
- 8 个波形序列槽位，支持组合多个效果
- `play_effect()` 方法：支持阻塞等待（含超时保护）和非阻塞模式
- ERM/LRA 电机类型切换
- 实时播放模式（支持带符号振幅控制）
- 依赖注入设计，I2C 总线由外部传入

## 硬件要求

- 支持 MicroPython 的开发板（ESP32、RP2040 等）
- TI DRV2605 或 DRV2605L 触觉驱动芯片
- 振动电机（ERM 或 LRA 类型）
- I2C 接线：

| 引脚 | 说明 |
|------|------|
| SDA | I2C 数据线 |
| SCL | I2C 时钟线 |
| VCC | 电源（2.5V-5.5V） |
| GND | 地 |
| OUT+/OUT- | 电机输出 |

## 软件环境

- MicroPython v1.23+
- 无需额外固件依赖

## 文件结构

```
drv2605l_driver/
├── code/
│   ├── drv2605l.py             # 驱动核心代码
│   └── main.py                 # 测试示例代码
├── README.md                   # 本文件
├── package.json                # 包配置信息
└── LICENSE                     # MIT 许可证
```

## 文件说明

- `code/drv2605l.py`：DRV2605/DRV2605L I2C 驱动程序，包含 Effect、Pause 和 DRV2605 类，提供完整的模式控制、波形库管理和序列编辑 API。
- `code/main.py`：驱动测试示例，演示 I2C 初始化、设备扫描、效果播放和超时保护用法。

## 快速开始

```python
from machine import I2C, Pin
from drv2605l import DRV2605, Effect

# 初始化 I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建驱动实例
drv = DRV2605(i2c)

# 设置波形序列并播放
drv.sequence[0] = Effect(1)   # 强点击
drv.sequence[1] = Effect(0)   # 空
drv.play_effect(timeout_ms=2000)  # 播放并等待完成

# 实时播放示例
drv.realtime_value = 0
drv.mode = 5  # MODE_REALTIME
drv.realtime_value = 64   # 50% 振幅
time.sleep(0.5)
drv.realtime_value = 0    # 停止
drv.mode = 0              # 返回内部触发模式
```

## 波形效果库

| 库 | 值 | 说明 |
|---|---|---|
| LIBRARY_EMPTY | 0 | 空库 |
| LIBRARY_TS2200A | 1 | TS2200 库 A（默认） |
| LIBRARY_TS2200B | 2 | TS2200 库 B |
| LIBRARY_TS2200C | 3 | TS2200 库 C |
| LIBRARY_TS2200D | 4 | TS2200 库 D |
| LIBRARY_TS2200E | 5 | TS2200 库 E |
| LIBRARY_LRA | 6 | LRA 专用库 |

## 操作模式

| 模式 | 值 | 说明 |
|---|---|---|
| MODE_INTTRIG | 0 | 内部触发（默认） |
| MODE_EXTTRIGEDGE | 1 | 外部触发，边沿模式 |
| MODE_EXTTRIGLVL | 2 | 外部触发，电平模式 |
| MODE_PWMANALOG | 3 | PWM/模拟输入模式 |
| MODE_AUDIOVIBE | 4 | 音频转振动模式 |
| MODE_REALTIME | 5 | 实时播放模式 |
| MODE_DIAGNOS | 6 | 诊断模式 |
| MODE_AUTOCAL | 7 | 自动校准模式 |

## 注意事项

- 上电后需要进行自动校准以获得最佳效果。
- `play_effect()` 默认最多等待 5 秒（可自定义超时时间），设置 `timeout_ms=0` 可实现非阻塞播放。
- 波形效果 ID 范围 0-123，具体效果参考 DRV2605 数据手册。
- ERM 电机为默认类型，LRA 电机需调用 `use_LRM()` 切换。
- I2C 总线实例必须从外部传入（依赖注入），驱动内部不创建 I2C 对象。

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-07-19 | 规范化版本，源自 Adafruit_CircuitPython_DRV2605 |

## 联系方式

- 作者：Tony DiCola, VynDragon, FreakStudio
- 仓库：[GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License. 详见 LICENSE 文件。

原始版权：(c) 2017 Tony DiCola for Adafruit Industries
