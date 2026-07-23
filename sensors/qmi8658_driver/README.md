# QMI8658 / QMI8658C MicroPython 驱动

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

本驱动为 QMI8658/QMI8658C 六轴惯性测量单元 (IMU) 提供 MicroPython 接口。支持三轴加速度计和三轴陀螺仪的原始数据与物理单位读取，适用于姿态检测、运动追踪、振动监测等场景。驱动基于 I2C 通信协议，默认配置为加速度 8g 量程、陀螺仪 512dps 量程、1000Hz 采样率。

> **注意**：仅静态检查通过，未硬件验证。

## 主要功能

- 读取加速度计和陀螺仪原始数据（有符号 16 位整数）
- 原始数据自动转换为物理单位（g 和 dps）
- 芯片 ID 与版本号查询
- 硬件复位支持（可选复位引脚）
- 自动 WHO_AM_I 验证确保设备正确连接
- 纯 MicroPython 实现，无外部依赖
- 默认即用配置（开箱即可采集数据）
- 支持调试日志开关，方便开发排查

## 硬件要求

### 推荐测试硬件

- 搭载 QMI8658 或 QMI8658C 芯片的开发板（如 Waveshare RP2350-Touch-LCD-3.5）
- 支持 I2C 的 MicroPython 微控制器（ESP32 / RP2040 / RP2350 等）

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| RST  | 复位引脚（可选，低电平复位） |

## 软件环境

| 项目 | 版本要求 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.1.0 |
| 依赖库 | 无（仅需 MicroPython 内置模块 `machine`、`time`、`micropython`） |

## 文件结构

```
├── code/
│   ├── qmi8658.py    # QMI8658 核心驱动
│   └── main.py       # 测试示例代码
├── package.json      # MIP 包配置文件
└── README.md         # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/qmi8658.py` | QMI8658/QMI8658C 六轴 IMU 驱动类，提供数据读取、配置、复位等完整功能 |
| `code/main.py` | 驱动测试示例，演示 I2C 初始化、设备扫描、数据采集与格式化输出 |
| `package.json` | MIP 包配置，用于 `mip.install()` 一键安装 |
| `README.md` | 本说明文档 |

## 快速开始

### 1. 将驱动文件复制到设备

使用 mpremote 或 Thonny 将 `code/qmi8658.py` 和 `code/main.py` 上传到 MicroPython 设备。

### 2. 硬件接线

| QMI8658 模块 | 微控制器 |
|-------------|----------|
| VCC         | 3.3V     |
| GND         | GND      |
| SCL         | GPIO22   |
| SDA         | GPIO21   |
| RST         | 可选     |

默认代码使用 ESP32 的 I2C0（SCL=GPIO22, SDA=GPIO21），请根据实际硬件修改 `main.py` 中的 `SCL_PIN` 和 `SDA_PIN`。

### 3. 运行测试

```python
from machine import I2C, Pin
from qmi8658 import QMI8658

# 初始化 I2C 总线（根据实际接线修改引脚号）
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建驱动实例
imu = QMI8658(i2c)

# 读取芯片信息
print("WHO_AM_I: 0x%02X" % imu.who_am_i())
print("Revision: 0x%02X" % imu.revision())

# 读取并打印六轴数据
raw = imu.read_raw()
print("Raw: ax=%d ay=%d az=%d gx=%d gy=%d gz=%d" % raw)

xyz = imu.read_xyz()
print("Cvt: ax=%.3f ay=%.3f az=%.3f gx=%.2f gy=%.2f gz=%.2f" % xyz)

# 释放资源
imu.deinit()
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 3.3V |
| 通信接口 | I2C |
| 默认 I2C 地址 | 0x6B (AD0 接 GND) |
| 芯片 ID (WHO_AM_I) | 0x05 |

### 测量范围

| 传感器 | 量程 | 灵敏度 |
|--------|------|--------|
| 加速度计 | 8g | 1/4096 g/LSB |
| 陀螺仪 | 512 dps | 1/64.0 dps/LSB |

### 使用限制

- 本驱动基于 Waveshare 示例改写，默认配置适用于该示例硬件；使用其他硬件时可能需要调整寄存器配置
- 仅静态检查通过，未在真实硬件上验证
- QMI8658C 兼容性需硬件确认 WHO_AM_I 和量程配置
- 不支持 SPI 接口（仅支持 I2C）
- 当前版本仅提供默认配置，不支持动态修改量程和采样率

### 兼容性提示

- 参考代码来源：[Waveshare RP2350-Touch-LCD-3.5 IMU 示例](https://github.com/waveshareteam/RP2350-Touch-LCD-3.5)
- 许可协议与上游保持一致（Apache-2.0）

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-07-23 | FreakStudio | 初始版本，基于 Waveshare Apache-2.0 示例规范化改写 |

## 联系方式

- GitHub: [FreakStudioCN/GraftSense-Drivers-MicroPython#](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython#)

## 许可协议

Apache License 2.0

Copyright 2026 FreakStudio

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
