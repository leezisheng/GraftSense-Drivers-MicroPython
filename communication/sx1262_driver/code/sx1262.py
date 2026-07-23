# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : jgromes
# @File    : sx1262.py
# @Description : SX1262 LoRa radio transceiver driver, SPI interface
# @License : MIT
# pylint: disable=wildcard-import,unused-wildcard-import,undefined-variable

__version__ = "1.0.0"
__author__ = "jgromes"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import micropython

micropython.alloc_emergency_exception_buf(100)

# ======================================== 导入相关模块 =========================================
from _sx126x import *
from sx126x import SX126X

# ======================================== 全局变量 ============================================
# 全局复用缓冲区（用于热点 I/O 路径）
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================
# 本驱动无独立的类外功能函数，所有功能由 SX1262 类提供

# ======================================== 自定义类 ============================================

# SX1262 使用的 PA 配置参数
_SX126X_PA_CONFIG_SX1262 = micropython.const(0x00)


class SX1262(SX126X):
    """
    SX1262 LoRa 射频收发器驱动类

    基于 SX126X 基类实现，支持 LoRa 和 GFSK 两种调制模式，
    提供阻塞和非阻塞两种通信模式。
    Attributes:
        blocking (bool): 是否使用阻塞模式
        _callbackFunction (callable): 非阻塞模式下的回调函数
        _txIq (bool): TX IQ 反转标志
        _rxIq (bool): RX IQ 反转标志
        _preambleDetectorLength (int): 前导码检测长度
    Methods:
        begin(): 初始化 LoRa 模式
        beginFSK(): 初始化 GFSK 模式
        setFrequency(): 设置频率
        setOutputPower(): 设置发射功率
        recv(): 接收数据
        send(): 发送数据
        setBlockingCallback(): 设置阻塞/非阻塞模式及回调
        deinit(): 释放硬件资源
    Notes:
        - 依赖 SX126X 基类提供底层 SPI 通信
        - 非阻塞模式下通过 IRQ 回调接收数据
        - 阻塞模式下发送/接收为同步操作
    ==========================================
    SX1262 LoRa radio transceiver driver.

    Based on SX126X base class, supports LoRa and GFSK modulation modes,
    providing both blocking and non-blocking communication.
    Attributes:
        blocking (bool): Whether blocking mode is active
        _callbackFunction (callable): Callback function in non-blocking mode
        _txIq (bool): TX IQ inversion flag
        _rxIq (bool): RX IQ inversion flag
        _preambleDetectorLength (int): Preamble detector length
    Methods:
        begin(): Initialize LoRa mode
        beginFSK(): Initialize GFSK mode
        setFrequency(): Set operating frequency
        setOutputPower(): Set transmit power
        recv(): Receive data
        send(): Transmit data
        setBlockingCallback(): Configure blocking/non-blocking mode with callback
        deinit(): Release hardware resources
    Notes:
        - Dependent on SX126X base class for low-level SPI communication
        - Non-blocking mode uses IRQ callback for data reception
        - Blocking mode send/receive are synchronous operations
    """

    # 类级常量：中断标志位
    TX_DONE = SX126X_IRQ_TX_DONE
    RX_DONE = SX126X_IRQ_RX_DONE
    ADDR_FILT_OFF = SX126X_GFSK_ADDRESS_FILT_OFF
    ADDR_FILT_NODE = SX126X_GFSK_ADDRESS_FILT_NODE
    ADDR_FILT_NODE_BROAD = SX126X_GFSK_ADDRESS_FILT_NODE_BROADCAST
    PREAMBLE_DETECT_OFF = SX126X_GFSK_PREAMBLE_DETECT_OFF
    PREAMBLE_DETECT_8 = SX126X_GFSK_PREAMBLE_DETECT_8
    PREAMBLE_DETECT_16 = SX126X_GFSK_PREAMBLE_DETECT_16
    PREAMBLE_DETECT_24 = SX126X_GFSK_PREAMBLE_DETECT_24
    PREAMBLE_DETECT_32 = SX126X_GFSK_PREAMBLE_DETECT_32
    # 状态码字典引用
    STATUS = ERROR

    def __init__(self, spi_bus: int, clk: int, mosi: int, miso: int, cs: int, irq: int, rst: int, gpio: int) -> None:
        """
        初始化 SX1262 驱动

        所有参数通过基类 SX126X 完成底层硬件初始化。
        Args:
            spi_bus (int): SPI 总线编号（如 0 或 1）
            clk (int): SPI 时钟引脚号
            mosi (int): SPI MOSI 数据引脚号
            miso (int): SPI MISO 数据引脚号
            cs (int): 片选引脚号
            irq (int): 中断请求引脚号
            rst (int): 复位引脚号
            gpio (int): 忙状态监测引脚号
        Raises:
            ValueError: 参数类型错误
        Notes:
            - 实际 SPI 和 Pin 对象由 SX126X 基类创建
            - 非阻塞回调默认设为空函数
        ==========================================
        Initialize SX1262 driver.

        All parameters are passed to the SX126X base class for low-level
        hardware initialization.
        Args:
            spi_bus (int): SPI bus number (e.g. 0 or 1)
            clk (int): SPI clock pin number
            mosi (int): SPI MOSI data pin number
            miso (int): SPI MISO data pin number
            cs (int): Chip select pin number
            irq (int): Interrupt request pin number
            rst (int): Reset pin number
            gpio (int): Busy status monitoring pin number
        Raises:
            ValueError: Invalid parameter type
        Notes:
            - Actual SPI and Pin objects are created by SX126X base class
            - Non-blocking callback defaults to dummy function
        """
        # 参数校验：确保所有引脚和总线参数为整数类型
        if not isinstance(spi_bus, int):
            raise ValueError("spi_bus must be int, got %s" % type(spi_bus))
        if not isinstance(clk, int):
            raise ValueError("clk must be int, got %s" % type(clk))
        if not isinstance(mosi, int):
            raise ValueError("mosi must be int, got %s" % type(mosi))
        if not isinstance(miso, int):
            raise ValueError("miso must be int, got %s" % type(miso))
        if not isinstance(cs, int):
            raise ValueError("cs must be int, got %s" % type(cs))
        if not isinstance(irq, int):
            raise ValueError("irq must be int, got %s" % type(irq))
        if not isinstance(rst, int):
            raise ValueError("rst must be int, got %s" % type(rst))
        if not isinstance(gpio, int):
            raise ValueError("gpio must be int, got %s" % type(gpio))

        super().__init__(spi_bus, clk, mosi, miso, cs, irq, rst, gpio)
        # 默认阻塞模式标志
        self.blocking = True
        # 默认回调为空函数
        self._callbackFunction = self._dummyFunction
        # 初始化 IQ 配置
        self._txIq = False
        self._rxIq = False
        # 默认前导码检测长度
        self._preambleDetectorLength = SX126X_GFSK_PREAMBLE_DETECT_16
        # debug 日志开关
        self._debug = False

    def _log(self, msg: str) -> None:
        """
        条件日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - ISR-safe: 否（涉及 print 和字符串拼接）
        ==========================================
        Conditional log output.
        Args:
            msg (str): Log message
        Notes:
            - ISR-safe: No (uses print and string concatenation)
        """
        if self._debug:
            print("[SX1262] %s" % msg)

    def begin(
        self,
        freq: float = 434.0,
        bw: float = 125.0,
        sf: int = 9,
        cr: int = 7,
        syncWord: int = SX126X_SYNC_WORD_PRIVATE,
        power: int = 14,
        currentLimit: float = 60.0,
        preambleLength: int = 8,
        implicit: bool = False,
        implicitLen: int = 0xFF,
        crcOn: bool = True,
        txIq: bool = False,
        rxIq: bool = False,
        tcxoVoltage: float = 1.6,
        useRegulatorLDO: bool = False,
        blocking: bool = True,
    ) -> int:
        """
        初始化 LoRa 调制模式

        依次配置扩频因子、带宽、编码率、同步字等 LoRa 参数。
        Args:
            freq (float): 工作频率（MHz），范围 150.0 ~ 960.0
            bw (float): 带宽（kHz）
            sf (int): 扩频因子，范围 5 ~ 12
            cr (int): 编码率，范围 5 ~ 8
            syncWord (int): 同步字，私有网络 0x12 或公共网络 0x34
            power (int): 发射功率（dBm），范围 -9 ~ 22
            currentLimit (float): 电流限制（mA）
            preambleLength (int): 前导码长度
            implicit (bool): 是否使用隐式报头
            implicitLen (int): 隐式报头模式下的数据包长度
            crcOn (bool): 是否启用 CRC 校验
            txIq (bool): 是否反转 TX IQ
            rxIq (bool): 是否反转 RX IQ
            tcxoVoltage (float): TCXO 电压，0.0 表示无 TCXO
            useRegulatorLDO (bool): 是否使用 LDO 稳压器（否则用 DCDC）
            blocking (bool): 是否使用阻塞模式
        Returns:
            int: 状态码，ERR_NONE 表示成功
        Notes:
            - 调用基类方法完成底层寄存器配置
            - 阻塞模式下调用 standby()，非阻塞模式下调用 startReceive()
        ==========================================
        Initialize LoRa modulation mode.

        Configures spreading factor, bandwidth, coding rate, sync word,
        and other LoRa parameters in sequence.
        Args:
            freq (float): Operating frequency in MHz, range 150.0 ~ 960.0
            bw (float): Bandwidth in kHz
            sf (int): Spreading factor, range 5 ~ 12
            cr (int): Coding rate, range 5 ~ 8
            syncWord (int): Sync word, 0x12 for private or 0x34 for public
            power (int): Transmit power in dBm, range -9 ~ 22
            currentLimit (float): Current limit in mA
            preambleLength (int): Preamble length
            implicit (bool): Whether to use implicit header
            implicitLen (int): Packet length in implicit header mode
            crcOn (bool): Whether to enable CRC
            txIq (bool): Whether to invert TX IQ
            rxIq (bool): Whether to invert RX IQ
            tcxoVoltage (float): TCXO voltage, 0.0 means no TCXO
            useRegulatorLDO (bool): Whether to use LDO regulator (otherwise DCDC)
            blocking (bool): Whether to use blocking mode
        Returns:
            int: Status code, ERR_NONE indicates success
        Notes:
            - Calls base class methods for low-level register configuration
            - Blocking mode calls standby(), non-blocking mode calls startReceive()
        """
        # 调用基类 LoRa 初始化
        state = super().begin(bw, sf, cr, syncWord, currentLimit, preambleLength, tcxoVoltage, useRegulatorLDO, txIq, rxIq)
        ASSERT(state)

        # 配置报头模式
        if not implicit:
            state = super().explicitHeader()
        else:
            state = super().implicitHeader(implicitLen)
        ASSERT(state)

        # 配置 CRC
        state = super().setCRC(crcOn)
        ASSERT(state)

        # 设置频率
        state = self.setFrequency(freq)
        ASSERT(state)

        # 设置发射功率
        state = self.setOutputPower(power)
        ASSERT(state)

        # 修复 PA 钳位
        state = super().fixPaClamping()
        ASSERT(state)

        # 设置阻塞/非阻塞模式
        state = self.setBlockingCallback(blocking)

        self._log("LoRa begin, freq=%.1f bw=%.1f sf=%d" % (freq, bw, sf))

        return state

    def beginFSK(
        self,
        freq: float = 434.0,
        br: float = 48.0,
        freqDev: float = 50.0,
        rxBw: float = 156.2,
        power: int = 14,
        currentLimit: float = 60.0,
        preambleLength: int = 16,
        dataShaping: float = 0.5,
        syncWord: list = None,
        syncBitsLength: int = 16,
        addrFilter: int = SX126X_GFSK_ADDRESS_FILT_OFF,
        addr: int = 0x00,
        crcLength: int = 2,
        crcInitial: int = 0x1D0F,
        crcPolynomial: int = 0x1021,
        crcInverted: bool = True,
        whiteningOn: bool = True,
        whiteningInitial: int = 0x0100,
        fixedPacketLength: bool = False,
        packetLength: int = 0xFF,
        preambleDetectorLength: int = SX126X_GFSK_PREAMBLE_DETECT_16,
        tcxoVoltage: float = 1.6,
        useRegulatorLDO: bool = False,
        blocking: bool = True,
    ) -> int:
        """
        初始化 GFSK（FSK）调制模式

        依次配置比特率、频偏、接收带宽、同步字、地址过滤等 GFSK 参数。
        Args:
            freq (float): 工作频率（MHz）
            br (float): 比特率（kbps）
            freqDev (float): 频偏（kHz）
            rxBw (float): 接收带宽（kHz）
            power (int): 发射功率（dBm）
            currentLimit (float): 电流限制（mA）
            preambleLength (int): 前导码长度
            dataShaping (float): 数据整形系数（0.0, 0.3, 0.5, 0.7, 1.0）
            syncWord (list): 同步字字节列表，默认 [0x2D, 0x01]
            syncBitsLength (int): 同步字比特长度
            addrFilter (int): 地址过滤模式
            addr (int): 节点地址
            crcLength (int): CRC 长度（0/1/2 字节）
            crcInitial (int): CRC 初始值
            crcPolynomial (int): CRC 多项式
            crcInverted (bool): 是否反转 CRC
            whiteningOn (bool): 是否启用数据白化
            whiteningInitial (int): 白化初始值
            fixedPacketLength (bool): 是否固定包长度
            packetLength (int): 包长度
            preambleDetectorLength (int): 前导码检测长度
            tcxoVoltage (float): TCXO 电压
            useRegulatorLDO (bool): 是否使用 LDO
            blocking (bool): 是否使用阻塞模式
        Returns:
            int: 状态码，ERR_NONE 表示成功
        Notes:
            - 同步字默认使用 [0x2D, 0x01]
        ==========================================
        Initialize GFSK (FSK) modulation mode.

        Configures bit rate, frequency deviation, RX bandwidth, sync word,
        address filtering, and other GFSK parameters in sequence.
        Args:
            freq (float): Operating frequency in MHz
            br (float): Bit rate in kbps
            freqDev (float): Frequency deviation in kHz
            rxBw (float): RX bandwidth in kHz
            power (int): Transmit power in dBm
            currentLimit (float): Current limit in mA
            preambleLength (int): Preamble length
            dataShaping (float): Data shaping factor (0.0, 0.3, 0.5, 0.7, 1.0)
            syncWord (list): Sync word byte list, default [0x2D, 0x01]
            syncBitsLength (int): Sync word bit length
            addrFilter (int): Address filtering mode
            addr (int): Node address
            crcLength (int): CRC length (0/1/2 bytes)
            crcInitial (int): CRC initial value
            crcPolynomial (int): CRC polynomial
            crcInverted (bool): Whether to invert CRC
            whiteningOn (bool): Whether to enable data whitening
            whiteningInitial (int): Whitening initial value
            fixedPacketLength (bool): Whether to use fixed packet length
            packetLength (int): Packet length
            preambleDetectorLength (int): Preamble detector length
            tcxoVoltage (float): TCXO voltage
            useRegulatorLDO (bool): Whether to use LDO
            blocking (bool): Whether to use blocking mode
        Returns:
            int: Status code, ERR_NONE indicates success
        Notes:
            - Default sync word is [0x2D, 0x01]
        """
        # 处理同步字默认值
        if syncWord is None:
            syncWord = [0x2D, 0x01]

        # 调用基类 GFSK 初始化
        state = super().beginFSK(br, freqDev, rxBw, currentLimit, preambleLength, dataShaping, preambleDetectorLength, tcxoVoltage, useRegulatorLDO)
        ASSERT(state)

        # 配置同步字
        state = super().setSyncBits(syncWord, syncBitsLength)
        ASSERT(state)

        # 配置地址过滤
        if addrFilter == SX126X_GFSK_ADDRESS_FILT_OFF:
            state = super().disableAddressFiltering()
        elif addrFilter == SX126X_GFSK_ADDRESS_FILT_NODE:
            state = super().setNodeAddress(addr)
        elif addrFilter == SX126X_GFSK_ADDRESS_FILT_NODE_BROADCAST:
            state = super().setBroadcastAddress(addr)
        else:
            state = ERR_UNKNOWN
        ASSERT(state)

        # 配置 CRC
        state = super().setCRC(crcLength, crcInitial, crcPolynomial, crcInverted)
        ASSERT(state)

        # 配置白化
        state = super().setWhitening(whiteningOn, whiteningInitial)
        ASSERT(state)

        # 配置包长度模式
        if fixedPacketLength:
            state = super().fixedPacketLengthMode(packetLength)
        else:
            state = super().variablePacketLengthMode(packetLength)
        ASSERT(state)

        # 设置频率
        state = self.setFrequency(freq)
        ASSERT(state)

        # 设置发射功率
        state = self.setOutputPower(power)
        ASSERT(state)

        # 修复 PA 钳位
        state = super().fixPaClamping()
        ASSERT(state)

        # 设置阻塞/非阻塞模式
        state = self.setBlockingCallback(blocking)

        self._log("GFSK begin, freq=%.1f br=%.1f" % (freq, br))

        return state

    def setFrequency(self, freq: float, calibrate: bool = True) -> int:
        """
        设置工作频率

        根据频率范围自动选择校准参数，如需校准则调用基类校准函数。
        Args:
            freq (float): 目标频率（MHz），范围 150.0 ~ 960.0
            calibrate (bool): 是否执行镜像校准
        Returns:
            int: 状态码，ERR_INVALID_FREQUENCY 或 ERR_NONE
        Notes:
            - 超出频率范围时返回 ERR_INVALID_FREQUENCY
        ==========================================
        Set operating frequency.

        Automatically selects calibration parameters based on frequency range.
        Args:
            freq (float): Target frequency in MHz, range 150.0 ~ 960.0
            calibrate (bool): Whether to perform image calibration
        Returns:
            int: Status code, ERR_INVALID_FREQUENCY or ERR_NONE
        Notes:
            - Returns ERR_INVALID_FREQUENCY when frequency is out of range
        """
        # 校验频率范围
        if freq < 150.0 or freq > 960.0:
            return ERR_INVALID_FREQUENCY

        state = ERR_NONE

        # 执行镜像校准
        if calibrate:
            data = bytearray(2)
            if freq > 900.0:
                data[0] = SX126X_CAL_IMG_902_MHZ_1
                data[1] = SX126X_CAL_IMG_902_MHZ_2
            elif freq > 850.0:
                data[0] = SX126X_CAL_IMG_863_MHZ_1
                data[1] = SX126X_CAL_IMG_863_MHZ_2
            elif freq > 770.0:
                data[0] = SX126X_CAL_IMG_779_MHZ_1
                data[1] = SX126X_CAL_IMG_779_MHZ_2
            elif freq > 460.0:
                data[0] = SX126X_CAL_IMG_470_MHZ_1
                data[1] = SX126X_CAL_IMG_470_MHZ_2
            else:
                data[0] = SX126X_CAL_IMG_430_MHZ_1
                data[1] = SX126X_CAL_IMG_430_MHZ_2
            state = super().calibrateImage(data)
            ASSERT(state)

        # 设置原始频率值
        return super().setFrequencyRaw(freq)

    def setOutputPower(self, power: int) -> int:
        """
        设置发射功率

        读写 OCP 配置寄存器，结合 PA 配置和发射参数完成功率设置。
        Args:
            power (int): 发射功率（dBm），范围 -9 ~ 22
        Returns:
            int: 状态码，ERR_INVALID_OUTPUT_POWER 或 ERR_NONE
        Notes:
            - 超出范围时返回 ERR_INVALID_OUTPUT_POWER
        ==========================================
        Set transmit output power.

        Reads/writes OCP configuration register, configures PA and
        TX parameters for the desired power level.
        Args:
            power (int): Transmit power in dBm, range -9 ~ 22
        Returns:
            int: Status code, ERR_INVALID_OUTPUT_POWER or ERR_NONE
        Notes:
            - Returns ERR_INVALID_OUTPUT_POWER when power is out of range
        """
        # 校验功率范围
        if not ((power >= -9) and (power <= 22)):
            return ERR_INVALID_OUTPUT_POWER

        # 读取 OCP 配置
        ocp = bytearray(1)
        ocp_mv = memoryview(ocp)
        state = super().readRegister(SX126X_REG_OCP_CONFIGURATION, ocp_mv, 1)
        ASSERT(state)

        # 配置 PA
        state = super().setPaConfig(0x04, _SX126X_PA_CONFIG_SX1262)
        ASSERT(state)

        # 设置发射参数
        state = super().setTxParams(power)
        ASSERT(state)

        # 写回 OCP 配置
        return super().writeRegister(SX126X_REG_OCP_CONFIGURATION, ocp, 1)

    def setTxIq(self, txIq: bool) -> None:
        """
        设置 TX IQ 反转
        Args:
            txIq (bool): 是否反转 TX IQ
        ==========================================
        Set TX IQ inversion.
        Args:
            txIq (bool): Whether to invert TX IQ
        """
        self._txIq = txIq

    def setRxIq(self, rxIq: bool) -> None:
        """
        设置 RX IQ 反转

        非阻塞模式下会自动调用 startReceive() 重新开始接收。
        Args:
            rxIq (bool): 是否反转 RX IQ
        Notes:
            - 非阻塞模式下副作用：触发 startReceive()
        ==========================================
        Set RX IQ inversion.

        In non-blocking mode, startReceive() is automatically called.
        Args:
            rxIq (bool): Whether to invert RX IQ
        Notes:
            - Side effect in non-blocking mode: triggers startReceive()
        """
        self._rxIq = rxIq
        if not self.blocking:
            ASSERT(super().startReceive())

    def setPreambleDetectorLength(self, preambleDetectorLength: int) -> None:
        """
        设置前导码检测长度

        非阻塞模式下会自动调用 startReceive() 重新开始接收。
        Args:
            preambleDetectorLength (int): 前导码检测长度值
        Notes:
            - 非阻塞模式下副作用：触发 startReceive()
        ==========================================
        Set preamble detector length.

        In non-blocking mode, startReceive() is automatically called.
        Args:
            preambleDetectorLength (int): Preamble detector length value
        Notes:
            - Side effect in non-blocking mode: triggers startReceive()
        """
        self._preambleDetectorLength = preambleDetectorLength
        if not self.blocking:
            ASSERT(super().startReceive())

    def setBlockingCallback(self, blocking: bool, callback: callable = None) -> int:
        """
        设置阻塞/非阻塞模式及回调

        阻塞模式：调用 standby() 停止接收，清除 IRQ 回调。
        非阻塞模式：调用 startReceive() 开始接收，注册 IRQ 回调。
        Args:
            blocking (bool): True 为阻塞模式，False 为非阻塞模式
            callback (callable): 非阻塞模式下的 IRQ 回调函数
        Returns:
            int: 状态码，ERR_NONE 表示成功
        Notes:
            - 回调函数签名为 callback(events)
            - ISR-safe: 否（涉及回调注册）
        ==========================================
        Set blocking/non-blocking mode and callback.

        Blocking mode: calls standby() to stop receiving, clears IRQ callback.
        Non-blocking mode: calls startReceive() to begin receiving, registers IRQ callback.
        Args:
            blocking (bool): True for blocking mode, False for non-blocking
            callback (callable): IRQ callback function for non-blocking mode
        Returns:
            int: Status code, ERR_NONE indicates success
        Notes:
            - Callback signature is callback(events)
            - ISR-safe: No (involves callback registration)
        """
        self.blocking = blocking
        if not self.blocking:
            # 非阻塞模式：启动接收并注册回调
            state = super().startReceive()
            ASSERT(state)
            if callback is not None:
                self._callbackFunction = callback
                super().setDio1Action(self._onIRQ)
            else:
                self._callbackFunction = self._dummyFunction
                super().clearDio1Action()
            return state
        else:
            # 阻塞模式：停止接收并清除回调
            state = super().standby()
            ASSERT(state)
            self._callbackFunction = self._dummyFunction
            super().clearDio1Action()
            return state

    def recv(self, len: int = 0, timeout_en: bool = False, timeout_ms: int = 0) -> tuple:
        """
        接收数据

        根据阻塞/非阻塞模式选择不同的接收路径。
        Args:
            len (int): 期望接收的数据长度，0 表示自适应
            timeout_en (bool): 是否启用接收超时
            timeout_ms (int): 接收超时时间（ms）
        Returns:
            tuple: (bytes_data, status)，data 为接收到的字节数据，status 为状态码
        Notes:
            - 非阻塞模式：直接读取已缓冲的数据
            - 阻塞模式：等待数据接收完成
            - CRC 错误时仍返回数据但附带 ERR_CRC_MISMATCH
        ==========================================
        Receive data.

        Selects receive path based on blocking/non-blocking mode.
        Args:
            len (int): Expected data length, 0 for adaptive
            timeout_en (bool): Whether to enable receive timeout
            timeout_ms (int): Receive timeout in ms
        Returns:
            tuple: (bytes_data, status), received data bytes and status code
        Notes:
            - Non-blocking mode: reads already-buffered data directly
            - Blocking mode: waits for data reception to complete
            - CRC error returns data with ERR_CRC_MISMATCH status
        """
        if not self.blocking:
            return self._readData(len)
        else:
            return self._receive(len, timeout_en, timeout_ms)

    def send(self, data: bytes) -> tuple:
        """
        发送数据

        根据阻塞/非阻塞模式选择不同的发送路径。
        Args:
            data (bytes): 待发送的字节数据
        Returns:
            tuple: (sent_length, status)，sent_length 为已发送字节数，status 为状态码
        Notes:
            - 非阻塞模式：启动发送后立即返回
            - 阻塞模式：等待发送完成
        ==========================================
        Transmit data.

        Selects transmit path based on blocking/non-blocking mode.
        Args:
            data (bytes): Data bytes to transmit
        Returns:
            tuple: (sent_length, status), number of bytes sent and status code
        Notes:
            - Non-blocking mode: returns immediately after starting transmission
            - Blocking mode: waits for transmission to complete
        """
        if not self.blocking:
            return self._startTransmit(data)
        else:
            return self._transmit(data)

    def deinit(self) -> None:
        """
        释放硬件资源

        清除 IRQ 回调，将模块设为待机模式。
        Notes:
            - ISR-safe: 否
        ==========================================
        Release hardware resources.

        Clears IRQ callback and sets module to standby mode.
        Notes:
            - ISR-safe: No
        """
        self._log("deinit")
        self._callbackFunction = self._dummyFunction
        try:
            super().clearDio1Action()
        except Exception:
            pass
        try:
            super().standby()
        except Exception:
            pass

    # =================== 私有方法 ===================

    def _events(self) -> int:
        """
        获取当前 IRQ 事件状态位

        Returns:
            int: IRQ 状态位掩码
        ==========================================
        Get current IRQ event status flags.

        Returns:
            int: IRQ status bitmask
        """
        return super().getIrqStatus()

    def _receive(self, len_: int = 0, timeout_en: bool = False, timeout_ms: int = 0) -> tuple:
        """
        阻塞模式接收数据

        等待数据到达或超时，解析结果。
        Args:
            len_ (int): 期望接收长度，0 表示最大包长
            timeout_en (bool): 是否启用超时
            timeout_ms (int): 超时时间（ms）
        Returns:
            tuple: (bytes_data, status)
        Notes:
            - ISR-safe: 否（阻塞 I/O 操作）
        ==========================================
        Blocking mode data reception.

        Waits for data arrival or timeout, parses the result.
        Args:
            len_ (int): Expected receive length, 0 for max packet length
            timeout_en (bool): Whether to enable timeout
            timeout_ms (int): Timeout in ms
        Returns:
            tuple: (bytes_data, status)
        Notes:
            - ISR-safe: No (blocking I/O operation)
        """
        state = ERR_NONE

        length = len_

        # 长度为 0 时使用最大包长
        if len_ == 0:
            length = SX126X_MAX_PACKET_LENGTH

        # 分配接收缓冲区
        data = bytearray(length)
        data_mv = memoryview(data)

        # 调用基类接收
        try:
            state = super().receive(data_mv, length, timeout_en, timeout_ms)
        except AssertionError as e:
            # 解析断言错误获取状态码
            state = list(ERROR.keys())[list(ERROR.values()).index(str(e))]

        # 解析结果
        if state == ERR_NONE or state == ERR_CRC_MISMATCH:
            if len_ == 0:
                length = super().getPacketLength(False)
                data = data[:length]
        else:
            return b"", state

        return bytes(data), state

    def _transmit(self, data: bytes) -> tuple:
        """
        阻塞模式发送数据

        校验数据类型后调用基类阻塞发送。
        Args:
            data (bytes): 待发送数据
        Returns:
            tuple: (sent_length, status)
        Notes:
            - ISR-safe: 否（阻塞 I/O 操作）
        ==========================================
        Blocking mode data transmission.

        Validates data type then calls base class blocking transmit.
        Args:
            data (bytes): Data to transmit
        Returns:
            tuple: (sent_length, status)
        Notes:
            - ISR-safe: No (blocking I/O operation)
        """
        # 校验数据类型
        if isinstance(data, bytes) or isinstance(data, bytearray):
            pass
        else:
            return 0, ERR_INVALID_PACKET_TYPE

        state = super().transmit(data, len(data))
        return len(data), state

    def _readData(self, len_: int = 0) -> tuple:
        """
        非阻塞模式读取已接收数据

        从接收缓冲区读取数据，读取完成后自动启动下一次接收。
        Args:
            len_ (int): 期望读取长度，0 表示自适应
        Returns:
            tuple: (bytes_data, status)
        Notes:
            - 读取完成自动调用 startReceive() 继续接收
            - ISR-safe: 否（SPI 通信）
        ==========================================
        Non-blocking mode data read.

        Reads data from receive buffer, then automatically starts next receive.
        Args:
            len_ (int): Expected read length, 0 for adaptive
        Returns:
            tuple: (bytes_data, status)
        Notes:
            - Automatically calls startReceive() after reading
            - ISR-safe: No (SPI communication)
        """
        state = ERR_NONE

        # 获取实际包长度
        length = super().getPacketLength()

        # 限制读取长度
        if len_ < length and len_ != 0:
            length = len_

        # 分配缓冲区
        data = bytearray(length)
        data_mv = memoryview(data)

        # 从基类读取数据
        try:
            state = super().readData(data_mv, length)
        except AssertionError as e:
            state = list(ERROR.keys())[list(ERROR.values()).index(str(e))]

        # 重新启动接收（非阻塞模式必须）
        ASSERT(super().startReceive())

        # 返回结果
        if state == ERR_NONE or state == ERR_CRC_MISMATCH:
            return bytes(data), state
        else:
            return b"", state

    def _startTransmit(self, data: bytes) -> tuple:
        """
        非阻塞模式启动发送

        校验数据类型后调用基类非阻塞发送。
        Args:
            data (bytes): 待发送数据
        Returns:
            tuple: (sent_length, status)
        Notes:
            - ISR-safe: 否（SPI 通信）
        ==========================================
        Non-blocking mode start transmission.

        Validates data type then calls base class non-blocking transmit.
        Args:
            data (bytes): Data to transmit
        Returns:
            tuple: (sent_length, status)
        Notes:
            - ISR-safe: No (SPI communication)
        """
        # 校验数据类型
        if isinstance(data, bytes) or isinstance(data, bytearray):
            pass
        else:
            return 0, ERR_INVALID_PACKET_TYPE

        state = super().startTransmit(data, len(data))
        return len(data), state

    def _dummyFunction(self, *args) -> None:
        """
        空占位回调函数

        Notes:
            - ISR-safe: 是（无内存分配，无 I/O）
        ==========================================
        Dummy placeholder callback function.

        Notes:
            - ISR-safe: Yes (no memory allocation, no I/O)
        """
        pass

    def _onIRQ(self, callback: callable) -> None:
        """
        内部 IRQ 处理器

        由基类 DIO1 引脚触发，负责读取 IRQ 事件并在发送完成后
        自动切换到接收模式。
        Args:
            callback (callable): 外部用户回调函数
        Notes:
            - 由 ISR 通过 schedule 间接调用
            - 发送完成后自动调用 startReceive() 维持接收状态
        ==========================================
        Internal IRQ handler.

        Triggered by base class DIO1 pin, reads IRQ events and
        automatically switches to receive mode after transmission completes.
        Args:
            callback (callable): External user callback function
        Notes:
            - Called indirectly by ISR via schedule
            - Automatically calls startReceive() after TX to maintain RX state
        """
        events = self._events()
        # 发送完成后自动回到接收模式
        if events & SX126X_IRQ_TX_DONE:
            super().startReceive()
        self._callbackFunction(events)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
