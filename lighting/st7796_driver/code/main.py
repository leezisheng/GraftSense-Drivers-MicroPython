# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 ST7796 SPI 显示驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import SPI, Pin
import time

# 从同目录导入驱动类
from st7796 import ST7796, color565, BLACK, WHITE, RED, GREEN, BLUE, BGR

# ======================================== 全局变量 ============================================

# --- 引脚定义（请根据实际硬件接线修改） ---
# SPI 时钟引脚
SCK_PIN = 18
# SPI MOSI 数据输出引脚
MOSI_PIN = 23
# 数据/命令选择引脚
DC_PIN = 2
# 片选引脚
CS_PIN = 15
# 复位引脚
RST_PIN = 4
# 背光控制引脚
BL_PIN = 5

# --- 显示参数 ---
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480

# --- 测试参数 ---
# 上次打印时间戳（ms）
last_print_time = time.ticks_ms()
# 打印间隔（ms）
print_interval = 2000
# 测试轮次计数
test_counter = 0

# ======================================== 功能函数 ============================================


def draw_test_pattern(display):
    """
    绘制测试图案：不同颜色的矩形和像素点
    此函数在初始化后调用一次，展示基本绘图功能
    """
    # 清屏为黑色
    display.fill(BLACK)
    print("Screen filled with black")

    # 绘制红色矩形（左上角区域）
    display.fill_rect(10, 10, 100, 100, RED)
    print("Filled red rectangle at (10,10) 100x100")

    # 绘制绿色矩形（右上角区域）
    display.fill_rect(210, 10, 100, 100, GREEN)
    print("Filled green rectangle at (210,10) 100x100")

    # 绘制蓝色矩形（左下角区域）
    display.fill_rect(10, 370, 100, 100, BLUE)
    print("Filled blue rectangle at (10,370) 100x100")

    # 绘制白色矩形（右下角区域）
    display.fill_rect(210, 370, 100, 100, WHITE)
    print("Filled white rectangle at (210,370) 100x100")

    # 在屏幕中央画十字交叉像素
    cx = DISPLAY_WIDTH // 2
    cy = DISPLAY_HEIGHT // 2
    for offset in range(-5, 6):
        display.pixel(cx + offset, cy, RED)
        display.pixel(cx, cy + offset, RED)
    print("Drew crosshair at center (%d, %d)" % (cx, cy))

    # 使用 color565 函数绘制黄色像素
    yellow = color565(255, 255, 0)
    display.pixel(cx + 10, cy + 10, yellow)
    display.pixel(cx - 10, cy - 10, yellow)
    print("Drew yellow pixels at center offsets")


def fill_color_cycle(display, counter):
    """
    全屏颜色循环切换
    每次调用切换一种颜色，循环 4 种基础色
    """
    colors = (RED, GREEN, BLUE, WHITE)
    names = ("RED", "GREEN", "BLUE", "WHITE")
    idx = counter % len(colors)
    display.fill(colors[idx])
    print("Cycle color: %s" % names[idx])


# ======================================== 自定义类 ==========================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: ST7796 SPI display driver test")

# --- 初始化 SPI 总线 ---
# SPI 速率 40 MHz，显示仅需单向通信
spi = SPI(1, baudrate=40000000, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=None)

# --- 初始化控制引脚 ---
dc = Pin(DC_PIN, Pin.OUT)
cs = Pin(CS_PIN, Pin.OUT)
rst = Pin(RST_PIN, Pin.OUT)
bl = Pin(BL_PIN, Pin.OUT)

# --- 创建 ST7796 显示驱动实例 ---
display = ST7796(spi=spi, dc=dc, cs=cs, reset=rst, backlight=bl, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotation=0, color_order=BGR)
print("ST7796 display driver initialized")

# --- 绘制初始测试图案 ---
draw_test_pattern(display)

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 低频操作：每隔一段时间切换全屏颜色
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            fill_color_cycle(display, test_counter)
            last_print_time = current_time
            test_counter += 1

        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    display.deinit()
    del display
    print("Program exited")
