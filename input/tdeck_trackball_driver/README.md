# T-Deck Trackball 驱动

## 简介

`tdeck_trackball` 是 LILYGO T-Deck Plus 板载轨迹球的 MicroPython GPIO 轮询驱动。

**这不是 I2C/SPI 轨迹球 IC 驱动**。T-Deck 轨迹球硬件由 Track Ball 组件 + 4 个 AN48841B Hall 开关 + TS-1187AB 中心按键组成，所有信号均为纯 GPIO 数字输入。驱动通过轮询四个方向 GPIO 的电平变化来跟踪相对位移，并读取中心按键状态。

> **注意：此驱动未在 T-Deck Plus 实物上完成硬件验证。语法和导入检查已通过，但方向映射和 Hall 开关电平变化行为需要在真实硬件上确认。**

## 主要功能

- 四方向 Hall 开关电平变化检测（right/up/left/down）
- 相对位移跟踪（累积 X/Y 位置）
- 中心按键状态读取（GPIO0，同时是 ESP32-S3 BOOT 引脚）
- 按键电平变化事件检测
- 可配置去抖延时
- GPIO 基线重新同步
- GPIO0 保护：驱动绝不将 BOOT 引脚配置为输出

## 硬件要求

- **主控**：ESP32-S3（LILYGO T-Deck Plus）
- **轨迹球组件**：Track Ball assembly + 4x AN48841B Hall switches + TS-1187AB center switch
- **接口**：5 个 GPIO 数字输入（无 I2C/SPI）

### 默认引脚映射（LILYGO T-Deck 官方 UnitTest）

| 功能 | GPIO | 板载标注 | 说明 |
|------|------|----------|------|
| 右方向 | GPIO2 | BOARD_TBOX_G02 | Hall 开关输入 |
| 上方向 | GPIO3 | BOARD_TBOX_G01 | Hall 开关输入 |
| 左方向 | GPIO1 | BOARD_TBOX_G04 | Hall 开关输入 |
| 下方向 | GPIO15 | BOARD_TBOX_G03 | Hall 开关输入 |
| 中心按键 | GPIO0 | BOARD_BOOT_PIN | TS-1187AB 按键输入（同时是 BOOT 引脚） |

## 软件环境

- MicroPython v1.23+
- `machine.Pin`、`time`、`micropython.const`

## 文件结构

```
tdeck_trackball_driver/
├── code/
│   ├── tdeck_trackball.py  # 轨迹球驱动
│   └── main.py             # 测试示例
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `tdeck_trackball.py` | T-Deck 轨迹球 GPIO 轮询驱动主模块 |
| `main.py` | 测试示例：GPIO 初始化、轨迹球轮询、位置跟踪 |

## 快速开始

```python
from machine import Pin
from tdeck_trackball import TDeckTrackball

# 创建轨迹球驱动实例（使用默认 T-Deck 引脚映射）
tb = TDeckTrackball(
    pin_right=2,      # GPIO2  (G02)
    pin_up=3,         # GPIO3  (G01)
    pin_left=1,       # GPIO1  (G04)
    pin_down=15,      # GPIO15 (G03)
    pin_button=0,     # GPIO0  (BOOT)
    step=1,
    debounce_ms=5,
)

# 轮询轨迹球
dx, dy, pressed = tb.poll()
print("Delta: dx=%d, dy=%d, pressed=%s" % (dx, dy, pressed))

# 获取累计位置
x, y = tb.position()
print("Position: x=%d, y=%d" % (x, y))

# 使用完毕后释放
tb.deinit()
```

## 注意事项

1. **这不是 I2C/SPI 轨迹球 IC 驱动**：T-Deck 轨迹球是纯 GPIO 输入，不含任何寄存器或通信协议
2. **未硬件验证**：驱动语法检查已通过，但未在 T-Deck Plus 实物上进行 GPIO 验证
3. **GPIO0 保护**：GPIO0 同时是 ESP32-S3 BOOT 引脚，驱动绝对不将其配置为输出模式
4. **方向映射**：方向映射遵循 LILYGO 官方 UnitTest 约定（right=+X, up=-Y, left=-X, down=+Y）
5. **电平变化检测**：驱动对任意电平变化进行计数，适用于 Hall 开关的边沿行为
6. **去抖**：建议设置 `debounce_ms=5~10` 以过滤机械/电磁噪声

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-07-21 | 初始版本，基于 LILYGO 官方 UnitTest 引脚映射；未硬件验证 |

## 联系方式

- 作者：FreakStudio
- 项目：GraftSense-Drivers-MicroPython

## 许可协议

MIT License
