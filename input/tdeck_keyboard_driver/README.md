# T-Deck Keyboard 驱动

## 简介

`tdeck_keyboard` 是 LILYGO T-Deck Plus 板载 T-Keyboard 的 MicroPython I2C 驱动。键盘控制器为板载 ESP32-C3 运行 LILYGO 官方固件，主控 ESP32-S3 通过 I2C 地址 `0x55` 与其通信。

**这不是 TCA8418 等通用键盘扫描芯片驱动**，而是 LILYGO 自定义 I2C 键盘协议。官方协议参考 [Xinyuan-LilyGO/T-Deck](https://github.com/Xinyuan-LilyGO/T-Deck) 仓库中的 `Keyboard_ESP32C3.ino` 和 `Keyboard_T_Deck_Master.ino`。

> **注意：此驱动未在 T-Deck Plus 实物上完成硬件验证。语法和导入检查已通过，但通信协议和按键矩阵映射需要在真实硬件上确认。**

## 主要功能

- 普通按键模式：读取单个按键 ASCII/控制字符（1 字节 I2C 读取）
- Raw 矩阵模式：读取 5 字节列位掩码（5 列 × 7 行矩阵）
- 按键矩阵解码：自动处理普通层/符号层/Shift 层
- 背光亮度控制（0..255）
- Alt+B 默认亮度设置（31..255）
- 键盘控制器供电引脚控制
- I2C OSError → RuntimeError 错误包装
- 所有轮询操作均有超时保护

## 硬件要求

- **主控**：ESP32-S3（LILYGO T-Deck Plus）
- **键盘控制器**：ESP32-C3（板载 I2C 从机）
- **接口**：I2C（地址 0x55）
- **供电**：可选 GPIO 控制键盘控制器供电

### 接线说明（T-Deck Plus 默认）

| 主控 ESP32-S3 | 键盘控制器 ESP32-C3 | 说明 |
|---------------|---------------------|------|
| GPIO8 (SCL)   | SCL                 | I2C 时钟 |
| GPIO18 (SDA)  | SDA                 | I2C 数据 |
| GPIO10        | PWR                 | 键盘供电控制（可选） |
| GND           | GND                 | 共地 |

## 软件环境

- MicroPython v1.23+
- `machine.I2C`、`machine.Pin`、`time`、`micropython.const`

## 文件结构

```
tdeck_keyboard_driver/
├── code/
│   ├── tdeck_keyboard.py   # 键盘驱动
│   └── main.py             # 测试示例
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `tdeck_keyboard.py` | T-Deck 键盘 I2C 驱动主模块 |
| `main.py` | 测试示例：I2C 扫描、按键读取、raw 矩阵、背光控制 |

## 快速开始

```python
from machine import I2C, Pin
from tdeck_keyboard import TDeckKeyboard

# 初始化 I2C（ESP32-S3 默认引脚）
i2c = I2C(0, scl=Pin(8), sda=Pin(18), freq=400000)

# 创建键盘驱动实例
kb = TDeckKeyboard(i2c, address=0x55, debug=False)

# 检测键盘
if kb.is_present():
    print("Keyboard found")

# 读取按键
key = kb.read_key()
if key is not None:
    print("Key:", repr(key))

# 设置背光
kb.set_brightness(200)

# 使用完毕后释放
kb.deinit()
```

## 注意事项

1. **这不是通用键盘驱动**：仅适用于 LILYGO T-Deck Plus 板载 ESP32-C3 键盘控制器
2. **未硬件验证**：驱动语法检查已通过，但未在 T-Deck Plus 实物上进行通信验证
3. **I2C 地址固定**：键盘控制器默认 I2C 地址为 0x55，不可更改
4. **供电时序**：若使用 `power_pin` 控制供电，需设置 `startup_ms` 等待 ESP32-C3 固件启动
5. **模式切换**：`set_raw_mode()` 和 `set_key_mode()` 会改变键盘固件工作模式
6. **轮询有超时**：`wait_key()` 有 `timeout_ms` 参数，不会无限阻塞

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-07-21 | 初始版本，基于 LILYGO 官方协议实现；未硬件验证 |

## 联系方式

- 作者：FreakStudio
- 项目：GraftSense-Drivers-MicroPython

## 许可协议

MIT License
