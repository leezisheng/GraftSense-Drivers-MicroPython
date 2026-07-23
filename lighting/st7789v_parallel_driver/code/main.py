# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Russ Hughes, FreakStudio
# @File    : main.py
# @Description : 测试ST7789V 8-bit并行接口驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from machine import Pin

# 时间相关的模块
import time

# 驱动相关的模块
from st7789v_parallel import ST7789, color565
from st7789v_parallel import BLACK, WHITE

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio: ST7789V 8-bit parallel display test")

# 数据总线引脚配置（D7 为 MSB，D0 为 LSB）
DATA_PINS = (7, 6, 5, 4, 3, 2, 1, 0)

# 控制引脚配置
WR_PIN = 8
RD_PIN = 9
DC_PIN = 10
CS_PIN = 11
RESET_PIN = 12
BACKLIGHT_PIN = 13

# 创建数据引脚 Pin 对象列表
data = [Pin(pin, Pin.OUT) for pin in DATA_PINS]

# 初始化设备（预声明为 None）
device = None

try:
    # 使用依赖注入方式创建 ST7789V 实例
    # 所有引脚作为 machine.Pin 实例传入
    device = ST7789(
        data[0],
        data[1],
        data[2],
        data[3],
        data[4],
        data[5],
        data[6],
        data[7],
        Pin(WR_PIN, Pin.OUT),
        Pin(RD_PIN, Pin.OUT),
        170,
        320,
        reset=Pin(RESET_PIN, Pin.OUT),
        dc=Pin(DC_PIN, Pin.OUT),
        cs=Pin(CS_PIN, Pin.OUT),
        backlight=Pin(BACKLIGHT_PIN, Pin.OUT),
        rotation=0,
    )
    print("ST7789V parallel display initialized successfully")

except Exception as e:
    print("Failed to initialize ST7789V: %s" % e)

# ========================================  主程序  ============================================

if device is not None:
    try:
        # 清屏为黑色
        device.fill(BLACK)
        # 绘制白色矩形边框
        device.rect(10, 10, 80, 40, WHITE)
        # 绘制蓝色填充矩形
        device.fill_rect(20, 20, 60, 20, color565(0, 160, 255))
        # 绘制一条对角线
        device.line(0, 0, 169, 319, WHITE)
        print("ST7789V test patterns drawn successfully")

    except Exception as e:
        print("Drawing error: %s" % e)

    finally:
        # 释放硬件资源
        device.deinit()
        device = None
        print("ST7789V driver deinitialized")
