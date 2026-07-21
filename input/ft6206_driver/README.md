# GraftSense-FT6206 电容触摸模块（MicroPython）

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本项目是 **FreakStudio GraftSense FT6206 电容触摸模块** 的 MicroPython 驱动库，专为嵌入式触控交互场景设计。FT6206 是一款支持单点和双点触摸的电容式触摸控制器，通过 I2C 接口与主控通信，广泛应用于 LCD 触摸屏、人机交互面板等场景。

---

## 主要功能

- **多点触摸支持**: 支持 1-2 点同时触摸检测，返回每个触摸点的精确坐标
- **I2C 通信**: 标准 I2C 接口（默认地址 0x38），支持 100kHz/400kHz 通信速率
- **中断回调注入**: 提供 irq_handler 方法供 INT 引脚中断使用，用户自主控制引脚配置
- **坐标变换**: 支持 X/Y 轴反转和坐标轴交换，适配不同屏幕旋转方向
- **芯片验证**: 初始化时可选验证芯片 ID，确保硬件连接正确
- **I2C 容错重试**: 内置重试机制，提高总线通信可靠性
- **低资源占用**: 预分配缓冲区，减少运行时内存碎片化

---

## 硬件要求

- **核心芯片**: FT6206 电容触摸控制器
- **开发环境**: MicroPython v1.23.0 及以上版本（ESP32、Raspberry Pi Pico 等开发板均可）
- **连接方式**: I2C 通信（SCL、SDA）+ 可选 INT 中断引脚
- **I2C 地址**: 默认 0x38

---

## 文件说明

| 文件名         | 功能描述                                                                 |
|----------------|--------------------------------------------------------------------------|
| `ft6206.py`    | 核心驱动库，定义 `FT6206` 类，封装所有触摸检测与坐标读取功能             |
| `main.py`      | 测试与示例代码，演示 I2C 扫描、芯片 ID 验证与触摸轮询功能                |

---

## 软件设计核心思想

1. **依赖注入**: I2C 实例、回调函数等通过构造函数参数注入，不依赖全局状态，便于测试与替换
2. **关注点分离**: 驱动仅负责 I2C 通信与数据解析，中断管理由调用者控制，Pin 对象在 main.py 中创建
3. **错误容错**: I2C 读写内置重试机制（最多 3 次），避免偶发性总线错误导致崩溃
4. **缓冲区复用**: 使用预分配 bytearray 存储寄存器数据，减少频繁分配带来的内存碎片化
5. **中文注释 + 英文异常**: 代码注释全部中文便于国内开发者阅读，异常信息和日志字符串保持英文确保终端兼容性

---

## 使用说明

### 1. 环境准备

- 安装 MicroPython v1.23.0 到目标开发板
- 将 `ft6206.py` 上传至开发板文件系统

### 2. 初始化驱动

```python
from machine import I2C, Pin
from ft6206 import FT6206

# 初始化 I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建 FT6206 实例
device = FT6206(
    i2c=i2c,
    address=0x38,
    width=320,
    height=240,
    max_touches=2,
    callback=touch_callback,
    verify=True,
)
```

### 3. 配置中断

```python
# 创建中断引脚并绑定驱动处理函数
int_pin = Pin(14, Pin.IN, Pin.PULL_UP)
int_pin.irq(trigger=Pin.IRQ_FALLING, handler=device.irq_handler)
```

### 4. 读取触摸数据

```python
# 轮询模式
positions = device.position
print(positions)

# 中断模式（通过 callback 参数注册回调函数）
def touch_callback(x_list, y_list, count):
    for i in range(count):
        print("Point {}: x={}, y={}".format(i, x_list[i], y_list[i]))
```

---

## 示例程序

```python
# MicroPython v1.23.0
import time
from machine import I2C, Pin
from ft6206 import FT6206

time.sleep(3)
print("FreakStudio : FT6206 touch controller test")

# 初始化 I2C 和驱动
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
device = FT6206(i2c, width=320, height=240)

# 轮询触摸状态
try:
    while True:
        touch_count = device.touched
        if touch_count > 0:
            print("Positions:", device.position)
        time.sleep_ms(100)
except KeyboardInterrupt:
    pass
finally:
    device.deinit()
    print("Program exited")
```

---

## 注意事项

1. **I2C 上拉电阻**: SCL 和 SDA 引脚需外接 4.7kΩ 上拉电阻（或使用内部上拉），确保总线信号稳定
2. **中断引脚配置**: INT 引脚建议配置为下拉模式（或外部上拉 + 内部下拉），下降沿触发
3. **坐标范围**: X/Y 坐标范围为 0 到 (width-1)/(height-1)，超出此范围的值为无效数据
4. **触摸延时**: 轮询模式下建议使用 50-100ms 的延时，避免 I2C 总线过载
5. **多设备共享**: 若 I2C 总线上有多个设备，确保 FT6206 地址 0x38 与其他设备不冲突
6. **初始化验证**: 建议开启 verify=True 参数，初始化时自动验证芯片 ID 确保连接正确
7. **缓冲协议**: 驱动使用 readfrom_mem_into 一次性读取全部寄存器，提高数据读取效率

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:  
📧 **邮箱**: <liqinghsui@freakstudio.cn>  
💻 **GitHub**: [https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---

## 许可协议

本项目采用 **MIT License** 开源协议。

```text
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
