# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : st7796.py
# @Description : ST7796/ST7796S SPI display driver
# @License : MIT

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import struct
import time

# ======================================== 全局变量 ============================================

# --- 显示命令常量 ---
_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_DISPOFF = const(0x28)
_DISPON = const(0x29)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)
_MADCTL = const(0x36)
_COLMOD = const(0x3A)
_INVON = const(0x21)
_INVOFF = const(0x20)

# --- MADCTL 方向位 ---
_MADCTL_MY = const(0x80)
_MADCTL_MX = const(0x40)
_MADCTL_MV = const(0x20)
_MADCTL_BGR = const(0x08)

# --- 颜色顺序常量 ---
RGB = const(0x00)
BGR = const(0x08)

# --- 常用颜色常量 ---
BLACK = const(0x0000)
WHITE = const(0xFFFF)
RED = const(0xF800)
GREEN = const(0x07E0)
BLUE = const(0x001F)

# --- 数据打包格式字符串 ---
_ENCODE_POS = ">HH"
_ENCODE_PIXEL = ">H"

# --- ST7796 初始化命令序列 ---
_INIT_CMDS = (
    (_SWRESET, None, 120),
    (_SLPOUT, None, 120),
    (0xF0, b"\xC3", 0),
    (0xF0, b"\x96", 0),
    (_COLMOD, b"\x55", 0),
    (0xB7, b"\xC6", 0),
    (0xB4, b"\x01", 0),
    (0xB6, b"\x80\x02\x3B", 0),
    (0xE8, b"\x40\x8A\x00\x00\x29\x19\xA5\x33", 0),
    (0xC1, b"\x06", 0),
    (0xC2, b"\xA7", 0),
    (0xC5, b"\x18", 120),
    (0xE0, b"\xF0\x09\x0B\x06\x04\x15\x2F\x54\x42\x3C\x17\x14\x18\x1B", 0),
    (0xE1, b"\xF0\x09\x0B\x06\x04\x03\x2D\x43\x42\x3B\x16\x14\x17\x1B", 120),
    (0xF0, b"\x3C", 0),
    (0xF0, b"\x69", 120),
    (_DISPON, None, 120),
)

# ======================================== 功能函数 ============================================


def color565(red, green=0, blue=0):
    """
    将 RGB 分量转换为 16 位 RGB565 格式颜色值
    Args:
        red: 红色分量（0-255），或 (R, G, B) 元组/列表
        green: 绿色分量（0-255），当 red 为单值时使用
        blue: 蓝色分量（0-255），当 red 为单值时使用
    Returns:
        int: 16 位 RGB565 颜色值
    ==========================================
    Convert RGB components to 16-bit RGB565 color value.
    Args:
        red: Red component (0-255), or (R, G, B) tuple/list
        green: Green component (0-255), used when red is a single value
        blue: Blue component (0-255), used when red is a single value
    Returns:
        int: 16-bit RGB565 color value
    """
    if isinstance(red, (tuple, list)):
        red, green, blue = red[:3]
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


# ======================================== 自定义类 ============================================


