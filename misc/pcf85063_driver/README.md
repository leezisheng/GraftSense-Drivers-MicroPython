# PCF85063/PCF85063ATL RTC MicroPython 驱动

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

本驱动为 NXP PCF85063 / PCF85063ATL 低功耗 I2C RTC 芯片提供 MicroPython 驱动封装。支持时间读写、闹钟配置和中断输出控制等核心功能，接口兼容 MicroPython 原生的 `machine.RTC` 风格。适用于需要低功耗精确计时的嵌入式项目，如数据记录器、定时唤醒设备和电池供电系统。

本驱动仅静态检查通过，未硬件验证。This driver has passed static checks only, not hardware verified.

## 主要功能

- 完整的时间读写：年、月、日、星期、时、分、秒
- 兼容 `machine.RTC.datetime()` 接口：支持元组格式获取/设置日期时间
- BCD 格式自动转换：内部寄存器 BCD 编码与十进制之间透明转换
- 可配置年份基准偏移（year_base）：灵活适配不同时间基准需求（如 year_base=2000 可使寄存器支持至 2100+ 年）
- 闹钟功能：按秒/分/时/日/星期独立配置匹配条件，支持闹钟中断输出
- 软件复位：通过 CTRL1 寄存器执行软复位，恢复寄存器默认值
- 参数校验：构造参数和 API 输入均有类型和范围校验
- 调试日志开关：通过 `debug` 参数控制调试输出，生产环境零开销
- I2C 通信重试机制：瞬时通信故障自动重试（可配置次数和间隔）
- 资源安全释放：`deinit()` 自动禁用闹钟中断并清除硬件引用

## 硬件要求

### 推荐测试硬件

- PCF85063 或 PCF85063ATL RTC 模块（I2C 接口，地址 0x51）

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.8V - 5.5V，典型 3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（需上拉电阻） |
| SDA  | I2C 数据线（需上拉电阻） |
| INT  | 闹钟中断输出（开漏，需上拉，可选） |

## 软件环境

- MicroPython 固件版本：v1.23.0 及以上
- 驱动版本：v0.1.0
- 依赖库：无外部依赖（仅使用标准 MicroPython 库 `machine`、`time`、`micropython`）

## 文件结构

```
├── code/
│   ├── pcf85063.py      # 核心驱动文件
│   └── main.py           # 测试示例程序
├── package.json          # 包配置文件
└── README.md             # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/pcf85063.py` | PCF85063 RTC 核心驱动，封装 I2C 通信、时间读写、闹钟配置等功能 |
| `code/main.py` | 测试示例程序，演示 I2C 初始化、设备扫描、时间读写和闹钟配置 |
| `package.json` | mip 包配置文件，用于通过 upypi 或 mip 安装驱动 |
| `README.md` | 驱动说明文档（本文件） |

## 快速开始

### 步骤一：复制文件

将 `code/pcf85063.py` 复制到 MicroPython 设备的文件系统中。

### 步骤二：接线

按硬件要求中的引脚连接表，将 PCF85063 模块连接到 MCU 的 I2C 引脚。

### 步骤三：运行测试

将 `code/main.py` 的内容复制到设备上运行，或通过以下最小代码快速验证：

```python
from machine import I2C, Pin
from pcf85063 import PCF85063

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建 RTC 驱动实例
rtc = PCF85063(i2c)

# 软件复位
rtc.reset()

# 设置时间：(year, month, day, weekday, hour, minute, second)
rtc.set_datetime((2026, 7, 23, 4, 12, 0, 0))

# 读取并打印时间
dt = rtc.read_datetime()
print("Current: %04d-%02d-%02d %02d:%02d:%02d" % dt[:6])

# 释放资源
rtc.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | 默认地址 0x51，可通过 `address` 参数修改 |
| BCD 格式 | 寄存器以 BCD 编码存储时间值，驱动通过 `bcd_to_dec()`/`dec_to_bcd()` 自动转换，用户无需关心 |
| year_base 配置 | 年份在寄存器中存储为（实际年份 - year_base），默认 year_base=1970。若年份范围为 2000-2099，可设 year_base=2000 使寄存器仅存储低 2 位值，延长有效范围。读取时驱动自动加上 year_base |
| 闹钟禁用 | 各闹钟字段默认值为 `ALARM_DISABLE(0x80)`，表示该字段不参与匹配。设为有效范围值（如秒 0-59）则启用匹配 |
| 闹钟中断 | 配置闹钟后需调用 `enable_alarm_interrupt(True)` 才会在 INT 引脚输出中断信号；`deinit()` 会自动禁用 |
| 软件复位 | `reset()` 写入 CTRL1 寄存器触发软复位，所有时间/闹钟寄存器恢复默认值 |
| 验证状态 | 本驱动仅静态检查通过，未硬件验证 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-07-23 | FreakStudio | 初始版本，支持时间读写、闹钟配置、year_base 偏移 |

## 联系方式

- GitHub: [FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright (c) 2026 FreakStudio

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
