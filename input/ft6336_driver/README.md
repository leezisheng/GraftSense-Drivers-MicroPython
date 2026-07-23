# FT6336 / FT6336U MicroPython 驱动

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

FT6336/FT6336U 是一款 I2C 接口的电容触摸控制器芯片，支持单点及多点触摸检测和手势识别。本驱动提供 MicroPython 下的触摸坐标读取、触摸点数查询、手势识别及芯片 ID 验证功能。驱动源自 Waveshare Apache-2.0 参考实现，已完成规范化改写。

> **注意**：本驱动仅静态检查通过，未硬件验证。

## 主要功能

- 支持 FT6336 / FT6336U 电容触摸控制器
- 触摸坐标读取：返回触点坐标及当前触摸点数
- 触摸点数查询：实时获取触摸点数量
- 手势识别：支持上滑、下滑、左滑、右滑手势检测
- 芯片 ID 验证：初始化时可选校验芯片 ID
- 中断驱动模式：通过 IRQ 引脚实现触摸事件通知（ISR-safe）
- 硬件复位：支持通过复位引脚进行硬件复位
- 依赖注入设计：I2C 总线实例外部传入，不内部创建

## 硬件要求

**推荐测试硬件**：

| 硬件 | 说明 |
|------|------|
| FT6336/FT6336U 触摸面板 | 电容触摸控制器 |
| 支持 I2C 的 MicroPython 开发板 | ESP32 / RP2040 / RP2350 等 |

**引脚说明**：

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线 |
| SDA | I2C 数据线 |
| RST | 复位引脚（可选） |
| INT | 中断引脚（可选） |

## 软件环境

- MicroPython 固件版本：v1.23.0 及以上
- 驱动版本：v0.1.0
- 依赖库：无外部依赖（仅使用 MicroPython 内置模块 `machine`、`time`、`micropython`）

## 文件结构

```
├── code/
│   ├── ft6336.py   # 核心驱动
│   └── main.py     # 测试示例
├── README.md       # 说明文档
└── package.json    # 包配置文件
```

## 文件说明

- `code/ft6336.py`：FT6336/FT6336U 电容触摸控制器驱动类，提供触摸坐标读取、手势识别、芯片 ID 验证等全部功能
- `code/main.py`：驱动测试示例，演示 I2C 初始化、设备扫描、芯片 ID 验证及触摸轮询

## 快速开始

1. **复制文件**：将 `code/ft6336.py` 和 `code/main.py` 上传至 MicroPython 设备的 `/` 目录

2. **接线**：按下表连接 FT6336 触摸面板与控制板

   | FT6336 引脚 | 控制板引脚 |
   |-------------|-----------|
   | VCC | 3.3V |
   | GND | GND |
   | SCL | GPIO 22 |
   | SDA | GPIO 21 |
   | RST | GPIO 25 |
   | INT | GPIO 26 |

3. **运行测试**：通过 REPL 或 IDE 执行 `main.py`

```python
# 最小可运行示例
from machine import I2C, Pin
from ft6336 import FT6336

# 初始化 I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 初始化驱动（不验证芯片ID、不使用中断）
touch = FT6336(i2c)

# 读取触摸点
point = touch.read_point()
if point is not None:
    print("x=%d, y=%d, points=%d" % (point["x"], point["y"], point["points"]))
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作条件 | 工作电压 3.3V，I2C 通信速率建议 100kHz-400kHz |
| I2C 地址 | 默认 I2C 地址为 0x38（7位地址），芯片 ID 期望值为 0x64 |
| 多点触控 | 当前仅读取 touch1 数据，多点触控扩展待完成 |
| 中断模式 | 若使用 IRQ 引脚，中断处理函数为 ISR-safe（仅设置标志位） |
| 手势识别 | 需先调用 enable_gesture(True) 启用后才能读取手势代码 |
| 静态检查 | 驱动仅静态检查通过，未硬件验证，使用前请在实际硬件上测试 |
| 许可协议 | 源自 Waveshare Apache-2.0 参考实现，本驱动保持 Apache-2.0 许可 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-07-23 | FreakStudio | 初始版本（规范化改写，仅静态检查通过） |

## 联系方式

- 邮箱：FreakStudio@163.com
- GitHub：[GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

Apache License 2.0

Copyright (c) 2026 FreakStudio

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
