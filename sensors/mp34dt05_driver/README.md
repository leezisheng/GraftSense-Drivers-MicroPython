# MP34DT05 MEMS 麦克风 MicroPython 驱动

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

MP34DT05 是一款低功耗 MEMS 数字麦克风，采用 PDM（脉冲密度调制）输出接口。本驱动利用 RP2040 的 PIO（可编程 I/O）硬件实现高效的 PDM 时钟生成和数据采样，并通过 Arm Thumb 汇编优化的 PDM 到 PCM 转换，实现低延迟、低 CPU 占用的连续音频采集。

适用于语音识别、音频录制、声学监测等需要高质量音频输入的应用场景。

## 主要功能

- 基于 RP2040 PIO 硬件的 PDM 时钟生成与数据采样，无需 CPU 参与
- Arm Thumb 汇编优化的 PDM 到 PCM 转换（Brian Kernighan 位计数法）
- 双缓冲机制：ISR 自动填充和切换缓冲区，主循环异步处理
- 通过 micropython.schedule 非阻塞回调通知缓冲区就绪
- 可配置采样缓冲区长度和 PIO 状态机 ID
- 零外部组件：仅需 PDM 麦克风芯片和两个 GPIO 引脚

## 硬件要求

### 推荐测试硬件

- Arduino Nano RP2040 Connect 或任意 RP2040 开发板
- MP34DT05 PDM MEMS 麦克风模块
- 面包板及杜邦线

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.6V~3.6V） |
| GND  | 电源负极 |
| CLK  | PDM 时钟输入（由 RP2040 PIO 输出，GPIO23） |
| DAT  | PDM 数据输出（RP2040 输入，GPIO22） |
| L/R  | 声道选择（GND = 左声道，VCC = 右声道） |

## 软件环境

- 固件版本：MicroPython v1.23.0+（RP2040）
- 驱动版本：v1.0.0
- 依赖库：无外部依赖（仅使用 rp2、micropython、array、uctypes、machine 内置模块）
- 芯片要求：RP2040（rp2 模块和 PIO 硬件为必需）

## 文件结构

