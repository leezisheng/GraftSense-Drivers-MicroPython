# ATECC608A/ATECC508A Crypto Authentication MicroPython Driver

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

This is a MicroPython driver for the Microchip ATECC608A and ATECC508A crypto authentication chips. It provides a complete I2C communication layer and wraps the full CryptoAuthLib command set, enabling secure key storage, ECDSA sign/verify, ECDH key agreement, SHA-256 hashing, random number generation, and configuration zone management for IoT security applications.

## 主要功能

- Full CryptoAuthLib API support: CheckMAC, Counter, DeriveKey, ECDH, GenDig, GenKey, Info, Lock, Nonce, Random, Read, SHA, Sign, Verify, Write, SelfTest, and more
- Automatic chip detection: ATECC508A vs ATECC608A
- I2C communication with built-in retry mechanism for transient errors
- CRC-16 verification with Viper-native acceleration fallback
- Comprehensive custom exception hierarchy (30+ error types) mapped to device status codes
- Singleton status code lookup module for memory efficiency
- Configuration zone parser with slot/key config decoding (uctypes bitfield)
- Watchdog-aware execution: auto-sleep before watchdog expiry
- Dependency injection: accepts external I2C bus instance for flexible hardware setup
- Debug logging support via `debug` parameter

## 硬件要求

### 推荐测试硬件

| Item | Description |
|------|-------------|
| MCU Board | ESP32, ESP8266, Raspberry Pi Pico (RP2040), or any MicroPython-compatible board |
| ATECC608A Module | Microchip ATECC608A breakout board (e.g., SparkFun Crypto Shield, Adafruit ATECC608) |
| ATECC508A Module | Microchip ATECC508A breakout board (alternative, subset of features) |
| Power Supply | 3.3V capable of 50mA+ |

### 引脚连接表

| ATECC608A Pin | MCU Pin (ESP32 example) | Description |
|---------------|------------------------|-------------|
| VCC           | 3.3V                   | Power supply |
| GND           | GND                    | Ground |
| SCL           | GPIO 22                | I2C clock line |
| SDA           | GPIO 21                | I2C data line |

> Note: Pin numbers can be changed in `main.py` to match your wiring.

## 软件环境

| Requirement | Version / Details |
|-------------|-------------------|
| MicroPython Firmware | v1.23.0 or later |
| Driver Version | v1.0.0 |
| Dependencies | None (uses only MicroPython built-in modules: `machine`, `micropython`, `uctypes`, `ustruct`, `uhashlib`, `ubinascii`, `utime`, `sys`) |

## 文件结构

```
├── atecc608a.py       # Main I2C driver class (ATECCX08A)
├── basic.py           # CryptoAuthLib API command wrappers (ATECCBasic base class)
├── constant.py        # Command opcodes, config masks, timing tables (singleton)
├── exceptions.py      # Custom exception hierarchy (30+ error types)
├── host.py            # Host-side SHA-256 helper (atcah_sha256)
├── packet.py          # Command packet serialization and CRC-16 (viper-optimized)
├── status.py          # Status code constants and error lookup (singleton)
├── util.py            # Configuration zone dump utilities (slot/key config parsing)
├── main.py            # Test example program
└── README.md          # Documentation
```

## 文件说明

