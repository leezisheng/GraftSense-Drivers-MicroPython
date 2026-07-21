# AXP2101 MicroPython 驱动

## 简介

AXP2101 是高度集成的电源管理 IC (PMU)，适用于需要多路电源轨的嵌入式系统。本驱动提供完整的 I2C 寄存器级 API，支持 DCDC/LDO 控制、ADC 电压/温度采集、电池充电管理、中断配置和状态监控。

默认 I2C 地址：`0x34`，芯片 ID：`0x4A`。

## 主要功能

- 多路 DCDC 降压转换器控制（DCDC1~DCDC5）
- 多路 LDO 稳压器控制（ALDO1~ALDO4, BLDO1~BLDO2, CPUSLDO, DLDO1~DLDO2）
- 电池充电管理（预充电电流、恒流充电、目标电压、终止电流）
- ADC 模数采集（电池电压、系统电压、VBUS 电压、芯片温度、TS 引脚温度）
- 完整中断系统（使能/禁用/状态查询，覆盖电池、充电、温度、电源键等事件）
- 电源路径管理（VBUS 限压/限流、BATFET 控制、VSYS 电压阈值）
- 看门狗定时器
- 快速上电序列配置
- 数据缓冲区读写（4 字节）
- 电量计（Fuel Gauge）数据读写

## 硬件要求

- AXP2101 PMU 芯片
- MCU 支持 MicroPython I2C 接口（ESP32、RP2040 等）
- 4.7k 上拉电阻接 I2C SCL/SDA

### 电源轨

| 通道 | 类型 | 电压范围 | 步进 |
|---|---|---|---|
| DCDC1 | 降压 | 1500-3400 mV | 100 mV |
| DCDC2 | 降压 | 500-1540 mV | 10/20 mV |
| DCDC3 | 降压 | 500-3400 mV | 10/20/100 mV |
| DCDC4 | 降压 | 500-1840 mV | 10/20 mV |
| DCDC5 | 降压 | 1200/1400-3700 mV | 100 mV |
| ALDO1-4 | LDO | 500-3500 mV | 100 mV |
| BLDO1-2 | LDO | 500-3500 mV | 100 mV |
| CPUSLDO | LDO | 500-1400 mV | 50 mV |
| DLDO1-2 | LDO | 500-3400 mV | 100 mV |

### I2C 地址

| 地址 | 说明 |
|---|---|
| 0x34 | AXP2101 默认 7 位 I2C 地址 |

## 软件环境

- MicroPython v1.23 或更高版本
- `machine.I2C` 和 `machine.Pin` 模块

## 文件结构

```
axp2101_driver/
├── code/
│   ├── axp2101.py        # PMU 主驱动文件
│   ├── I2CInterface.py    # I2C 底层辅助类
│   └── main.py            # 功能测试示例
├── package.json           # 包描述文件
├── README.md              # 本文件
└── LICENSE                # MIT 许可证
```

## 文件说明

- `axp2101.py`：AXP2101 PMU 主驱动，继承自 I2CInterface，实现所有寄存器操作和功能 API
- `I2CInterface.py`：纯 MicroPython I2C 读写接口辅助类，提供位操作和多字节读取功能，无 CircuitPython/Adafruit 分支
- `main.py`：功能测试示例，演示 I2C 扫描、芯片 ID 验证、电池状态/电压/电量读取、充电状态、系统电压和温度读取

## 快速开始

```python
from machine import I2C, Pin
from axp2101 import AXP2101, AXP2101_SLAVE_ADDRESS

# 初始化 I2C 总线 / Initialize I2C bus
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建 PMU 实例 / Create PMU instance
pmu = AXP2101(i2c)

# 读取芯片 ID / Read chip ID
print("Chip ID: 0x%02X" % pmu.getChipID())

# 读取电池状态 / Read battery status
if pmu.isBatteryConnect():
    print("Battery: %d mV, %d%%" % (pmu.getBattVoltage(), pmu.getBatteryPercent()))

# 使能 DCDC1 / Enable DCDC1
pmu.enableDC1()
pmu.setDC1Voltage(3300)

# 释放资源 / Release resources
pmu.deinit()
```

## 注意事项

- 关机（`shutdown()`）、复位（`reset()`）和 BATFET 控制方法在真实硬件上需谨慎使用，可能导致系统掉电
- 驱动继承了 I2CInterface 的底层寄存器读写能力，所有寄存器操作通过基类方法完成
- 默认 I2C 地址为 0x34，若使用其他地址需在构造时传入 `addr` 参数
- 本驱动来源于 XPowersLib MicroPython，已针对 GraftSense 规范进行标准化

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 0.1.0 | 2022-10-20 | 初始版本（Lewis He） |
| 1.0.0 | 2026-07-19 | 规范化版本（FreakStudio） |

## 联系方式

- 原作者：Lewis He (lewishe@outlook.com)
- 维护者：FreakStudio

## 许可协议

MIT License - 详见 LICENSE 文件
