# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 12:00
# @Author  : Guy Carver (original), boochow (modifications)
# @File    : st7735.py
# @Description : ST7735 TFT LCD 显示驱动（SPI）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Guy Carver, boochow"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import time
from math import sqrt
import micropython

# ======================================== 全局变量 ============================================
# 旋转方向查找表（对应 MADCTL 寄存器位设置）
# 以引脚朝上方向为基准：
#   0x00 = 不旋转（默认竖向，引脚朝上）
#   0x60 = 顺时针旋转 90 度
#   0xC0 = 顺时针旋转 180 度
#   0xA0 = 顺时针旋转 270 度
TFT_ROTATIONS = [0x00, 0x60, 0xC0, 0xA0]
# MADCTL 位：BGR 颜色顺序
TFT_BGR = 0x08
# MADCTL 位：RGB 颜色顺序
TFT_RGB = 0x00
# 默认屏幕尺寸（宽 x 高）
SCREEN_SIZE = (128, 160)


# ======================================== 功能函数 ============================================
def clamp(value, min_val, max_val):
    """
    将数值限制在指定范围内
    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值
    Returns:
        限制后的值
    ==========================================
    Clamp a value between min and max.
    """
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def tft_color(r, g, b):
    """
    将 8 位 RGB 分量转换为 16 位 RGB565 颜色值
    本函数假定 RGB 565 颜色布局，对 BGR 布局结果不正确
    Args:
        r (int): 红色分量 (0-255)
        g (int): 绿色分量 (0-255)
        b (int): 蓝色分量 (0-255)
    Returns:
        int: 16 位 RGB565 颜色值
    ==========================================
    Create a 16-bit RGB565 color value from 8-bit R, G, B components.
    This assumes RGB 565 layout and will be incorrect for BGR.
    """
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# ======================================== 自定义类 ============================================
class TFT:
    """
    ST7735 TFT LCD 显示驱动类
    通过 SPI 接口控制 ST7735 芯片，支持多种初始化模式（蓝标/红标/绿标）
    Attributes:
        _spi: SPI 总线实例
        _dc (Pin): 数据/命令选择引脚
        _reset (Pin): 复位引脚
        _cs (Pin): 片选引脚
        _size (tuple): 当前屏幕尺寸 (宽, 高)
        _rotate (int): 当前旋转角度索引 (0-3)
        _rgb (bool): 颜色顺序，True 为 RGB，False 为 BGR
    Methods:
        color(): 创建 RGB565 颜色值（静态方法）
        on(): 开关显示
        fill(): 填充整个屏幕
        pixel(): 绘制单像素
        text(): 绘制文本
        line(): 绘制直线
        rect()/fillrect(): 绘制矩形
        circle()/fillcircle(): 绘制圆形
        image(): 绘制位图
        initb()/initr()/initb2()/initg(): 初始化显示
        deinit(): 释放硬件资源
    Notes:
        - SPI 总线必须由外部注入，不在类内创建
        - DC/Reset/CS 引脚必须为 Pin 实例，不在类内创建
        - 支持 ISR-safe: 否（所有方法均涉及 SPI 通信）
    ==========================================
    ST7735 TFT LCD display driver class.
    Controls ST7735 chip via SPI interface with multiple init modes.
    Attributes:
        _spi: SPI bus instance
        _dc (Pin): Data/Command pin
        _reset (Pin): Reset pin
        _cs (Pin): Chip select pin
        _size (tuple): Current screen size (width, height)
        _rotate (int): Current rotation index (0-3)
        _rgb (bool): Color order, True for RGB, False for BGR
    Methods:
        color(): Create RGB565 color value (static)
        on(): Turn display on/off
        fill(): Fill entire screen
        pixel(): Draw single pixel
        text(): Draw text
        line(): Draw line
        rect()/fillrect(): Draw rectangle
        circle()/fillcircle(): Draw circle
        image(): Draw bitmap
        initb()/initr()/initb2()/initg(): Initialize display
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided SPI bus instance
        - DC/Reset/CS pins must be Pin instances
        - ISR-safe: No (all methods involve SPI communication)
    """

    # ========== 寄存器命令常量 ==========
    NOP = micropython.const(0x00)
    SWRESET = micropython.const(0x01)
    RDDID = micropython.const(0x04)
    RDDST = micropython.const(0x09)

    SLPIN = micropython.const(0x10)
    SLPOUT = micropython.const(0x11)
    PTLON = micropython.const(0x12)
    NORON = micropython.const(0x13)

    INVOFF = micropython.const(0x20)
    INVON = micropython.const(0x21)
    DISPOFF = micropython.const(0x28)
    DISPON = micropython.const(0x29)
    CASET = micropython.const(0x2A)
    RASET = micropython.const(0x2B)
    RAMWR = micropython.const(0x2C)
    RAMRD = micropython.const(0x2E)

    VSCRDEF = micropython.const(0x33)
    VSCSAD = micropython.const(0x37)

    COLMOD = micropython.const(0x3A)
    MADCTL = micropython.const(0x36)

    FRMCTR1 = micropython.const(0xB1)
    FRMCTR2 = micropython.const(0xB2)
    FRMCTR3 = micropython.const(0xB3)
    INVCTR = micropython.const(0xB4)
    DISSET5 = micropython.const(0xB6)

    PWCTR1 = micropython.const(0xC0)
    PWCTR2 = micropython.const(0xC1)
    PWCTR3 = micropython.const(0xC2)
    PWCTR4 = micropython.const(0xC3)
    PWCTR5 = micropython.const(0xC4)
    VMCTR1 = micropython.const(0xC5)

    RDID1 = micropython.const(0xDA)
    RDID2 = micropython.const(0xDB)
    RDID3 = micropython.const(0xDC)
    RDID4 = micropython.const(0xDD)

    PWCTR6 = micropython.const(0xFC)

    GMCTRP1 = micropython.const(0xE0)
    GMCTRN1 = micropython.const(0xE1)

    # ========== 颜色常量（RGB565 格式）==========
    BLACK = 0
    RED = tft_color(0xFF, 0x00, 0x00)
    MAROON = tft_color(0x80, 0x00, 0x00)
    GREEN = tft_color(0x00, 0xFF, 0x00)
    FOREST = tft_color(0x00, 0x80, 0x80)
    BLUE = tft_color(0x00, 0x00, 0xFF)
    NAVY = tft_color(0x00, 0x00, 0x80)
    CYAN = tft_color(0x00, 0xFF, 0xFF)
    YELLOW = tft_color(0xFF, 0xFF, 0x00)
    PURPLE = tft_color(0xFF, 0x00, 0xFF)
    WHITE = tft_color(0xFF, 0xFF, 0xFF)
    GRAY = tft_color(0x80, 0x80, 0x80)

    @staticmethod
    def color(r, g, b):
        """
        创建 RGB565 格式的 16 位颜色值
        Args:
            r (int): 红色分量 (0-255)
            g (int): 绿色分量 (0-255)
            b (int): 蓝色分量 (0-255)
        Returns:
            int: 16 位 RGB565 颜色值
        ==========================================
        Create a 16-bit RGB565 color value.
        Args:
            r (int): Red component (0-255)
            g (int): Green component (0-255)
            b (int): Blue component (0-255)
        Returns:
            int: 16-bit RGB565 color value
        """
        return tft_color(r, g, b)

    def __init__(self, spi, aDC, aReset, aCS, debug=False):
        """
        初始化 ST7735 显示驱动
        Args:
            spi: SPI 总线实例（必须外部注入）
            aDC (Pin): 数据/命令选择引脚实例
            aReset (Pin): 复位引脚实例
            aCS (Pin): 片选引脚实例
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: 参数类型不正确
        Notes:
            - 所有引脚必须为 machine.Pin 实例
            - 初始化后需调用 initb()/initr()/initb2()/initg() 之一来配置显示
        ==========================================
        Initialize ST7735 display driver.
        Args:
            spi: SPI bus instance (must be externally provided)
            aDC (Pin): Data/Command pin instance
            aReset (Pin): Reset pin instance
            aCS (Pin): Chip select pin instance
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
        Notes:
            - All pins must be machine.Pin instances
            - Call initb()/initr()/initb2()/initg() after construction
        """
        # 参数校验：spi 实例检查
        if not hasattr(spi, "write"):
            raise ValueError("spi must be an SPI instance")
        # 参数校验：引脚实例检查
        if not hasattr(aDC, "value"):
            raise ValueError("aDC must be a Pin instance")
        if not hasattr(aReset, "value"):
            raise ValueError("aReset must be a Pin instance")
        if not hasattr(aCS, "value"):
            raise ValueError("aCS must be a Pin instance")
        # 参数校验：debug 类型检查
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._spi = spi
        self._dc = aDC
        self._reset = aReset
        self._cs = aCS
        self._debug = debug
        self._size = SCREEN_SIZE
        self._offset = bytearray([0, 0])
        # 默认竖向，引脚朝上
        self._rotate = 0
        # 默认 RGB 颜色顺序
        self._rgb = True
        # 顶部固定区域
        self._tfa = 0
        # 底部固定区域
        self._bfa = 0
        self._color_data = bytearray(2)
        self._window_loc_data = bytearray(4)
        self._cs(1)

    # ========== 公共方法 ==========

    def _log(self, msg):
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 debug=True 时输出，ISR-safe: 否
        ==========================================
        Output debug log message.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when debug=True, ISR-safe: No
        """
        if self._debug:
            print("[ST7735] %s" % msg)

    def size(self):
        """
        获取当前屏幕尺寸
        Returns:
            tuple: (宽度, 高度)
        ==========================================
        Get current screen size.
        Returns:
            tuple: (width, height)
        """
        return self._size

    def on(self, on_off=True):
        """
        打开或关闭显示
        Args:
            on_off (bool): True 打开显示，False 关闭显示
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Turn display on or off.
        Args:
            on_off (bool): True to turn on, False to turn off
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 根据参数发送对应命令
        if on_off:
            self._writecommand(TFT.DISPON)
        else:
            self._writecommand(TFT.DISPOFF)

    def invertcolor(self, invert):
        """
        反转显示颜色（黑变白，白变黑）
        Args:
            invert (bool): True 开启反转，False 关闭反转
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Invert the display color (black becomes white).
        Args:
            invert (bool): True to invert, False to normal
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 根据参数发送反转开启或关闭命令
        if invert:
            self._writecommand(TFT.INVON)
        else:
            self._writecommand(TFT.INVOFF)

    def rgb(self, on_off=True):
        """
        设置颜色顺序为 RGB 或 BGR
        Args:
            on_off (bool): True 为 RGB 顺序，False 为 BGR 顺序
        Returns:
            None
        Notes:
            - 修改后立即更新 MADCTL 寄存器
            - ISR-safe: 否
        ==========================================
        Set color order to RGB or BGR.
        Args:
            on_off (bool): True for RGB, False for BGR
        Returns:
            None
        Notes:
            - Updates MADCTL register immediately
            - ISR-safe: No
        """
        self._rgb = on_off
        self._set_madctl()

    def rotation(self, rot):
        """
        设置屏幕旋转方向
        0 = 默认竖向（引脚朝上），1/2/3 依次顺时针旋转 90 度
        Args:
            rot (int): 旋转索引 (0-3)
        Returns:
            None
        Raises:
            ValueError: 旋转值超出 0-3 范围
        Notes:
            - 当竖向/横向切换时交换屏幕尺寸
            - ISR-safe: 否
        ==========================================
        Set screen rotation.
        0 = portrait (pins top), 1/2/3 rotate 90 deg clockwise each step.
        Args:
            rot (int): Rotation index (0-3)
        Returns:
            None
        Raises:
            ValueError: Rotation value out of 0-3 range
        Notes:
            - Swaps screen size when switching portrait/landscape
            - ISR-safe: No
        """
        # 参数校验：旋转值范围检查
        if not isinstance(rot, int):
            raise ValueError("rot must be int, got %s" % type(rot))
        if rot < 0 or rot >= 4:
            raise ValueError("rot must be 0-3, got %d" % rot)

        rotchange = self._rotate ^ rot
        self._rotate = rot
        # 当竖向与横向切换时（bit 0 变化），交换宽高
        if rotchange & 1:
            self._size = (self._size[1], self._size[0])
        self._set_madctl()

    def pixel(self, pos, color):
        """
        在指定位置绘制单个像素
        Args:
            pos (tuple): (x, y) 像素坐标
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - 超出屏幕范围的坐标将被忽略
            - ISR-safe: 否
        ==========================================
        Draw a single pixel at the given position.
        Args:
            pos (tuple): (x, y) pixel coordinate
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - Coordinates outside screen range are ignored
            - ISR-safe: No
        """
        # 边界检查：超出屏幕范围则忽略
        if 0 <= pos[0] < self._size[0] and 0 <= pos[1] < self._size[1]:
            self._set_window_point(pos)
            self._push_color(color)

    def text(self, pos, string, color, font, size=1, nowrap=False):
        """
        在指定位置绘制文本
        如果字符串超出屏幕右侧，默认会换行到下一行
        Args:
            pos (tuple): (x, y) 起始坐标
            string (str): 要绘制的文本字符串
            color (int): 16 位 RGB565 颜色值
            font (dict): 字体字典，包含 Start/End/Width/Height/Data 字段
            size (int|tuple): 字体缩放倍数，整数表示等比例缩放，元组表示 (x_scale, y_scale)
            nowrap (bool): True 禁止自动换行，超出部分截断
        Returns:
            None
        Notes:
            - 若 font 为 None 则直接返回
            - ISR-safe: 否
        ==========================================
        Draw text at the given position.
        If the string reaches the end of the display it wraps to next line.
        Args:
            pos (tuple): (x, y) start coordinate
            string (str): Text string to draw
            color (int): 16-bit RGB565 color value
            font (dict): Font dict with Start/End/Width/Height/Data
            size (int|tuple): Font scale, int for uniform scale, tuple for (x,y)
            nowrap (bool): True to disable auto wrap, truncate overflow
        Returns:
            None
        Notes:
            - Returns immediately if font is None
            - ISR-safe: No
        """
        # 字体为空则直接返回
        if font is None:
            return

        # 处理字体缩放参数：统一转为 (x_scale, y_scale) 元组
        if isinstance(size, int) or isinstance(size, float):
            wh = (size, size)
        else:
            wh = size

        px, py = pos
        width = wh[0] * font["Width"] + 1
        # 逐字符绘制
        for c in string:
            self.char((px, py), c, color, font, wh)
            px += width
            # 检查是否超出屏幕右侧
            if px + width > self._size[0]:
                if nowrap:
                    break
                else:
                    # 换行：y 下移，x 回到起始位置
                    py += font["Height"] * wh[1] + 1
                    px = pos[0]

    def char(self, pos, char, color, font, sizes):
        """
        使用指定字体在指定位置绘制单个字符
        Args:
            pos (tuple): (x, y) 起始坐标
            char (str): 单字符
            color (int): 16 位 RGB565 颜色值
            font (dict): 字体字典
            sizes (tuple): (x_scale, y_scale) 缩放倍数
        Returns:
            None
        Notes:
            - 若字符不在字体范围内则跳过
            - ISR-safe: 否
        ==========================================
        Draw a single character at the given position.
        Args:
            pos (tuple): (x, y) start coordinate
            char (str): Single character
            color (int): 16-bit RGB565 color value
            font (dict): Font dict
            sizes (tuple): (x_scale, y_scale)
        Returns:
            None
        Notes:
            - Skips character if outside font range
            - ISR-safe: No
        """
        # 字体为空则直接返回
        if font is None:
            return

        startchar = font["Start"]
        endchar = font["End"]
        ci = ord(char)

        # 字符在字体范围内才绘制
        if startchar <= ci <= endchar:
            fontw = font["Width"]
            fonth = font["Height"]
            ci = (ci - startchar) * fontw

            charA = font["Data"][ci : ci + fontw]
            px = pos[0]
            # 无缩放或缩小：使用 image 方法批量输出像素
            if sizes[0] <= 1 and sizes[1] <= 1:
                buf = bytearray(2 * fonth * fontw)
                for q in range(fontw):
                    c = charA[q]
                    for r in range(fonth):
                        if c & 0x01:
                            pos_buf = 2 * (r * fontw + q)
                            buf[pos_buf] = color >> 8
                            buf[pos_buf + 1] = color & 0xFF
                        c >>= 1
                self.image(pos[0], pos[1], pos[0] + fontw - 1, pos[1] + fonth - 1, buf)
            else:
                # 有缩放：逐点绘制矩形
                for c in charA:
                    py = pos[1]
                    for r in range(fonth):
                        if c & 0x01:
                            self.fillrect((px, py), sizes, color)
                        py += sizes[1]
                        c >>= 1
                    px += sizes[0]

    def line(self, start, end, color):
        """
        绘制直线（支持任意角度）
        水平/垂直线由 hline/vline 处理以提高效率
        Args:
            start (tuple): (x, y) 起始坐标
            end (tuple): (x, y) 结束坐标
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - 使用 Bresenham 算法绘制斜线
            - ISR-safe: 否
        ==========================================
        Draw a line between two points.
        Horizontal/vertical lines are forwarded to hline/vline for efficiency.
        Args:
            start (tuple): (x, y) start coordinate
            end (tuple): (x, y) end coordinate
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - Uses Bresenham algorithm for diagonal lines
            - ISR-safe: No
        """
        # 垂直线：委托给 vline
        if start[0] == end[0]:
            pnt = end if (end[1] < start[1]) else start
            self.vline(pnt, abs(end[1] - start[1]) + 1, color)
        # 水平线：委托给 hline
        elif start[1] == end[1]:
            pnt = end if end[0] < start[0] else start
            self.hline(pnt, abs(end[0] - start[0]) + 1, color)
        else:
            # Bresenham 直线算法
            px, py = start
            ex, ey = end
            dx = ex - px
            dy = ey - py
            inx = 1 if dx > 0 else -1
            iny = 1 if dy > 0 else -1

            dx = abs(dx)
            dy = abs(dy)
            if dx >= dy:
                dy <<= 1
                e = dy - dx
                dx <<= 1
                while px != ex:
                    self.pixel((px, py), color)
                    if e >= 0:
                        py += iny
                        e -= dx
                    e += dy
                    px += inx
            else:
                dx <<= 1
                e = dx - dy
                dy <<= 1
                while py != ey:
                    self.pixel((px, py), color)
                    if e >= 0:
                        px += inx
                        e -= dy
                    e += dx
                    py += iny

    def vline(self, start, length, color):
        """
        绘制垂直线
        Args:
            start (tuple): (x, y) 起始坐标
            length (int): 线段长度（可为负数）
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Draw a vertical line.
        Args:
            start (tuple): (x, y) start coordinate
            length (int): Line length (may be negative)
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 边界裁剪
        s = (clamp(start[0], 0, self._size[0]), clamp(start[1], 0, self._size[1]))
        e = (s[0], clamp(s[1] + length, 0, self._size[1]))
        # 确保较小的 y 在前
        if e[1] < s[1]:
            s, e = e, s
        self._set_window_loc(s, e)
        self._set_color(color)
        self._draw(length)

    def hline(self, start, length, color):
        """
        绘制水平线
        Args:
            start (tuple): (x, y) 起始坐标
            length (int): 线段长度（可为负数）
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Draw a horizontal line.
        Args:
            start (tuple): (x, y) start coordinate
            length (int): Line length (may be negative)
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 边界裁剪
        s = (clamp(start[0], 0, self._size[0]), clamp(start[1], 0, self._size[1]))
        e = (clamp(s[0] + length, 0, self._size[0]), s[1])
        # 确保较小的 x 在前
        if e[0] < s[0]:
            s, e = e, s
        self._set_window_loc(s, e)
        self._set_color(color)
        self._draw(length)

    def rect(self, start, size, color):
        """
        绘制空心矩形
        Args:
            start (tuple): (x, y) 左上角坐标
            size (tuple): (宽度, 高度)
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - 通过四条边线实现
            - ISR-safe: 否
        ==========================================
        Draw a hollow rectangle.
        Args:
            start (tuple): (x, y) top-left coordinate
            size (tuple): (width, height)
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - Implemented via four edge lines
            - ISR-safe: No
        """
        # 上边
        self.hline(start, size[0], color)
        # 下边
        self.hline((start[0], start[1] + size[1] - 1), size[0], color)
        # 左边
        self.vline(start, size[1], color)
        # 右边
        self.vline((start[0] + size[0] - 1, start[1]), size[1], color)

    def fillrect(self, start, size, color):
        """
        绘制填充矩形
        Args:
            start (tuple): (x, y) 左上角坐标
            size (tuple): (宽度, 高度)
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Draw a filled rectangle.
        Args:
            start (tuple): (x, y) top-left coordinate
            size (tuple): (width, height)
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 边界裁剪
        s = (clamp(start[0], 0, self._size[0]), clamp(start[1], 0, self._size[1]))
        e = (clamp(s[0] + size[0] - 1, 0, self._size[0]), clamp(s[1] + size[1] - 1, 0, self._size[1]))

        # 确保坐标顺序正确
        if e[0] < s[0]:
            tmp = e[0]
            e = (s[0], e[1])
            s = (tmp, s[1])
        if e[1] < s[1]:
            tmp = e[1]
            e = (e[0], s[1])
            s = (s[0], tmp)

        self._set_window_loc(s, e)
        numPixels = (e[0] - s[0] + 1) * (e[1] - s[1] + 1)
        self._set_color(color)
        self._draw(numPixels)

    def circle(self, pos, radius, color):
        """
        绘制空心圆
        Args:
            pos (tuple): (x, y) 圆心坐标
            radius (int): 半径（像素）
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - 使用中点圆算法（八分对称）
            - ISR-safe: 否
        ==========================================
        Draw a hollow circle.
        Args:
            pos (tuple): (x, y) center coordinate
            radius (int): Radius in pixels
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - Uses midpoint circle algorithm (8-way symmetry)
            - ISR-safe: No
        """
        # 设置颜色数据缓冲
        self._color_data[0] = color >> 8
        self._color_data[1] = color
        xend = int(0.7071 * radius) + 1
        rsq = radius * radius
        # 利用八分对称绘制圆周
        for x in range(xend):
            y = int(sqrt(rsq - x * x))
            xp = pos[0] + x
            yp = pos[1] + y
            xn = pos[0] - x
            yn = pos[1] - y
            xyp = pos[0] + y
            yxp = pos[1] + x
            xyn = pos[0] - y
            yxn = pos[1] - x

            # 八个对称点
            self._set_window_point((xp, yp))
            self._writedata(self._color_data)
            self._set_window_point((xp, yn))
            self._writedata(self._color_data)
            self._set_window_point((xn, yp))
            self._writedata(self._color_data)
            self._set_window_point((xn, yn))
            self._writedata(self._color_data)
            self._set_window_point((xyp, yxp))
            self._writedata(self._color_data)
            self._set_window_point((xyp, yxn))
            self._writedata(self._color_data)
            self._set_window_point((xyn, yxp))
            self._writedata(self._color_data)
            self._set_window_point((xyn, yxn))
            self._writedata(self._color_data)

    def fillcircle(self, pos, radius, color):
        """
        绘制填充圆
        Args:
            pos (tuple): (x, y) 圆心坐标
            radius (int): 半径（像素）
            color (int): 16 位 RGB565 颜色值
        Returns:
            None
        Notes:
            - 通过逐条水平扫描线（vline）实现填充
            - ISR-safe: 否
        ==========================================
        Draw a filled circle.
        Args:
            pos (tuple): (x, y) center coordinate
            radius (int): Radius in pixels
            color (int): 16-bit RGB565 color value
        Returns:
            None
        Notes:
            - Implemented via horizontal scan lines (vline)
            - ISR-safe: No
        """
        rsq = radius * radius
        # 逐列绘制垂直扫描线
        for x in range(radius):
            y = int(sqrt(rsq - x * x))
            y0 = pos[1] - y
            ey = y0 + y * 2
            y0 = clamp(y0, 0, self._size[1])
            ln = abs(ey - y0) + 1

            self.vline((pos[0] + x, y0), ln, color)
            self.vline((pos[0] - x, y0), ln, color)

    def fill(self, color=BLACK):
        """
        用指定颜色填充整个屏幕
        Args:
            color (int): 16 位 RGB565 颜色值，默认黑色
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Fill entire screen with given color.
        Args:
            color (int): 16-bit RGB565 color, default BLACK
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        self.fillrect((0, 0), self._size, color)

    def image(self, x0, y0, x1, y1, data):
        """
        在指定矩形区域绘制位图数据
        Args:
            x0 (int): 左上角 x 坐标
            y0 (int): 左上角 y 坐标
            x1 (int): 右下角 x 坐标
            y1 (int): 右下角 y 坐标
            data (bytearray): RGB565 格式的像素数据
        Returns:
            None
        Notes:
            - 数据必须为连续的 RGB565 字节流
            - ISR-safe: 否
        ==========================================
        Draw bitmap data in the specified rectangular area.
        Args:
            x0 (int): Top-left x coordinate
            y0 (int): Top-left y coordinate
            x1 (int): Bottom-right x coordinate
            y1 (int): Bottom-right y coordinate
            data (bytearray): Pixel data in RGB565 format
        Returns:
            None
        Notes:
            - Data must be a contiguous RGB565 byte stream
            - ISR-safe: No
        """
        self._set_window_loc((x0, y0), (x1, y1))
        self._writedata(data)

    def setvscroll(self, tfa, bfa):
        """
        设置垂直滚动区域
        Args:
            tfa (int): 顶部固定区域高度（行数）
            bfa (int): 底部固定区域高度（行数）
        Returns:
            None
        Notes:
            - 中间区域为可滚动区域
            - 屏幕总高度最大 162 行
            - ISR-safe: 否
        ==========================================
        Set vertical scroll area.
        Args:
            tfa (int): Top fixed area height in lines
            bfa (int): Bottom fixed area height in lines
        Returns:
            None
        Notes:
            - Middle area is the scrollable region
            - Maximum total height is 162 lines
            - ISR-safe: No
        """
        # 发送垂直滚动定义命令
        self._writecommand(TFT.VSCRDEF)
        data2 = bytearray([0, tfa])
        self._writedata(data2)
        data2[1] = 162 - tfa - bfa
        self._writedata(data2)
        data2[1] = bfa
        self._writedata(data2)
        self._tfa = tfa
        self._bfa = bfa

    def vscroll(self, value):
        """
        设置垂直滚动偏移
        Args:
            value (int): 滚动偏移量
        Returns:
            None
        Notes:
            - 偏移量受顶部/底部固定区域限制
            - ISR-safe: 否
        ==========================================
        Set vertical scroll offset.
        Args:
            value (int): Scroll offset
        Returns:
            None
        Notes:
            - Offset is constrained by top/bottom fixed areas
            - ISR-safe: No
        """
        # 计算实际滚动地址并限制范围
        a = value + self._tfa
        if a + self._bfa > 162:
            a = 162 - self._bfa
        self._write_scroll_addr(a)

    # ========== 初始化方法 ==========

    def initb(self):
        """
        初始化蓝标版本 ST7735 显示屏
        配置寄存器序列：复位、睡眠退出、颜色模式、帧率、电源、Gamma 等
        Returns:
            None
        Notes:
            - 屏幕尺寸会调整为原尺寸加偏移（用于蓝标版本）
            - ISR-safe: 否
        ==========================================
        Initialize blue tab version of ST7735 display.
        Configures register sequence: reset, sleep out, color mode, frame rate, power, gamma.
        Returns:
            None
        Notes:
            - Screen size adjusted with offsets for blue tab
            - ISR-safe: No
        """
        self._size = (SCREEN_SIZE[0] + 2, SCREEN_SIZE[1] + 1)
        self._reset_device()
        # 软件复位
        self._writecommand(TFT.SWRESET)
        time.sleep_us(50)
        # 退出睡眠模式
        self._writecommand(TFT.SLPOUT)
        time.sleep_us(500)

        data1 = bytearray(1)
        # 设置颜色模式：16 位色
        self._writecommand(TFT.COLMOD)
        data1[0] = 0x05
        self._writedata(data1)
        time.sleep_us(10)

        # 设置帧率：最快刷新，6 行前沿，3 行后沿
        data3 = bytearray([0x00, 0x06, 0x03])
        self._writecommand(TFT.FRMCTR1)
        self._writedata(data3)
        time.sleep_us(10)

        # 设置 MADCTL：行列地址模式，底部到顶部刷新
        self._writecommand(TFT.MADCTL)
        data1[0] = 0x08
        self._writedata(data1)

        data2 = bytearray(2)
        # 显示设置：1 时钟周期非重叠，2 周期门极上升，3 周期振荡均衡
        self._writecommand(TFT.DISSET5)
        data2[0] = 0x15
        data2[1] = 0x02
        self._writedata(data2)

        # 显示反转控制：行反转模式
        self._writecommand(TFT.INVCTR)
        data1[0] = 0x00
        self._writedata(data1)

        # 电源控制序列
        self._writecommand(TFT.PWCTR1)
        # GVDD = 4.7V
        data2[0] = 0x02
        # 1.0uA
        data2[1] = 0x70
        self._writedata(data2)
        time.sleep_us(10)

        self._writecommand(TFT.PWCTR2)
        # VGH = 14.7V, VGL = -7.35V
        data1[0] = 0x05
        self._writedata(data1)

        self._writecommand(TFT.PWCTR3)
        # 运放电流小
        data2[0] = 0x01
        # 升压频率
        data2[1] = 0x02
        self._writedata(data2)

        self._writecommand(TFT.VMCTR1)
        # VCOMH = 4V
        data2[0] = 0x3C
        # VCOML = -1.1V
        data2[1] = 0x38
        self._writedata(data2)
        time.sleep_us(10)

        self._writecommand(TFT.PWCTR6)
        data2[0] = 0x11
        data2[1] = 0x15
        self._writedata(data2)

        # Gamma 校正（正极性）
        dataGMCTRP = bytearray([0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D, 0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10])
        self._writecommand(TFT.GMCTRP1)
        self._writedata(dataGMCTRP)

        # Gamma 校正（负极性）
        dataGMCTRN = bytearray([0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10])
        self._writecommand(TFT.GMCTRN1)
        self._writedata(dataGMCTRN)
        time.sleep_us(10)

        # 设置列地址：从第 2 列开始
        self._writecommand(TFT.CASET)
        self._window_loc_data[0] = 0x00
        self._window_loc_data[1] = 2
        self._window_loc_data[2] = 0x00
        self._window_loc_data[3] = self._size[0] - 1
        self._writedata(self._window_loc_data)

        # 设置行地址：从第 2 行开始（因有偏移）
        self._writecommand(TFT.RASET)
        self._window_loc_data[1] = 1
        self._window_loc_data[3] = self._size[1] - 1
        self._writedata(self._window_loc_data)

        # 正常显示模式
        self._writecommand(TFT.NORON)
        time.sleep_us(10)

        self._writecommand(TFT.RAMWR)
        time.sleep_us(500)

        # 开启显示
        self._writecommand(TFT.DISPON)
        self._cs(1)
        time.sleep_us(500)

    def initr(self):
        """
        初始化红标版本 ST7735 显示屏
        配置寄存器序列：复位、睡眠退出、帧率、电源、Gamma、显示开启等
        Returns:
            None
        Notes:
            - 屏幕尺寸保持默认
            - ISR-safe: 否
        ==========================================
        Initialize red tab version of ST7735 display.
        Returns:
            None
        Notes:
            - Screen size remains default
            - ISR-safe: No
        """
        self._reset_device()

        # 软件复位
        self._writecommand(TFT.SWRESET)
        time.sleep_us(150)
        # 退出睡眠模式
        self._writecommand(TFT.SLPOUT)
        time.sleep_us(500)

        # 帧率控制：最快刷新，6 行前沿，3 行后沿
        data3 = bytearray([0x01, 0x2C, 0x2D])
        self._writecommand(TFT.FRMCTR1)
        self._writedata(data3)

        self._writecommand(TFT.FRMCTR2)
        self._writedata(data3)

        data6 = bytearray([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])
        self._writecommand(TFT.FRMCTR3)
        self._writedata(data6)
        time.sleep_us(10)

        data1 = bytearray(1)
        # 显示反转控制：行反转
        self._writecommand(TFT.INVCTR)
        data1[0] = 0x07
        self._writedata(data1)

        # 电源控制序列
        self._writecommand(TFT.PWCTR1)
        data3[0] = 0xA2
        data3[1] = 0x02
        data3[2] = 0x84
        self._writedata(data3)

        self._writecommand(TFT.PWCTR2)
        data1[0] = 0xC5
        self._writedata(data1)

        data2 = bytearray(2)
        self._writecommand(TFT.PWCTR3)
        data2[0] = 0x0A
        data2[1] = 0x00
        self._writedata(data2)

        self._writecommand(TFT.PWCTR4)
        data2[0] = 0x8A
        data2[1] = 0x2A
        self._writedata(data2)

        self._writecommand(TFT.PWCTR5)
        data2[0] = 0x8A
        data2[1] = 0xEE
        self._writedata(data2)

        self._writecommand(TFT.VMCTR1)
        data1[0] = 0x0E
        self._writedata(data1)

        # 关闭颜色反转
        self._writecommand(TFT.INVOFF)

        # 设置 MADCTL 寄存器
        self._writecommand(TFT.MADCTL)
        data1[0] = 0xC8
        self._writedata(data1)

        # 设置颜色模式：16 位色
        self._writecommand(TFT.COLMOD)
        data1[0] = 0x05
        self._writedata(data1)

        # 设置列地址范围
        self._writecommand(TFT.CASET)
        self._window_loc_data[0] = 0x00
        self._window_loc_data[1] = 0x00
        self._window_loc_data[2] = 0x00
        self._window_loc_data[3] = self._size[0] - 1
        self._writedata(self._window_loc_data)

        # 设置行地址范围
        self._writecommand(TFT.RASET)
        self._window_loc_data[3] = self._size[1] - 1
        self._writedata(self._window_loc_data)

        # Gamma 校正（正极性）
        dataGMCTRP = bytearray([0x0F, 0x1A, 0x0F, 0x18, 0x2F, 0x28, 0x20, 0x22, 0x1F, 0x1B, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])
        self._writecommand(TFT.GMCTRP1)
        self._writedata(dataGMCTRP)

        # Gamma 校正（负极性）
        dataGMCTRN = bytearray([0x0F, 0x1B, 0x0F, 0x17, 0x33, 0x2C, 0x29, 0x2E, 0x30, 0x30, 0x39, 0x3F, 0x00, 0x07, 0x03, 0x10])
        self._writecommand(TFT.GMCTRN1)
        self._writedata(dataGMCTRN)
        time.sleep_us(10)

        # 开启显示
        self._writecommand(TFT.DISPON)
        time.sleep_us(100)

        # 正常显示模式
        self._writecommand(TFT.NORON)
        time.sleep_us(10)

        self._cs(1)

    def initb2(self):
        """
        初始化另一种蓝标版本 ST7735 显示屏
        与 initb() 类似但帧率控制序列不同（3 次 FRMCTR 写入），偏移量不同
        Returns:
            None
        Notes:
            - 偏移量为 (2, 1) 而非 (0, 1)
            - ISR-safe: 否
        ==========================================
        Initialize another blue tab version of ST7735 display.
        Similar to initb() but different frame rate sequence and offsets.
        Returns:
            None
        Notes:
            - Offsets are (2, 1) instead of (0, 1)
            - ISR-safe: No
        """
        self._size = (SCREEN_SIZE[0] + 2, SCREEN_SIZE[1] + 1)
        self._offset[0] = 2
        self._offset[1] = 1
        self._reset_device()
        # 软件复位
        self._writecommand(TFT.SWRESET)
        time.sleep_us(50)
        # 退出睡眠模式
        self._writecommand(TFT.SLPOUT)
        time.sleep_us(500)

        # 帧率控制（连续写入 3 次）
        data3 = bytearray([0x01, 0x2C, 0x2D])
        self._writecommand(TFT.FRMCTR1)
        self._writedata(data3)
        time.sleep_us(10)

        self._writecommand(TFT.FRMCTR2)
        self._writedata(data3)
        time.sleep_us(10)

        self._writecommand(TFT.FRMCTR3)
        self._writedata(data3)
        time.sleep_us(10)

        # 显示反转控制
        self._writecommand(TFT.INVCTR)
        data1 = bytearray(1)
        data1[0] = 0x07
        self._writedata(data1)

        # 电源控制序列
        self._writecommand(TFT.PWCTR1)
        data3[0] = 0xA2
        data3[1] = 0x02
        data3[2] = 0x84
        self._writedata(data3)
        time.sleep_us(10)

        self._writecommand(TFT.PWCTR2)
        data1[0] = 0xC5
        self._writedata(data1)

        self._writecommand(TFT.PWCTR3)
        data2 = bytearray(2)
        data2[0] = 0x0A
        data2[1] = 0x00
        self._writedata(data2)

        self._writecommand(TFT.PWCTR4)
        data2[0] = 0x8A
        data2[1] = 0x2A
        self._writedata(data2)

        self._writecommand(TFT.PWCTR5)
        data2[0] = 0x8A
        data2[1] = 0xEE
        self._writedata(data2)

        self._writecommand(TFT.VMCTR1)
        data1[0] = 0x0E
        self._writedata(data1)
        time.sleep_us(10)

        # 设置 MADCTL
        self._writecommand(TFT.MADCTL)
        data1[0] = 0xC8
        self._writedata(data1)

        # Gamma 校正（正极性）
        dataGMCTRP = bytearray([0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D, 0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10])
        self._writecommand(TFT.GMCTRP1)
        self._writedata(dataGMCTRP)

        # Gamma 校正（负极性）
        dataGMCTRN = bytearray([0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10])
        self._writecommand(TFT.GMCTRN1)
        self._writedata(dataGMCTRN)
        time.sleep_us(10)

        # 设置列地址：从第 2 列开始
        self._writecommand(TFT.CASET)
        self._window_loc_data[0] = 0x00
        self._window_loc_data[1] = 0x02
        self._window_loc_data[2] = 0x00
        self._window_loc_data[3] = self._size[0] - 1
        self._writedata(self._window_loc_data)

        # 设置行地址：从第 1 行开始
        self._writecommand(TFT.RASET)
        self._window_loc_data[1] = 0x01
        self._window_loc_data[3] = self._size[1] - 1
        self._writedata(self._window_loc_data)

        data1 = bytearray(1)
        # 设置颜色模式：16 位色
        self._writecommand(TFT.COLMOD)
        data1[0] = 0x05
        self._writedata(data1)
        time.sleep_us(10)

        # 正常显示模式
        self._writecommand(TFT.NORON)
        time.sleep_us(10)

        self._writecommand(TFT.RAMWR)
        time.sleep_us(500)

        # 开启显示
        self._writecommand(TFT.DISPON)
        self._cs(1)
        time.sleep_us(500)

    def initg(self):
        """
        初始化绿标版本 ST7735 显示屏
        配置寄存器序列：复位、睡眠退出、帧率、电源、Gamma、显示开启等
        Returns:
            None
        Notes:
            - 偏移量 (0, 0)，列地址从第 1 列开始
            - ISR-safe: 否
        ==========================================
        Initialize green tab version of ST7735 display.
        Returns:
            None
        Notes:
            - Offsets (0, 0), column address starts from 1
            - ISR-safe: No
        """
        self._reset_device()

        # 软件复位
        self._writecommand(TFT.SWRESET)
        time.sleep_us(150)
        # 退出睡眠模式
        self._writecommand(TFT.SLPOUT)
        time.sleep_us(255)

        # 帧率控制：最快刷新，6 行前沿，3 行后沿
        data3 = bytearray([0x01, 0x2C, 0x2D])
        self._writecommand(TFT.FRMCTR1)
        self._writedata(data3)

        self._writecommand(TFT.FRMCTR2)
        self._writedata(data3)

        data6 = bytearray([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])
        self._writecommand(TFT.FRMCTR3)
        self._writedata(data6)
        time.sleep_us(10)

        # 显示反转控制：行反转
        self._writecommand(TFT.INVCTR)
        self._writedata(bytearray([0x07]))
        # 电源控制序列
        self._writecommand(TFT.PWCTR1)
        data3[0] = 0xA2
        data3[1] = 0x02
        data3[2] = 0x84
        self._writedata(data3)

        self._writecommand(TFT.PWCTR2)
        self._writedata(bytearray([0xC5]))

        data2 = bytearray(2)
        self._writecommand(TFT.PWCTR3)
        data2[0] = 0x0A
        data2[1] = 0x00
        self._writedata(data2)

        self._writecommand(TFT.PWCTR4)
        data2[0] = 0x8A
        data2[1] = 0x2A
        self._writedata(data2)

        self._writecommand(TFT.PWCTR5)
        data2[0] = 0x8A
        data2[1] = 0xEE
        self._writedata(data2)

        self._writecommand(TFT.VMCTR1)
        self._writedata(bytearray([0x0E]))

        # 关闭颜色反转
        self._writecommand(TFT.INVOFF)

        # 设置 MADCTL（使用当前旋转设置）
        self._set_madctl()

        # 设置颜色模式：16 位色
        self._writecommand(TFT.COLMOD)
        self._writedata(bytearray([0x05]))

        # 设置列地址：从第 1 列开始
        self._writecommand(TFT.CASET)
        self._window_loc_data[0] = 0x00
        self._window_loc_data[1] = 0x01
        self._window_loc_data[2] = 0x00
        self._window_loc_data[3] = self._size[0] - 1
        self._writedata(self._window_loc_data)

        # 设置行地址
        self._writecommand(TFT.RASET)
        self._window_loc_data[3] = self._size[1] - 1
        self._writedata(self._window_loc_data)

        # Gamma 校正（正极性）
        dataGMCTRP = bytearray([0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D, 0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10])
        self._writecommand(TFT.GMCTRP1)
        self._writedata(dataGMCTRP)

        # Gamma 校正（负极性）
        dataGMCTRN = bytearray([0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10])
        self._writecommand(TFT.GMCTRN1)
        self._writedata(dataGMCTRN)

        # 正常显示模式
        self._writecommand(TFT.NORON)
        time.sleep_us(10)

        # 开启显示
        self._writecommand(TFT.DISPON)
        time.sleep_us(100)

        self._cs(1)

    # ========== 属性访问器 ==========

    def get_rotation(self):
        """
        获取当前旋转方向索引
        Returns:
            int: 旋转索引 (0-3)
        ==========================================
        Get current rotation index.
        Returns:
            int: Rotation index (0-3)
        """
        return self._rotate

    def get_rgb(self):
        """
        获取当前颜色顺序
        Returns:
            bool: True 为 RGB 顺序，False 为 BGR 顺序
        ==========================================
        Get current color order.
        Returns:
            bool: True for RGB, False for BGR
        """
        return self._rgb

    # ========== 私有方法 ==========

    def _set_color(self, color):
        """
        设置当前绘制颜色并预计算批量写入缓冲
        Args:
            color (int): 16 位 RGB565 颜色值
        Notes:
            - 副作用：修改 self._color_data 和 self._buf
        """
        # 拆分颜色高低字节到缓冲
        self._color_data[0] = color >> 8
        self._color_data[1] = color
        # 预创建批量写入缓冲（32 个像素一组的字节序列）
        self._buf = bytes(self._color_data) * 32

    def _draw(self, pixels):
        """
        将当前颜色连续写入设备指定次数（批量像素填充）
        Args:
            pixels (int): 要写入的像素数量
        Notes:
            - 副作用：通过 SPI 写入像素数据到显示 RAM
        """
        # 设置数据模式（DC 高电平）
        self._dc(1)
        # 选中芯片（CS 低电平）
        self._cs(0)
        # 以 32 像素为一组批量写入
        for i in range(pixels // 32):
            self._spi.write(self._buf)
        # 处理剩余不足 32 的像素
        rest = int(pixels) % 32
        if rest > 0:
            buf2 = bytes(self._color_data) * rest
            self._spi.write(buf2)
        # 取消片选
        self._cs(1)

    def _set_window_point(self, pos):
        """
        设置单点绘制窗口（用于逐像素绘制）
        Args:
            pos (tuple): (x, y) 像素坐标
        Notes:
            - 副作用：通过 SPI 发送 CASET/RASET/RAMWR 命令序列
        """
        # 计算考虑偏移后的实际坐标
        x = self._offset[0] + int(pos[0])
        y = self._offset[1] + int(pos[1])
        # 设置列地址（起点 = 终点 = x）
        self._writecommand(TFT.CASET)
        self._window_loc_data[0] = self._offset[0]
        self._window_loc_data[1] = x
        self._window_loc_data[2] = self._offset[0]
        self._window_loc_data[3] = x
        self._writedata(self._window_loc_data)

        # 设置行地址（起点 = 终点 = y）
        self._writecommand(TFT.RASET)
        self._window_loc_data[0] = self._offset[1]
        self._window_loc_data[1] = y
        self._window_loc_data[2] = self._offset[1]
        self._window_loc_data[3] = y
        self._writedata(self._window_loc_data)
        # 写 RAM 命令
        self._writecommand(TFT.RAMWR)

    def _set_window_loc(self, pos0, pos1):
        """
        设置矩形绘制窗口（用于区域填充）
        Args:
            pos0 (tuple): (x0, y0) 左上角坐标
            pos1 (tuple): (x1, y1) 右下角坐标
        Notes:
            - 副作用：通过 SPI 发送 CASET/RASET/RAMWR 命令序列
        """
        # 设置列地址范围
        self._writecommand(TFT.CASET)
        self._window_loc_data[0] = self._offset[0]
        self._window_loc_data[1] = self._offset[0] + int(pos0[0])
        self._window_loc_data[2] = self._offset[0]
        self._window_loc_data[3] = self._offset[0] + int(pos1[0])
        self._writedata(self._window_loc_data)

        # 设置行地址范围
        self._writecommand(TFT.RASET)
        self._window_loc_data[0] = self._offset[1]
        self._window_loc_data[1] = self._offset[1] + int(pos0[1])
        self._window_loc_data[2] = self._offset[1]
        self._window_loc_data[3] = self._offset[1] + int(pos1[1])
        self._writedata(self._window_loc_data)

        # 写 RAM 命令
        self._writecommand(TFT.RAMWR)

    def _writecommand(self, command):
        """
        通过 SPI 发送命令字节到设备
        Args:
            command (int): 8 位命令字节
        Notes:
            - DC = 0 表示命令模式
            - 副作用：CS 拉低选中芯片，完毕后 CS 拉高释放
        """
        # 命令模式：DC 低电平
        self._dc(0)
        # 选中芯片
        self._cs(0)
        self._spi.write(bytearray([command]))
        # 释放片选
        self._cs(1)

    def _writedata(self, data):
        """
        通过 SPI 发送数据到设备
        Args:
            data (bytearray|bytes): 数据字节序列
        Notes:
            - DC = 1 表示数据模式
            - 副作用：CS 拉低选中芯片，完毕后 CS 拉高释放
        """
        # 数据模式：DC 高电平
        self._dc(1)
        # 选中芯片
        self._cs(0)
        self._spi.write(data)
        # 释放片选
        self._cs(1)

    def _push_color(self, color):
        """
        将单个颜色值推送到当前窗口
        Args:
            color (int): 16 位 RGB565 颜色值
        Notes:
            - 副作用：修改 self._color_data，通过 SPI 写入
        """
        # 拆分颜色高低字节
        self._color_data[0] = color >> 8
        self._color_data[1] = color
        self._writedata(self._color_data)

    def _set_madctl(self):
        """
        设置 MADCTL 寄存器（控制旋转方向和 RGB/BGR 顺序）
        Notes:
            - 副作用：通过 SPI 发送 MADCTL 命令和参数
            - 根据 self._rgb 和 self._rotate 计算寄存器值
        """
        self._writecommand(TFT.MADCTL)
        rgb = TFT_RGB if self._rgb else TFT_BGR
        self._writedata(bytearray([TFT_ROTATIONS[self._rotate] | rgb]))

    def _reset_device(self):
        """
        通过硬件引脚复位设备
        复位时序：高→低→高（各 500us）
        Notes:
            - 副作用：操作 Reset 引脚电平
        """
        # 复位引脚时序：高→低→高
        self._dc(0)
        self._reset(1)
        time.sleep_us(500)
        self._reset(0)
        time.sleep_us(500)
        self._reset(1)
        time.sleep_us(500)

    def _write_scroll_addr(self, addr):
        """
        设置垂直滚动起始地址
        Args:
            addr (int): 滚动起始地址
        Notes:
            - 副作用：通过 SPI 发送 VSCSAD 命令和地址参数
        """
        self._writecommand(TFT.VSCSAD)
        data2 = bytearray([addr >> 8, addr & 0xFF])
        self._writedata(data2)

    # ========== 资源释放 ==========

    def deinit(self):
        """
        释放硬件资源
        关闭显示，释放片选引脚，使设备进入低功耗状态
        Returns:
            None
        Notes:
            - 副作用：发送 DISPOFF 命令，CS 拉高
            - 可多次调用而不产生错误
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Turns off display, releases chip select, puts device in low-power state.
        Returns:
            None
        Notes:
            - Side effects: Sends DISPOFF command, CS high
            - Safe to call multiple times
            - ISR-safe: No
        """
        try:
            self._writecommand(TFT.DISPOFF)
            self._cs(1)
            self._log("ST7735 deinitialized")
        except Exception:
            # 静默处理释放错误，避免二次异常
            pass


# ======================================== 初始化配置 ==========================================
# 驱动文件不在此区域实例化硬件

# ========================================  主程序  ===========================================
# 驱动文件不在此区域运行主程序