class ST7796:
    """
    ST7796/ST7796S SPI 显示驱动类

    提供 SPI 接口的 ST7796 系列 TFT 显示屏基础驱动能力，
    包含初始化、旋转、像素绘制、矩形填充、颜色反转和背光控制等功能。
    支持 320x480 分辨率，16 位 RGB565 颜色格式。

    Attributes:
        spi (SPI): SPI 总线实例
        dc (Pin): 数据/命令选择引脚实例
        cs (Pin): 片选引脚实例（可选）
        reset_pin (Pin): 复位引脚实例（可选）
        backlight (Pin): 背光控制引脚实例（可选）
        width (int): 显示宽度（像素）
        height (int): 显示高度（像素）
        rotation (int): 旋转角度（0-3）
        color_order (int): 颜色顺序（RGB 或 BGR）
    Methods:
        reset(): 执行硬件复位或软件复位
        init(): 发送 ST7796 初始化命令序列
        set_rotation(rotation): 设置显示旋转角度
        set_window(x0, y0, x1, y1): 设置显示窗口区域
        blit_buffer(buf, x, y, w, h): 写入像素缓冲区到指定区域
        pixel(x, y, color): 绘制单个像素
        fill_rect(x, y, w, h, color): 填充矩形区域
        fill(color): 填充全屏
        invert(enable): 反转显示颜色
        display_on(): 打开显示
        display_off(): 关闭显示
        deinit(): 释放资源（关闭显示和背光）
    Notes:
        - 依赖外部传入 SPI 和 Pin 实例，不在内部创建
        - 创建实例时自动执行硬件复位和初始化
        - 仅支持 16 位 RGB565 颜色格式
        - ST7796 初始化命令序列与 ST7789 不同，不可互换
    ==========================================
    ST7796/ST7796S SPI display driver.

    Provides basic SPI display driver for ST7796 series TFT screens,
    including init, rotation, pixel draw, rectangle fill, color inversion
    and backlight control. Supports 320x480 resolution, 16-bit RGB565 color.

    Attributes:
        spi (SPI): SPI bus instance
        dc (Pin): Data/command pin instance
        cs (Pin): Chip select pin instance (optional)
        reset_pin (Pin): Reset pin instance (optional)
        backlight (Pin): Backlight pin instance (optional)
        width (int): Display width in pixels
        height (int): Display height in pixels
        rotation (int): Rotation angle (0-3)
        color_order (int): Color order (RGB or BGR)
    Methods:
        reset(): Perform hardware or software reset
        init(): Send ST7796 initialization command sequence
        set_rotation(rotation): Set display rotation angle
        set_window(x0, y0, x1, y1): Set display window area
        blit_buffer(buf, x, y, w, h): Write pixel buffer to area
        pixel(x, y, color): Draw a single pixel
        fill_rect(x, y, w, h, color): Fill a rectangular area
        fill(color): Fill entire screen
        invert(enable): Invert display colors
        display_on(): Turn display on
        display_off(): Turn display off
        deinit(): Release resources (turn off display and backlight)
    Notes:
        - Requires externally provided SPI and Pin instances
        - Hardware reset and init are performed on instance creation
        - Only supports 16-bit RGB565 color format
        - ST7796 init command sequence differs from ST7789, do not interchange
    """

    __slots__ = (
        "spi",
        "dc",
        "cs",
        "reset_pin",
        "backlight",
        "width",
        "height",
        "rotation",
        "color_order",
        "_buf4",
        "_debug",
    )

    def __init__(self, spi, dc, cs=None, reset=None, backlight=None, width=320, height=480, rotation=0, color_order=BGR, debug=False):
        """
        初始化 ST7796 显示驱动实例

        Args:
            spi: SPI 总线实例，须具有 write 方法
            dc: 数据/命令选择引脚实例，须具有 value 方法
            cs: 片选引脚实例（可选）
            reset: 复位引脚实例（可选），为 None 时使用软件复位
            backlight: 背光控制引脚实例（可选）
            width (int): 显示宽度（像素），默认 320
            height (int): 显示高度（像素），默认 480
            rotation (int): 旋转角度（0-3），默认 0
            color_order (int): 颜色顺序，默认 BGR
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型或值无效
        Notes:
            - 创建实例时自动执行硬件复位和初始化序列
            - SPI 和 Pin 实例必须由调用方创建并传入
        ==========================================
        Initialize ST7796 display driver instance.

        Args:
            spi: SPI bus instance, must have write method
            dc: Data/command pin instance, must have value method
            cs: Chip select pin instance (optional)
            reset: Reset pin instance (optional), software reset if None
            backlight: Backlight pin instance (optional)
            width (int): Display width in pixels, default 320
            height (int): Display height in pixels, default 480
            rotation (int): Rotation angle (0-3), default 0
            color_order (int): Color order, default BGR
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type or value
        Notes:
            - Hardware reset and init sequence run on instance creation
            - SPI and Pin instances must be created externally
        """
        # SPI 参数校验
        if not hasattr(spi, "write"):
            raise ValueError("spi must have write() method")
        # DC 引脚参数校验
        if not hasattr(dc, "value"):
            raise ValueError("dc must have value() method")
        # CS 引脚参数校验（可选）
        if cs is not None and not hasattr(cs, "value"):
            raise ValueError("cs must have value() method or be None")
        # reset 引脚参数校验（可选）
        if reset is not None and not hasattr(reset, "value"):
            raise ValueError("reset must have value() method or be None")
        # backlight 引脚参数校验（可选）
        if backlight is not None and not hasattr(backlight, "value"):
            raise ValueError("backlight must have value() method or be None")
        # width 参数校验
        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be a positive int, got %s" % repr(width))
        # height 参数校验
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be a positive int, got %s" % repr(height))
        # rotation 参数校验
        if not isinstance(rotation, int) or rotation not in (0, 1, 2, 3):
            raise ValueError("rotation must be int in (0,1,2,3), got %s" % repr(rotation))
        # color_order 参数校验
        if color_order not in (RGB, BGR):
            raise ValueError("color_order must be RGB or BGR, got %s" % repr(color_order))

        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.reset_pin = reset
        self.backlight = backlight
        self.width = width
        self.height = height
        self.rotation = rotation
        self.color_order = color_order
        self._buf4 = bytearray(4)
        self._debug = debug

        self.reset()
        self.init()

    def _log(self, msg):
        """
        输出调试日志

        Args:
            msg (str): 日志消息
        Notes:
            - 仅在 _debug 为 True 时输出
            - 日志前缀为 [ST7796]
        ==========================================
        Output debug log.

        Args:
            msg (str): Log message
        Notes:
            - Only prints when _debug is True
            - Log prefix is [ST7796]
        """
        if self._debug:
            print("[ST7796] %s" % msg)

    def reset(self):
        """
        执行硬件复位或软件复位

        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 若 reset_pin 为 None，发送软件复位命令 (_SWRESET)
            - 若 reset_pin 已配置，通过引脚电平执行硬件复位
            - 复位后会延时 120ms 等待显示屏稳定
        ==========================================
        Perform hardware or software reset.

        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Sends SWRESET command if reset_pin is None
            - Performs hardware reset via pin if reset_pin is configured
            - Delays 120ms after reset for display stabilization
        """
        if self.reset_pin is None:
            self._log("software reset")
            self._write_cmd(_SWRESET)
            time.sleep_ms(120)
            return
        self._log("hardware reset")
        self.reset_pin.value(1)
        time.sleep_ms(10)
        self.reset_pin.value(0)
        time.sleep_ms(20)
        self.reset_pin.value(1)
        time.sleep_ms(120)

    def init(self):
        """
        发送 ST7796 初始化命令序列

        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 按 _INIT_CMDS 顺序发送寄存器配置命令
            - 初始化完成后自动打开背光（若已配置）
            - 初始化完成后设置显示旋转角度
        ==========================================
        Send ST7796 initialization command sequence.

        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Sends register config commands in _INIT_CMDS order
            - Automatically turns on backlight after init (if configured)
            - Sets display rotation after init
        """
        self._log("init display")
        # 遍历初始化命令序列
        for cmd, data, delay in _INIT_CMDS:
            if cmd == _MADCTL:
                data = bytes([self._madctl()])
            self._write_cmd(cmd, data)
            if delay:
                time.sleep_ms(delay)
        self.set_rotation(self.rotation)
        # 初始化完成后打开背光
        if self.backlight is not None:
            self.backlight.value(1)

    def set_rotation(self, rotation):
        """
        设置显示旋转角度

        Args:
            rotation (int): 旋转角度（0=0°, 1=90°, 2=180°, 3=270°）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 通过写入 MADCTL 寄存器实现旋转
            - 旋转参数会被掩码到 0-3 范围
        ==========================================
        Set display rotation angle.

        Args:
            rotation (int): Rotation angle (0=0, 1=90, 2=180, 3=270 degrees)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Achieves rotation by writing to MADCTL register
            - Rotation value is masked to 0-3 range
        """
        self.rotation = rotation & 3
        # 根据旋转角度计算 MADCTL 寄存器值
        if self.rotation == 0:
            madctl = self.color_order
        elif self.rotation == 1:
            madctl = _MADCTL_MX | _MADCTL_MV | self.color_order
        elif self.rotation == 2:
            madctl = _MADCTL_MX | _MADCTL_MY | self.color_order
        else:
            madctl = _MADCTL_MY | _MADCTL_MV | self.color_order
        self._write_cmd(_MADCTL, bytes([madctl]))

    def set_window(self, x0, y0, x1, y1):
        """
        设置显示窗口区域

        Args:
            x0 (int): 起始列地址
            y0 (int): 起始行地址
            x1 (int): 结束列地址
            y1 (int): 结束行地址
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 设置列地址 (CASET) 和行地址 (RASET) 寄存器
            - 后续 RAM 写入操作将限于此窗口内
        ==========================================
        Set display window area.

        Args:
            x0 (int): Start column address
            y0 (int): Start row address
            x1 (int): End column address
            y1 (int): End row address
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Sets column (CASET) and row (RASET) address registers
            - Subsequent RAM write operations are confined to this window
        """
        struct.pack_into(_ENCODE_POS, self._buf4, 0, x0, x1)
        self._write_cmd(_CASET, self._buf4)
        struct.pack_into(_ENCODE_POS, self._buf4, 0, y0, y1)
        self._write_cmd(_RASET, self._buf4)
        self._write_cmd(_RAMWR)

    def blit_buffer(self, buffer, x, y, width, height):
        """
        将像素缓冲区写入指定区域

        Args:
            buffer: 像素数据缓冲区，RGB565 格式（bytes/bytearray/memoryview）
            x (int): X 起始坐标
            y (int): Y 起始坐标
            width (int): 区域宽度（像素）
            height (int): 区域高度（像素）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 自动设置窗口并写入数据
            - 缓冲区大小应为 width * height * 2 字节
        ==========================================
        Write pixel buffer to specified area.

        Args:
            buffer: Pixel data buffer in RGB565 format (bytes/bytearray/memoryview)
            x (int): X start coordinate
            y (int): Y start coordinate
            width (int): Area width in pixels
            height (int): Area height in pixels
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Automatically sets window and writes data
            - Buffer size should be width * height * 2 bytes
        """
        self.set_window(x, y, x + width - 1, y + height - 1)
        self._write_data(buffer)

    def pixel(self, x, y, color):
        """
        绘制单个像素

        Args:
            x (int): X 坐标
            y (int): Y 坐标
            color (int): RGB565 颜色值
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Draw a single pixel.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color (int): RGB565 color value
        Raises:
            RuntimeError: SPI communication failed
        """
        # 将颜色值打包为大端 16 位格式
        struct.pack_into(_ENCODE_PIXEL, self._buf4, 0, color)
        self.blit_buffer(memoryview(self._buf4)[:2], x, y, 1, 1)

    def fill_rect(self, x, y, width, height, color):
        """
        填充矩形区域

        Args:
            x (int): 起始 X 坐标
            y (int): 起始 Y 坐标
            width (int): 矩形宽度（像素）
            height (int): 矩形高度（像素）
            color (int): RGB565 颜色值
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Fill a rectangular area.

        Args:
            x (int): Start X coordinate
            y (int): Start Y coordinate
            width (int): Rectangle width in pixels
            height (int): Rectangle height in pixels
            color (int): RGB565 color value
        Raises:
            RuntimeError: SPI communication failed
        """
        # 预生成一行像素数据，按行重复写入
        line = struct.pack(_ENCODE_PIXEL, color) * width
        self.set_window(x, y, x + width - 1, y + height - 1)
        for _ in range(height):
            self._write_data(line)

    def fill(self, color=BLACK):
        """
        填充全屏为指定颜色

        Args:
            color (int): RGB565 颜色值，默认 BLACK
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 等同于 fill_rect(0, 0, width, height, color)
        ==========================================
        Fill entire screen with specified color.

        Args:
            color (int): RGB565 color value, default BLACK
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Equivalent to fill_rect(0, 0, width, height, color)
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    def invert(self, enable=True):
        """
        反转显示颜色

        Args:
            enable (bool): True 反转显示，False 恢复正常
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 通过 INVON/INVOFF 命令切换
        ==========================================
        Invert display colors.

        Args:
            enable (bool): True to invert, False to restore normal
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Toggles via INVON/INVOFF commands
        """
        self._write_cmd(_INVON if enable else _INVOFF)

    def display_on(self):
        """
        打开显示

        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 发送 DISPON (0x29) 命令
        ==========================================
        Turn display on.

        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Sends DISPON (0x29) command
        """
        self._write_cmd(_DISPON)

    def display_off(self):
        """
        关闭显示

        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 发送 DISPOFF (0x28) 命令
        ==========================================
        Turn display off.

        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Sends DISPOFF (0x28) command
        """
        self._write_cmd(_DISPOFF)

    def deinit(self):
        """
        释放显示资源

        Notes:
            - 关闭显示面板
            - 关闭背光（若已配置）
            - 不释放 SPI 总线（由调用方管理）
        ==========================================
        Release display resources.

        Notes:
            - Turns off the display panel
            - Turns off backlight (if configured)
            - Does not release SPI bus (managed by caller)
        """
        self._log("deinit")
        self.display_off()
        if self.backlight is not None:
            self.backlight.value(0)

    # --- 私有方法 ---

    def _madctl(self):
        """返回当前默认 MADCTL 值"""
        return self.color_order

    def _select(self):
        """选中 SPI 芯片（拉低 CS 引脚）"""
        if self.cs is not None:
            self.cs.value(0)

    def _deselect(self):
        """取消选中 SPI 芯片（拉高 CS 引脚）"""
        if self.cs is not None:
            self.cs.value(1)

    def _write_cmd(self, cmd, data=None):
        """
        通过 SPI 写入命令及可选数据

        拉低 DC 发送命令字节，若提供 data 则切换 DC 为高后发送数据。
        每次操作前后控制 CS 片选信号。

        Args:
            cmd (int): 命令字节
            data (bytes): 可选数据
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Write command and optional data via SPI.

        Pulls DC low to send command byte, then pulls DC high
        to send data if provided. Controls CS before and after.

        Args:
            cmd (int): Command byte
            data (bytes): Optional data
        Raises:
            RuntimeError: SPI communication failed
        """
        self._select()
        # DC=0 表示发送命令
        self.dc.value(0)
        try:
            self.spi.write(bytes([cmd]))
        except OSError:
            raise RuntimeError("SPI write command 0x%02X failed" % cmd)
        if data is not None:
            # DC=1 表示发送数据
            self.dc.value(1)
            try:
                self.spi.write(data)
            except OSError:
                raise RuntimeError("SPI write data failed")
        self._deselect()

    def _write_data(self, data):
        """
        通过 SPI 写入纯数据

        保持 DC 为高，通过 SPI 发送数据字节。操作前后控制 CS 片选。

        Args:
            data (bytes): 数据字节序列
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Write data via SPI.

        Keeps DC high, sends data bytes via SPI.
        Controls CS before and after the operation.

        Args:
            data (bytes): Data bytes
        Raises:
            RuntimeError: SPI communication failed
        """
        self._select()
        # DC=1 表示发送数据
        self.dc.value(1)
        try:
            self.spi.write(data)
        except OSError:
            raise RuntimeError("SPI write data failed")
        self._deselect()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
