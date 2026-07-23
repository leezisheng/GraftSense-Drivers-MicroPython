# CST328 MicroPython Driver

## Table of Contents

- [Introduction](#introduction)
- [Main Features](#main-features)
- [Hardware Requirements](#hardware-requirements)
- [Software Environment](#software-environment)
- [File Structure](#file-structure)
- [File Descriptions](#file-descriptions)
- [Quick Start](#quick-start)
- [Notes](#notes)
- [Version History](#version-history)
- [Contact](#contact)
- [License](#license)

## Introduction

CST328 is an I2C capacitive touch controller driver for MicroPython. It supports single-point touch detection and coordinate reporting via I2C interface. The driver uses 16-bit register addressing for touch data access and supports optional interrupt-driven touch detection with ISR-safe internal handler or user-provided callback.

> **Note**: This driver has passed static code review only and has NOT been hardware verified.

## Main Features

- Single-point capacitive touch detection
- I2C communication with 16-bit register addressing support
- Optional interrupt pin support with ISR-safe internal handler
- External callback injection for custom interrupt handling
- Optional hardware reset pin support
- Automatic retry mechanism for transient I2C errors
- Debug logging support
- Configurable touch screen logical size
- Pure MicroPython implementation with no third-party dependencies

## Hardware Requirements

| Pin | Description |
|-----|-------------|
| VCC | Power supply (3.3V) |
| GND | Ground |
| SCL | I2C clock line |
| SDA | I2C data line |
| RST | Reset pin (optional) |
| INT | Interrupt pin (optional) |

Recommended test hardware:
- Any MicroPython-compatible board with I2C support (ESP32, RP2040, etc.)
- CST328 capacitive touch panel module
- Logic level converter (if necessary)

## Software Environment

| Item | Version / Requirement |
|------|-----------------------|
| MicroPython Firmware | v1.23.0 or later |
| Driver Version | v1.0.0 |
| Dependencies | None (pure MicroPython standard library) |

## File Structure

```
cst328_driver/
├── code/
│   ├── cst328.py        # Core driver
│   └── main.py           # Test example
├── package.json          # Package configuration
└── README.md             # Documentation
```

## File Descriptions

| File | Description |
|------|-------------|
| `code/cst328.py` | CST328 touch controller core driver, providing touch detection and coordinate reading |
| `code/main.py` | Complete test example demonstrating I2C initialization, device scanning, and touch polling |
| `package.json` | MicroPython package configuration for mip/upypi installation |

## Quick Start

1. Copy `code/cst328.py` and `code/main.py` to your MicroPython device.
2. Connect the CST328 module according to the pin table above.
3. Edit the pin definitions in `main.py` (`SCL_PIN`, `SDA_PIN`, `RST_PIN`, `IRQ_PIN`) to match your wiring.
4. Run `main.py`.

Minimum runnable code example:

```python
from machine import I2C, Pin
from cst328 import CST328

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
rst_pin = Pin(19, Pin.OUT)
irq_pin = Pin(18, Pin.IN)

touch = CST328(i2c, rst_pin=rst_pin, irq_pin=irq_pin, width=320, height=240)

while True:
    point = touch.read_point()
    if point is not None:
        print("Touch: x=%d, y=%d" % (point["x"], point["y"]))
```

## Notes

| Category | Description |
|----------|-------------|
| Operating Conditions | I2C voltage level must match the MCU (typically 3.3V); use a level converter if needed |
| Touch Range | Coordinate range is determined by the width/height parameters (default 320x240) |
| Initial State | CST328 may report a spurious touch event on power-up; it is recommended to discard the first reading |
| Interrupt Mode | When using interrupt mode, the driver only reads touch data when the interrupt flag is set, reducing I2C bus traffic |
| Compatibility | MicroPython v1.23+; tested via static code review only, no hardware verification performed |
| I2C Address | Default I2C address is 0x1A; ensure no conflicts with other I2C devices on the same bus |

## Version History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| v1.0.0 | 2026-07-23 | FreakStudio | Initial normalized version |

## Contact

- Email: FreakStudio@example.com
- GitHub: https://github.com/FreakStudioCN

## License

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