| File | Purpose |
|------|---------|
| `atecc608a.py` | Main driver class `ATECCX08A` (alias `ATECC608A`) -- provides I2C wake/idle/sleep/execute with retry, device auto-detection, and deinit resource cleanup |
| `basic.py` | Base class `ATECCBasic` -- implements all CryptoAuthLib command wrappers: `atcab_info()`, `atcab_read_serial_number()`, `atcab_random()`, `atcab_sha()`, `atcab_genkey()`, `atcab_sign()`, `atcab_verify()`, `atcab_ecdh()`, `atcab_read_config_zone()`, `atcab_is_locked()`, `atcab_selftest()`, and 60+ more |
| `constant.py` | Singleton class `C` -- dynamically returns `micropython.const()` values for all command opcodes, parameter modes, I2C timing, zone/slot addresses, and execution time tables |
| `exceptions.py` | Complete exception hierarchy rooted at `CryptoError` -- includes `CheckmacVerifyFailedError`, `ParseError`, `EccFaultError`, `ExecutionError`, `WatchDogAboutToExpireError`, `NoDevicesFoundError`, `UnsupportedDeviceError`, and 25+ more |
| `host.py` | Host-side SHA-256 helper `atcah_sha256()` -- wraps `uhashlib.sha256().digest()` for pre-computation before sending to chip |
| `packet.py` | `ATCAPacket` class -- serializes command packets with CRC-16 via `micropython.viper` accelerated computation, exposes request/response data buffers and execution delay lookup |
| `status.py` | Singleton class `S` -- maps all ATCA status codes to `micropython.const()` values and provides `decode_error()` that returns `(status_code, exception_class)` pairs |
| `util.py` | Configuration dump utilities -- `dump_slot()`, `dump_key()`, `dump_configuration()` parse and pretty-print the 128-byte config zone using `uctypes` bitfield structures |
| `main.py` | Test program demonstrating I2C scan, device detection, serial number read, lock status check, random number generation, and SHA-256 hashing with proper exception handling and cleanup |

## 快速开始

1. Copy all `.py` files to your MicroPython device.
2. Wire the ATECC608A module according to the pin table above.
3. Power on the device and connect via serial terminal.

### 最小代码示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 ATECC608A 加密认证芯片驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import machine
import time
import ubinascii
from atecc608a import ATECC608A

# ======================================== 全局变量 ============================================

# I2C 硬件引脚配置（ESP32 示例，可按实际接线修改）
I2C_BUS = 0
PIN_SCL = 22
PIN_SDA = 21
I2C_FREQ = 1000000

# ATECC608A I2C 默认地址
DEVICE_ADDR = 0x60

# ATECC608A 设备类型标识字节（位于 info 响应字节 3）
ATCAB_INFO_DEVTYPE_INDEX = 3
ATCAB_INFO_DEVTYPE_ECC608A = 0x60

# 测试数据包
TEST_DATA = b"Hello ATECC608A!"

# 定时打印间隔（ms）
last_print_time = time.ticks_ms()
print_interval = 3000

# ======================================== 功能函数 ============================================

def test_device_info(device):
    """打印设备信息（低频，保留自动执行）"""
    try:
        # 读取设备信息（revision 模式）
        info = device.atcab_info().response_data
        rev = ubinascii.hexlify(info)
        print("Device info: %s" % rev)
    except Exception as e:
        print("Failed to read device info: %s" % str(e))


def test_serial_number(device):
    """打印芯片序列号（低频，保留自动执行）"""
    try:
        # 读取序列号（config zone 前 32 字节含 SN）
        sn_packet = device.atcab_read_serial_number()
        sn = ubinascii.hexlify(sn_packet.response_data)
        print("Serial number: %s" % sn)
    except Exception as e:
        print("Failed to read serial number: %s" % str(e))


def test_random(device):
    """生成随机数（高频，默认注释调用，可 REPL 手动调用）"""
    try:
        rnd_packet = device.atcab_random()
        rnd = ubinascii.hexlify(rnd_packet.response_data)
        print("Random: %s" % rnd)
    except Exception as e:
        print("Failed to generate random: %s" % str(e))


def test_sha256(device, data: bytes = TEST_DATA):
    """SHA-256 计算（高频，默认注释调用，可 REPL 手动调用）"""
    try:
        sha_packet = device.atcab_sha(data)
        # SHA 响应数据包含 32 字节摘要
        digest = ubinascii.hexlify(sha_packet.response_data)
        print("SHA-256: %s" % digest)
    except Exception as e:
        print("Failed to compute SHA-256: %s" % str(e))


def test_read_config_zone(device):
    """读取配置区数据（低频，默认注释调用，可 REPL 手动调用）"""
    try:
        config_packet = device.atcab_read_config_zone()
        config = ubinascii.hexlify(config_packet.response_data)
        print("Config zone: %s" % config)
    except Exception as e:
        print("Failed to read config zone: %s" % str(e))


