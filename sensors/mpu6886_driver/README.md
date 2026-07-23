# MPU6886 6 轴运动跟踪传感器驱动 - MicroPython 版本

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

MPU6886 是一款 6 轴运动跟踪传感器，集成 3 轴加速度计和 3 轴陀螺仪，通过 I2C 接口与 MCU 通信。支持可配置加速度计量程（2/4/8/16g）和陀螺仪量程（250/500/1000/2000 dps），内置温度传感器。本驱动提供简洁的 Python 接口，支持多种物理单位换算（m/s^2、g、rad/s、deg/s），并包含陀螺仪零偏自动校准功能。

## 主要功能

- 加速度读取：三轴加速度值，支持 g 和 m/s^2 单位
- 角速度读取：三轴角速度值，支持 deg/s 和 rad/s 单位
- 温度读取：芯片内部温度（摄氏度）
- 芯片 ID 查询：WHO_AM_I 寄存器验证设备连接
- 陀螺仪校准：自动采集并计算零偏补偿值
- 可配置量程：加速度 2g/4g/8g/16g，陀螺仪 250/500/1000/2000 dps
- 依赖注入架构：I2C 总线由外部传入，便于多设备共享总线
- 上下文管理器支持：with 语句自动管理资源
- 调试日志开关（debug 参数）

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| MPU6886 传感器模块 | 6 轴 IMU 模块 |
| ESP32 开发板 | 主控 MCU |
| 杜邦线 | 4 根（VCC、GND、SCL、SDA） |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | ustruct、utime（MicroPython 内置） |
| 测试平台 | ESP32 |

## 文件结构

```
├── mpu6886.py   # MPU6886 核心驱动
├── main.py      # 测试示例
└── README.md    # 说明文档
```

## 文件说明

- **mpu6886.py**：MPU6886 6 轴传感器核心驱动文件。包含 `MPU6886` 类（传感器驱动）、灵敏度系数常量、单位换算尺度因子。提供 I2C 寄存器读写底层操作、传感器数据读取属性（acceleration/gyro/temperature）、陀螺仪校准功能、上下文管理器支持和资源释放。
- **main.py**：驱动测试示例。初始化 I2C 总线，扫描设备地址，验证芯片 ID，读取加速度/角速度/温度数据并定时打印。
- **README.md**：本说明文档。

## 快速开始

### 步骤一：复制文件

将 `mpu6886.py` 和 `main.py` 复制到 MicroPython 设备的根目录。

### 步骤二：接线

按以下方式连接（以 ESP32 为例）：

| MPU6886 | ESP32 |
|---------|-------|
| VCC     | 3.3V  |
| GND     | GND   |
| SCL     | GPIO22 |
| SDA     | GPIO21 |

### 步骤三：运行测试

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Mika Tuupola
# @File    : main.py
# @Description : 测试 MPU6886 6轴运动传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
import micropython
from mpu6886 import MPU6886, SF_G, SF_DEG_S

# ======================================== 全局变量 ============================================
# I2C 引脚配置（ESP32 为例，可根据实际接线修改）
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
# MPU6886 设备参数
MPU6886_I2C_ADDR = 0x68
# WHO_AM_I 寄存器期望值
MPU6886_CHIP_ID = 0x19

# 打印间隔控制
last_print_time = time.ticks_ms()
# 打印间隔（ms）
print_interval = 500

