# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Guy Carver, boochow
# @File    : main.py
# @Description : 测试 ST7735 TFT LCD 显示驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, SPI
from st7735 import TFT

# ======================================== 全局变量 ============================================
# SPI 引脚配置（ESP32 为例，可根据实际接线修改）
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 23
SPI_MISO_PIN = 19
# ST7735 控制引脚配置
# ST7735 数据/命令选择引脚
TFT_DC_PIN = 2
# ST7735 复位引脚
TFT_RESET_PIN = 4
# ST7735 片选引脚
TFT_CS_PIN = 5

# 打印间隔控制
last_print_time = 0
# 打印间隔（ms）
print_interval = 2000


# ======================================== 功能函数 ============================================
def run_display_demo(tft):
    """
    运行显示演示：填充颜色并绘制图形
    此函数默认注释调用，可在 REPL 中手动调用
    Args:
        tft (TFT): TFT 显示驱动实例
    """
    print("Running display demo...")
    # 填充为黑色背景
    tft.fill(TFT.BLACK)

    # 绘制填充矩形（红色）
    tft.fillrect((10, 10), (50, 30), TFT.RED)
    # 绘制空心矩形（绿色）
    tft.rect((10, 50), (50, 30), TFT.GREEN)
    # 绘制水平线（蓝色）
    tft.hline((70, 20), 40, TFT.BLUE)
    # 绘制垂直线（青色）
    tft.vline((70, 20), 40, TFT.CYAN)
    # 绘制填充圆（黄色）
    tft.fillcircle((40, 110), 15, TFT.YELLOW)
    # 绘制空心圆（白色）
    tft.circle((90, 110), 15, TFT.WHITE)
    # 绘制对角线（紫色）
    tft.line((10, 140), (120, 150), TFT.PURPLE)

    print("Display demo completed")


def test_screen_rotation(tft):
    """
    测试屏幕旋转功能（模式切换，默认注释调用，可 REPL 手动触发）
    Args:
        tft (TFT): TFT 显示驱动实例
    """
    # 依次测试 4 个旋转方向
    for rot in range(4):
        tft.rotation(rot)
        tft.fill(TFT.BLACK)
        tft.text((10, 50), "Rot %d" % rot, TFT.WHITE, {"Start": 32, "End": 126, "Width": 8, "Height": 16, "Data": []})

    # 恢复默认方向
    tft.rotation(0)
    tft.fill(TFT.BLACK)
    print("Rotation test completed")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 st7735.TFT

# ======================================== 初始化配置 ===========================================
# 等待设备就绪
time.sleep(3)
print("FreakStudio: ST7735 TFT LCD display driver test")

# 创建 SPI 总线实例
spi = SPI(1, sck=Pin(SPI_SCK_PIN), mosi=Pin(SPI_MOSI_PIN), miso=Pin(SPI_MISO_PIN), baudrate=20000000, polarity=0, phase=0)

# 创建控制引脚实例
dc = Pin(TFT_DC_PIN, Pin.OUT, Pin.PULL_DOWN)
reset = Pin(TFT_RESET_PIN, Pin.OUT, Pin.PULL_DOWN)
cs = Pin(TFT_CS_PIN, Pin.OUT, Pin.PULL_DOWN)

# 创建 TFT 驱动实例
tft = TFT(spi, dc, reset, cs, debug=False)
print("TFT driver instance created")

# 初始化显示（选择适合你屏幕版本的初始化方法）
# 可选：tft.initb(), tft.initr(), tft.initb2(), tft.initg()
print("Initializing display (green tab version)...")
tft.initg()
print("Display initialized")

# 填充黑色背景
tft.fill(TFT.BLACK)

# 设置 RGB 颜色顺序并填充测试颜色
tft.rgb(True)
print("Color order set to RGB")

# 填充蓝色背景测试
tft.fill(TFT.BLUE)
time.sleep_ms(500)

# 填充红色测试
tft.fill(TFT.RED)
time.sleep_ms(500)

# 填充绿色测试
tft.fill(TFT.GREEN)
time.sleep_ms(500)

# 填充黑色（恢复正常）
tft.fill(TFT.BLACK)

# 运行显示演示（低频核心 API，保留自动执行）
run_display_demo(tft)


# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        # 定时打印状态信息
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            size = tft.size()
            rotation_idx = tft.get_rotation()
            rgb_mode = tft.get_rgb()
            print("Screen: %dx%d, Rotation: %d, RGB: %s" % (size[0], size[1], rotation_idx, str(rgb_mode)))
            last_print_time = current_time

        # 模式切换，注释默认执行，可 REPL 手动触发
        # test_screen_rotation(tft)

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    tft.deinit()
    del tft
    print("Program exited")
