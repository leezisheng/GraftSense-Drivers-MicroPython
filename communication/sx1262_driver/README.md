# SX1262 LoRa Radio Transceiver MicroPython Driver

## 目录

1. [简介](#简介)
2. [主要功能](#主要功能)
3. [硬件要求](#硬件要求)
4. [软件环境](#软件环境)
5. [文件结构](#文件结构)
6. [文件说明](#文件说明)
7. [快速开始](#快速开始)
8. [注意事项](#注意事项)
9. [版本记录](#版本记录)
10. [联系方式](#联系方式)
11. [许可协议](#许可协议)

## 简介

This is a MicroPython driver for the Semtech SX1262 LoRa radio transceiver chip. It supports both LoRa and GFSK (FSK) modulation modes, providing long-range, low-power wireless communication for IoT applications. The driver features both blocking (synchronous) and non-blocking (callback-based) operation modes.

## 主要功能

- Dual modulation support: LoRa and GFSK (FSK)
- Blocking and non-blocking (IRQ callback) modes
- Cross-platform support: MicroPython and CircuitPython
- Configurable frequency (150-960 MHz), bandwidth, spreading factor, coding rate
- TX power control (-9 to +22 dBm)
- CRC error detection
- GFSK address filtering (node and broadcast)
- Data whitening for GFSK mode
- Channel Activity Detection (CAD) for LoRa
- RSSI and SNR measurement
- TCXO voltage control
- LDO/DC-DC regulator selection
- Duty-cycle receive mode for low-power operation

## 硬件要求

### 推荐测试硬件

| Item | Description |
|------|-------------|
| MCU Board | ESP32, ESP8266, Raspberry Pi Pico (RP2040), or any MicroPython-compatible board |
| SX1262 Module | SX1262-based LoRa module (e.g., E22-900M30S, E22-400M30S) |
| Antenna | Matching frequency antenna (433MHz or 868/915MHz) |
| Power Supply | 3.3V capable of 100mA+ (TX peak) |

### 引脚连接表

| SX1262 Pin | MCU Pin (ESP32 example) | Description |
|------------|------------------------|-------------|
| VCC        | 3.3V                   | Power supply |
| GND        | GND                    | Ground |
| SCK        | GPIO 5                 | SPI clock |
| MOSI       | GPIO 27                | SPI MOSI (Master Out Slave In) |
| MISO       | GPIO 19                | SPI MISO (Master In Slave Out) |
| NSS/CS     | GPIO 18                | SPI chip select |
| DIO1/IRQ   | GPIO 26                | Interrupt request |
| RST        | GPIO 14                | Reset |
| BUSY/GPIO  | GPIO 33                | Busy status indicator |

> Note: Pin numbers can be changed in `main.py` to match your wiring.

## 软件环境

| Requirement | Version / Details |
|-------------|-------------------|
| MicroPython Firmware | v1.23.0 or later |
| Driver Version | v1.0.0 |
| Dependencies | None (uses only MicroPython built-in modules: `machine`, `utime`, `sys`) |

## 文件结构

```
├── sx1262.py          # Main SX1262 driver (LoRa radio with high-level API)
├── sx126x.py          # SX126X base class (SPI communication, register access)
├── _sx126x.py         # Internal constants, error codes, and helper functions
├── main.py            # Test example program
└── README.md          # Documentation
```

## 文件说明

| File | Purpose |
|------|---------|
| `sx1262.py` | Main driver class `SX1262` - provides high-level LoRa/GFSK API: `begin()`, `beginFSK()`, `send()`, `recv()`, `setFrequency()`, `setOutputPower()` |
| `sx126x.py` | Base class `SX126X` - handles low-level SPI communication, register read/write, modulation parameter configuration for both LoRa and GFSK |
| `_sx126x.py` | Shared internal module - defines all command opcodes, register addresses, error codes, status constants, and the `ASSERT`/`yield_` helper functions |
| `main.py` | Test program demonstrating LoRa initialization, packet transmission, and reception with proper error handling and resource cleanup |

## 快速开始

1. Copy all `.py` files to your MicroPython device.
2. Wire the SX1262 module according to the pin table above.
3. Power on the device and connect via serial terminal.

### 最小代码示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : jgromes
# @File    : main.py
# @Description : Test SX1262 LoRa driver class
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from sx1262 import SX1262

# ======================================== 全局变量 ============================================
# 测试用的 LoRa 默认参数
# 测试频率（MHz）
TEST_FREQ = 434.0
# 测试带宽（kHz）
TEST_BW = 125.0
# 测试扩频因子
TEST_SF = 9
# 测试编码率
TEST_CR = 7
# 测试发射功率（dBm）
TEST_POWER = 14
# 测试前导码长度
TEST_PREAMBLE = 8
# 接收超时（ms）
TEST_TIMEOUT_MS = 3000
# 测试数据包
TEST_PACKET = b"Hello SX1262!"

last_print_time = time.ticks_ms()
# 打印间隔（ms）
print_interval = 3000

# ======================================== 功能函数 ============================================
def print_device_info():
    """打印设备状态信息"""
    try:
        rssi = device.getRSSI()
        print("RSSI: %.1f dBm" % rssi)
    except Exception:
        print("RSSI: N/A")

def test_receive():
    """接收测试（高频，默认注释调用，可 REPL 手动调用）"""
    data, status = device.recv(0, timeout_en=True, timeout_ms=TEST_TIMEOUT_MS)
    # ERR_NONE：成功
    if status == device.STATUS[0]:
        print("Received: %s (len=%d)" % (data, len(data)))
    # ERR_CRC_MISMATCH：CRC 校验失败
    elif status == device.STATUS[-7]:
        print("Received with CRC error: %s" % data)
    else:
        print("Receive status: %s" % device.STATUS.get(status, str(status)))
    return data, status

def test_send(data):
    """发送测试（模式切换，默认注释调用，可 REPL 手动触发）"""
    sent_len, status = device.send(data)
    print("Sent %d bytes, status: %s" % (sent_len, device.STATUS.get(status, str(status))))
    return sent_len, status

# ======================================== 自定义类 ============================================
# (无: 使用 SX1262 类)

# ======================================== 初始化配置 ==========================================
time.sleep(3)

print("FreakStudio: Testing SX1262 LoRa driver")

# SPI 硬件引脚配置（以 ESP32 为例，请根据实际接线修改）
# SPI 总线编号
SPI_BUS = 1
# SPI 时钟引脚
PIN_SCK = 5
# SPI MOSI 数据引脚
PIN_MOSI = 27
# SPI MISO 数据引脚
PIN_MISO = 19
# 片选引脚
PIN_CS = 18
# 中断请求引脚（DIO1）
PIN_IRQ = 26
# 复位引脚
PIN_RST = 14
# 忙状态监测引脚
PIN_GPIO = 33

print("Initializing SX1262...")
print("  SPI bus: %d" % SPI_BUS)
print("  Pins: SCK=%d MOSI=%d MISO=%d CS=%d IRQ=%d RST=%d GPIO=%d" %
      (PIN_SCK, PIN_MOSI, PIN_MISO, PIN_CS, PIN_IRQ, PIN_RST, PIN_GPIO))

# 创建驱动实例（基类内部完成 SPI/Pin 初始化）
device = SX1262(SPI_BUS, PIN_SCK, PIN_MOSI, PIN_MISO, PIN_CS, PIN_IRQ, PIN_RST, PIN_GPIO)

print("Configuring LoRa mode (freq=%.1f MHz, bw=%.1f kHz, sf=%d, cr=%d)..." %
      (TEST_FREQ, TEST_BW, TEST_SF, TEST_CR))

# 初始化 LoRa 模式
state = device.begin(
    freq=TEST_FREQ,
    bw=TEST_BW,
    sf=TEST_SF,
    cr=TEST_CR,
    power=TEST_POWER,
    preambleLength=TEST_PREAMBLE,
    # 阻塞模式测试
    blocking=True,
    useRegulatorLDO=False
)

if state == 0:
    print("SX1262 initialization successful!")
else:
    raise RuntimeError(
        "SX1262 initialization failed, status: %s"
        % device.STATUS.get(state, str(state))
    )

print_device_info()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频查询：自动执行发送测试数据包
            print("\n--- Sending test packet ---")
            test_send(TEST_PACKET)

            # 短暂等待后尝试接收回应
            time.sleep_ms(100)
            print("--- Listening for response ---")
            test_receive()

            last_print_time = current_time

        # 高频发送，注释默认执行，可 REPL 手动调用
        # test_send(TEST_PACKET)
        # 高频状态查询，注释默认执行，可 REPL 手动调用
        # print_device_info()

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        device.deinit()
    except Exception:
        pass
    del device
    print("Program exited")
```

## 注意事项

| Category | Details |
|----------|---------|
| Frequency Compliance | Ensure your operating frequency complies with local radio regulations (e.g., 433MHz, 868MHz, 915MHz ISM bands) |
| Antenna Required | Never transmit without a properly matched antenna connected - this can damage the RF output stage |
| Power Supply | SX1262 TX current can peak at 100mA+. Ensure adequate 3.3V supply with proper decoupling |
| SPI Speed | Default SPI baudrate is 2MHz. Do not exceed 10MHz for reliable operation |
| Frequency Range | Valid frequency range: 150.0 MHz to 960.0 MHz |
| TX Power Range | Valid output power: -9 dBm to +22 dBm |
| Spreading Factor | Valid SF range: 5 to 12 (LoRa mode) |
| Coding Rate | Valid CR range: 5 to 8 |
| Blocking vs Non-blocking | Blocking mode uses busy-wait loops; non-blocking mode requires IRQ callback setup |
| Cross-platform | Driver reports errors via status codes, not exceptions (except parameter validation in main driver) |
| Base Class Hardware | SPI and Pin objects are created in the SX126X base class (aux file). The main SX1262 class accepts pin/bus IDs and passes them through |

## 版本记录

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0.0 | 2026-07-19 | jgromes | Initial normalized version with bilingual docstrings, type annotations, parameter validation, deinit() method, debug logging |

## 联系方式

- GitHub: [GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)
- Email: support@freakstudio.cn

## 许可协议

MIT License

Copyright (c) 2026 jgromes

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