def test_check_lock_status(device):
    """检查各区锁定状态（低频，保留自动执行）"""
    try:
        # 检查配置区是否已锁定
        config_locked = device.atcab_is_locked("config")
        print("Config zone locked: %s" % config_locked)
        # 检查数据区是否已锁定
        data_locked = device.atcab_is_locked("data")
        print("Data zone locked: %s" % data_locked)
    except Exception as e:
        print("Failed to check lock status: %s" % str(e))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Testing ATECC608A crypto driver")

# 初始化 I2C 总线
print("Initializing I2C bus %d (SCL=%d, SDA=%d, freq=%d)..." %
      (I2C_BUS, PIN_SCL, PIN_SDA, I2C_FREQ))
i2c = machine.I2C(I2C_BUS, scl=machine.Pin(PIN_SCL), sda=machine.Pin(PIN_SDA),
                   freq=I2C_FREQ)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

# 检查是否未找到任何设备
if not devices:
    raise RuntimeError("No I2C device found")

# 检查目标地址设备是否存在
if DEVICE_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02x" % DEVICE_ADDR)

# 创建 ATECC608A 驱动实例
print("Initializing ATECC608A at address 0x%02x..." % DEVICE_ADDR)
device = ATECC608A(bus=i2c, address=DEVICE_ADDR, debug=False)
print("Device type: %s" % device.device)

# 验证设备类型
info_data = device.atcab_info().response_data
dev_type = info_data[ATCAB_INFO_DEVTYPE_INDEX]
if dev_type == ATCAB_INFO_DEVTYPE_ECC608A:
    print("Device verification: ATECC608A confirmed")
else:
    print("Device verification: unknown type 0x%02x" % dev_type)

# 版本信息
print("CryptoAuthLib version: %s" % device.atcab_version())

print("ATECC608A initialization successful!")

# ========================================  主程序  ===========================================

try:
    # 启动测试：读取设备信息和序列号
    print("\n--- Device Identification ---")
    test_device_info(device)
    test_serial_number(device)

    # 检查锁定状态
    print("\n--- Lock Status ---")
    test_check_lock_status(device)

    main_loop_count = 0
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            main_loop_count += 1
            print("\n--- Main loop #%d ---" % main_loop_count)

            # 低频自动执行：随机数生成
            print("Generating random number...")
            test_random(device)

            # 低频自动执行：SHA-256 测试
            print("Computing SHA-256...")
            test_sha256(device)

            # 配置区读取（数据量大，默认注释，可 REPL 手动调用）
            # test_read_config_zone(device)

            last_print_time = current_time

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
| I2C Address | Default I2C address is 0x60 (7-bit). Address can be changed in device configuration |
| I2C Speed | Valid I2C frequency range: 100kHz to 1MHz. Default 1MHz |
| Wakeup Delay | After `wake()`, wait at least 150us (tWHI + tWLO) before communication |
| ATECC508A Limitations | Some commands (SelfTest, KDF, SecureBoot) are ATECC608A-only and will raise `UnsupportedDeviceError` on ATECC508A |
| Config Zone | Config zone is 128 bytes and contains slot/key configurations, serial number, and lock status. Write only before locking |
| Locking | Once a zone is locked, it becomes read-only. Lock operations are irreversible |
| Watchdog | Commands have a maximum execution time. If watchdog is about to expire, driver auto-sleeps to reset |
| Retry | Default 20 retries for transient I2C errors. Adjust with `retries` parameter |
| Singleton Modules | `constant.py` and `status.py` use `sys.modules[__name__] = Class()` to replace the module with a singleton instance. They are imported as `import constant as ATCA_CONSTANTS` and `import status as ATCA_STATUS` -- do not attempt to instantiate them |
| Viper CRC | `packet.py` uses `@micropython.viper` for CRC-16 acceleration. A pure-Python fallback is provided in comments |
| Debug | Set `debug=True` in the driver constructor to see I2C communication logs |

## 版本记录

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0.0 | 2026-07-19 | stewedio | Initial normalized version with bilingual docstrings, type annotations, parameter validation, deinit() method, and multi-file architecture |

## 联系方式

- GitHub: [GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)
- Email: support@freakstudio.cn

## 许可协议

MIT License

Copyright (c) 2026 stewedio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
