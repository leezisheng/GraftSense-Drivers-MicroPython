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

last_print_time = 0
# 打印间隔（ms）
print_interval = 3000
device = None


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
print("  Pins: SCK=%d MOSI=%d MISO=%d CS=%d IRQ=%d RST=%d GPIO=%d" % (PIN_SCK, PIN_MOSI, PIN_MISO, PIN_CS, PIN_IRQ, PIN_RST, PIN_GPIO))

# 创建驱动实例（基类内部完成 SPI/Pin 初始化）
device = SX1262(SPI_BUS, PIN_SCK, PIN_MOSI, PIN_MISO, PIN_CS, PIN_IRQ, PIN_RST, PIN_GPIO)

print("Configuring LoRa mode (freq=%.1f MHz, bw=%.1f kHz, sf=%d, cr=%d)..." % (TEST_FREQ, TEST_BW, TEST_SF, TEST_CR))

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
    useRegulatorLDO=False,
)

if state == 0:
    print("SX1262 initialization successful!")
else:
    raise RuntimeError("SX1262 initialization failed, status: %s" % device.STATUS.get(state, str(state)))

print_device_info()

# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

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
    device = None
    print("Program exited")