```
├── mp34dt05.py    # 核心驱动文件
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明

- **mp34dt05.py**：MP34DT05 MEMS 麦克风核心驱动，包含 PIO PDM 采样程序、Arm Thumb 汇编 PDM→PCM 转换、双缓冲管理和回调机制
- **main.py**：驱动测试程序，演示麦克风初始化、采样启动和音频数据统计

## 快速开始

### 1. 复制文件

将 `mp34dt05.py` 和 `main.py` 复制到 RP2040 设备的文件系统中。

### 2. 硬件接线

| MP34DT05 | RP2040 (Nano RP2040 Connect) |
|----------|------------------------------|
| VCC      | 3.3V                         |
| GND      | GND                          |
| CLK      | GPIO23                       |
| DAT      | GPIO22                       |
| L/R      | GND（左声道）                |

### 3. 运行测试

将以下代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 MP34DT05 MEMS 麦克风驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin
from mp34dt05 import MP34DT05

# ======================================== 全局变量 ============================================
# 缓冲区处理计数
buffer_processed_count = 0
# 缓冲区处理完成标志
buffer_ready = False
# 就绪的缓冲区索引
ready_buffer_idx = 0

# 数据打印间隔（ms）
print_interval = 2000
# 上次打印时间戳（ms）
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================
def buffer_handler(idx: int):
    """
    缓冲区就绪回调函数
    当 PDM 采样填满一个缓冲区后，通过 micropython.schedule 调用此函数
    Args:
        idx (int): 就绪的缓冲区索引（0 或 1）
    Notes:
        - 在 micropython.schedule 调度上下文中执行（非 ISR）
        - 应在此函数中调用 get_buffer(idx) 获取数据进行处理
    """
    global buffer_processed_count, buffer_ready, ready_buffer_idx
    # 递增缓冲区处理计数
    buffer_processed_count += 1
    # 设置就绪标志，供主循环读取
    buffer_ready = True
    ready_buffer_idx = idx

def do_stop():
    """停止采样（模式切换，默认注释调用，可 REPL 手动触发）"""
    mic.stop()
    print("Microphone sampling stopped")

def do_start():
    """恢复采样（模式切换，默认注释调用，可 REPL 手动触发）"""
    mic.start()
    print("Microphone sampling resumed")

# ======================================== 自定义类 ============================================
# 无自定义类，全部逻辑在主程序中

# ======================================== 初始化配置 ==========================================
# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing MP34DT05 MEMS microphone PDM driver...")

# 初始化 PDM 麦克风引脚
# PDM 时钟引脚（Arduino Nano RP2040 Connect: GPIO23）
pdm_clk = Pin(23, Pin.OUT)
# PDM 数据引脚（Arduino Nano RP2040 Connect: GPIO22）
pdm_data = Pin(22, Pin.IN)

# 创建 MP34DT05 驱动实例，注册缓冲区就绪回调
mic = MP34DT05(pdm_clk, pdm_data, handler=buffer_handler, buf_len=1024)

# 启动 PDM 采样
print("Starting PDM sampling...")
mic.start()
print("Microphone ready, buffer_handler will be called when data is available")

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频读取：打印采样统计信息
            print("Buffers processed: %d | Active: %s"
                  % (buffer_processed_count, mic.is_active))
            last_print_time = current_time

        # 检查是否有缓冲区就绪
        if buffer_ready:
            buffer_ready = False
            # 获取就绪的缓冲区数据进行处理
            buf = mic.get_buffer(ready_buffer_idx)
            # 计算缓冲区中音频样本的平均幅值（简单统计）
            if len(buf) > 0:
                # 计算样本 DC 偏置（PDM 空闲值约为 128）
                avg = sum(buf) // len(buf)
                print("Buffer[%d] ready, avg=%d (len=%d)" % (ready_buffer_idx, avg, len(buf)))

        # 以下为模式切换函数，默认注释执行，可 REPL 手动调用
        # do_stop()               # 停止采样，REPL 手动触发
        # do_start()              # 恢复采样，REPL 手动触发

        # 短延时降低 CPU 占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    mic.stop()
    mic.deinit()
    del mic
    print("Program exited")
```

### 4. 最小代码示例

```python
from machine import Pin
from mp34dt05 import MP34DT05

def on_buffer_ready(idx):
    buf = mic.get_buffer(idx)
    avg = sum(buf) // len(buf)
    print("Buffer[%d] avg=%d" % (idx, avg))

pdm_clk = Pin(23, Pin.OUT)
pdm_data = Pin(22, Pin.IN)
mic = MP34DT05(pdm_clk, pdm_data, handler=on_buffer_ready)
mic.start()
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 芯片平台 | 仅支持 RP2040 系列，依赖 rp2 模块和 PIO 硬件 |
| 引脚选择 | 时钟和数据引脚必须为同一 PIO 块的相邻 GPIO（PIO0: GPIO0~31, PIO1: GPIO16~47） |
| PDM 时钟 | 频率固定为 3.072 MHz，对应 48 kHz 采样率（64x 过采样） |
| 缓冲区大小 | 默认 1024 字节，可配置。越大延迟越高，越小 CPU 调度越频繁 |
| 声道选择 | L/R 引脚接 GND 为左声道有效，接 VCC 为右声道有效 |
| ISR 性能 | IRQ 使用软中断模式（hard=False），避免 PIO IRQ 硬中断导致的死锁问题 |
| 内存分配 | PIO 和 Arm Thumb 汇编代码不使用堆内存，双缓冲区占用 2 * buf_len 字节 |
| 电源噪声 | PDM 麦克风对电源噪声敏感，建议 VCC 和 GND 靠近麦克风放置去耦电容（100nF + 10uF） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-19 | FreakStudio | 初始版本，基于 GraftSense 规范重写 |

## 联系方式

- 邮箱：freakstudio@example.com
- GitHub：[https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
