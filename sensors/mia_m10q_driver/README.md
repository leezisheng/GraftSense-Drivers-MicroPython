# MIA-M10Q MicroPython 驱动

## 简介

MIA-M10Q 是 u-blox 的微型 GNSS 模块，通过 UART 输出标准 NMEA 语句。本驱动提供一个轻量级 NMEA 句子解析器，逐字符解析 NMEA 数据并提取时间、经纬度、速度、高度、卫星信息等 GPS 定位数据。

**重要说明：本驱动仅支持 NMEA 协议，不是完整的 u-blox UBX 二进制协议驱动。** 不支持通过 UBX 命令配置模块参数（如更新率、星座选择等）。如需 UBX 配置功能，请使用 u-blox 官方工具（u-center）预先配置模块。

## 主要功能

- 逐字符解析 NMEA 句子（RMC、GGA、VTG、GSA、GSV、GLL）
- CRC 校验和错误统计
- 坐标格式化输出（度分/度分秒/十进制度）
- 速度输出（节/mph/km/h）
- 日期/时间输出（支持时区偏移）
- 罗盘方向计算
- 卫星可见性和使用状态跟踪
- 原始数据日志记录
- UART 超时检测

## 硬件要求

- MIA-M10Q GNSS 模块（或其他标准 NMEA 输出 GPS 模块）
- MCU 支持 MicroPython UART 接口（ESP32、RP2040 等）
- UART 连接（默认 9600 波特率）：TX 接 MCU RX，RX 接 MCU TX

## 软件环境

- MicroPython v1.23 或更高版本
- `machine.UART` 和 `machine.Pin` 模块
- 兼容标准 Python 3（非 MicroPython 环境下使用 `time.time()` 替代 `utime`）

## 文件结构

```
mia_m10q_driver/
├── code/
│   ├── mia_m10q.py        # NMEA 解析驱动文件
│   └── main.py            # UART 读取测试示例
├── package.json           # 包描述文件
├── README.md              # 本文件
└── LICENSE                # MIT 许可证
```

## 文件说明

- `mia_m10q.py`：NMEA GPS 句子解析器，逐字符输入解析，不包含任何 UART 读写操作，兼容 MicroPython 和标准 Python
- `main.py`：UART 读取测试示例，演示 NMEA 数据接收、解析和格式化输出

## 快速开始

```python
from machine import Pin, UART
from mia_m10q import MicropyGPS

# 初始化 UART / Initialize UART
uart = UART(1, baudrate=9600, tx=Pin(17), rx=Pin(16))

# 创建解析器实例 / Create parser instance
gps = MicropyGPS(local_offset=8)

# 读取并解析 NMEA 数据 / Read and parse NMEA data
while True:
    if uart.any():
        data = uart.read()
        if data:
            for byte in data:
                gps.update(chr(byte))
    print(gps.latitude_string(), gps.longitude_string())
    print("Speed:", gps.speed_string('kph'))
```

## 注意事项

- **本驱动仅支持 NMEA 协议，不是完整的 u-blox UBX 二进制协议驱动**
- 模块默认以 9600 波特率输出 NMEA 语句，若已通过 u-center 修改波特率请在初始化时相应调整
- 冷启动首次定位可能需要 30 秒以上，室外开阔天空环境下定位更快
- UART 读取和超时控制由调用方在 main.py 中实现，驱动类本身不执行 I/O 操作
- 本驱动来源于 `micropyGPS` 开源项目，已针对 GraftSense 规范进行标准化

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 0.1.0 | 2017 | 初始版本（Michael Calvin McCoy） |
| 1.0.0 | 2026-07-19 | 规范化版本（FreakStudio） |

## 联系方式

- 原作者：Michael Calvin McCoy (calvin.mccoy@protonmail.com)
- 维护者：FreakStudio

## 许可协议

MIT License - 详见 LICENSE 文件
