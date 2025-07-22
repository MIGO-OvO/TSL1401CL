# Spectrometer Pro  
# 光谱仪专业版

## 项目描述 / Project Description  
这是一个基于TSL1401CL传感器的上下位机程序架构，由下位机(Arduino)和上位机(Python GUI)组成。下位机负责控制TSL1401线性传感器采集光数据，上位机通过串口接收数据并进行实时可视化分析。  
This is an upper and lower computer program architecture based on the TSL1401CL sensor, consisting of the lower computer (Arduino) and the upper computer (Python GUI). The lower computer is responsible for controlling the TSL1401 linear sensor to collect optical data, while the upper computer receives the data through the serial port and conducts real-time visual analysis.

---

## 功能特点 / Features  
### 下位机功能 / Lower Computer Features
- 📶 实时采集数据  
  Real-time capture of 128-pixel spectral data
- ⚡ 连续采集模式 
  Supports continuous capture mode
- 🔧 可调整帧间隔时间（0-1000ms）  
  Adjustable frame interval (0-1000ms)
- 📡 串口命令控制（开始/停止采集）  
  Serial command control (start/stop capture)

### 上位机功能 / Upper Computer Features
- 📊 CCD信号曲线可视化  
  Real-time spectral curve visualization
- 📈 数据统计面板（最大值/最小值/均值/标准差/峰值位置）  
  Data statistics panel (max/min/mean/std/peak position)

---

## 硬件要求 / Hardware Requirements  
- Arduino开发板（UNO/Nano等）  
  Arduino board (UNO/Nano, etc.)
- TSL1401线性传感器模块  
  TSL1401 linear sensor module
- USB数据线  
  USB cable

**接线说明 / Wiring Guide**  
| 传感器引脚 | Arduino引脚 |  
|------------|-------------|  
| SI         | Digital 2   |  
| CLK        | Digital 3   |  
| AO         | Analog A0   |  
| GND        | GND         |  
| VDD        | 3.3V/5V     |  

---

## 软件依赖 / Software Dependencies  
### 下位机 / Lower Computer
- Arduino IDE (≥1.8.x)
- [Arduino AVR Boards](https://www.arduino.cc/en/main/software)

### 上位机 / Upper Computer
```bash
Python 3.8+
pip install numpy pyside6 pyserial matplotlib
```

---

## 安装与使用 / Installation and Usage  
1. **烧写下位机程序**  
   **Flash Lower Computer Program**  
   - 打开`TSL1401.ino`文件  
     Open `TSL1401.ino` file
   - 选择对应开发板型号  
     Select correct board model
   - 上传到Arduino  
     Upload to Arduino

2. **运行上位机**  
   **Run Upper Computer**  
   ```bash
   python main.py
   ```

3. **操作步骤**  
   **Operation Steps**  
   1. 选择Arduino连接的COM端口  
      Select COM port connected to Arduino
   2. 点击"Connect Device"建立连接  
      Click "Connect Device" to establish connection
   3. 点击"Start Capture"开始数据采集  
      Click "Start Capture" to start data acquisition
   4. 观察实时光谱曲线和统计数据  
      Observe real-time spectral curve and statistics


## 文件说明 / File Description  
| 文件名 | 描述 |  
|--------|------|  
| `main.py` | 上位机Python程序（PySide6 GUI）<br>Upper computer Python program (PySide6 GUI) |  
| `TSL1401.ino` | 下位机Arduino程序<br>Lower computer Arduino program |  

---

## 许可证 / License  
本项目采用[MIT许可证](LICENSE)  
This project is licensed under [MIT License](LICENSE)  

```text
MIT License

Copyright (c) 2023 Spectrometer Pro

Permission is hereby granted...
```