# ======================================== 功能函数 ============================================
def read_sensor_data():
    """
    读取传感器数据并打印（低频核心 API，保留自动执行）
    此函数在主循环中定时调用
    """
    # 读取加速度
    ax, ay, az = mpu.acceleration
    # 读取角速度
    gx, gy, gz = mpu.gyro
    # 读取温度
    temp = mpu.temperature

    print("Accel (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ax, ay, az))
    print("Gyro  (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (gx, gy, gz))
    print("Temperature: %.2f C" % temp)


def run_gyro_calibration():
    """
    执行陀螺仪校准（模式切换，默认注释调用，可 REPL 手动触发）
    设备必须保持静止状态
    """
    print("Starting gyroscope calibration...")
    print("Please keep the device stationary...")
    offset = mpu.calibrate(count=256, delay=10)
    print("Calibration complete, offset: X=%.4f, Y=%.4f, Z=%.4f" % offset)
    return offset


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 mpu6886.MPU6886

# ======================================== 初始化配置 ===========================================
# 等待设备就绪
time.sleep(3)
print("FreakStudio: MPU6886 6-axis motion sensor driver test")

# 创建 I2C 总线实例
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
print("I2C bus created on SCL=Pin(%d), SDA=Pin(%d)" % (I2C_SCL_PIN, I2C_SDA_PIN))

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found I2C devices at addresses: %s" % [hex(addr) for addr in devices])

# 检查目标设备是否存在
if MPU6886_I2C_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X" % MPU6886_I2C_ADDR
    )
print("Device found at 0x%02X" % MPU6886_I2C_ADDR)

# 创建 MPU6886 驱动实例
mpu = MPU6886(i2c, address=MPU6886_I2C_ADDR, debug=False)
print("MPU6886 driver instance created")

# 读取并验证芯片 ID
chip_id = mpu.whoami
if chip_id == MPU6886_CHIP_ID:
    print("Device verified: MPU6886 found (ID: 0x%02X)" % chip_id)
else:
    print("Warning: Unexpected chip ID 0x%02X (expected 0x%02X)" % (chip_id, MPU6886_CHIP_ID))

# 读取初始传感器数据
ax, ay, az = mpu.acceleration
gx, gy, gz = mpu.gyro
temp = mpu.temperature
print("Initial readings:")
print("  Acceleration (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ax, ay, az))
print("  Gyroscope (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (gx, gy, gz))
print("  Temperature: %.2f C" % temp)


# ========================================  主程序  ===========================================
try:
    # 上下文管理器示例（读取一次进行对比）
    with MPU6886(i2c, address=MPU6886_I2C_ADDR) as ctx_mpu:
        ctx_ax, ctx_ay, ctx_az = ctx_mpu.acceleration
        ctx_gx, ctx_gy, ctx_gz = ctx_mpu.gyro
        ctx_temp = ctx_mpu.temperature
        print("Context manager test:")
        print("  Accel (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ctx_ax, ctx_ay, ctx_az))
        print("  Gyro  (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (ctx_gx, ctx_gy, ctx_gz))
        print("  Temperature: %.2f C" % ctx_temp)

    # 主循环：定时读取传感器数据
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            read_sensor_data()
            last_print_time = current_time

        # 陀螺仪校准，注释默认执行，可 REPL 手动触发
        # run_gyro_calibration()

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    mpu.deinit()
    del mpu
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V，确保供电稳定 |
| I2C 地址 | 默认为 0x68（AD0 引脚接低电平），接高电平时为 0x69 |
| 陀螺仪校准 | 使用时建议先执行 `calibrate()` 校准零偏，设备需保持完全静止 |
| 量程选择 | 加速度默认 2g，陀螺仪默认 250dps；可根据实际运动剧烈程度调整 |
| 更新频率 | 默认 1kHz 采样率，可根据需求调整 |
| 温度读数 | 为芯片内部温度，非精确环境温度 |
| 多设备共享 | I2C 总线可与其他 I2C 设备共享，只要地址不冲突 |
| 资源释放 | 使用完毕后调用 `deinit()` 将设备置于睡眠模式 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | Mika Tuupola | 初始版本（GraftSense 规范化） |

## 联系方式

- 原作者：Mika Tuupola
- GitHub：https://github.com/tuupola/micropython-mpu6886
- GraftSense 规范化：GraftSense 团队

## 许可协议

MIT License

Copyright (c) 2020 Mika Tuupola

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
