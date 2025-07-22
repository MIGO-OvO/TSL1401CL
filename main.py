import sys
import numpy as np
import serial
import re
import serial.tools.list_ports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import QThread, Signal, Slot, Qt, QSize
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QResizeEvent, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker


# 串口通信线程
class SerialThread(QThread):
    dataReceived = Signal(list)

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.running = True
        self.capturing = False

    def run(self):
        try:
            self.ser = serial.Serial(self.port, 115200, timeout=1)
            while self.running:
                if self.ser.in_waiting and self.capturing:
                    line = self.ser.readline().decode().strip()
                    if line:
                        try:
                            data = [int(x) for x in line.split(',')]
                            if len(data) == 128:
                                self.dataReceived.emit(data)
                        except ValueError:
                            pass
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                self.ser.close()

    def stop(self):
        self.running = False
        self.wait(1000)

    def start_capture(self):
        """开始采集数据"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.write('S'.encode())
            self.capturing = True

    def stop_capture(self):
        """停止采集数据"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.write('X'.encode())
            self.capturing = False


# 主应用窗口
class SpectrometerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("High Precision Spectrometer")
        self.setGeometry(100, 100, 1200, 900)  # 4:3 比例
        self.base_font_size = 14  #
        self.base_padding = 12  #
        self.setMinimumSize(1200, 900)  # 最小尺寸
        self.setup_ui()
        self.serial_thread = None
        self.is_capturing = False

    def setup_ui(self):
        # 设置全局字体
        font = QFont("Arial", self.base_font_size)
        QApplication.setFont(font)

        # 主布局
        main_widget = QWidget()
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(
            self.base_padding, self.base_padding,
            self.base_padding, self.base_padding
        )
        self.main_layout.setSpacing(self.base_padding)

        # 左侧控制面板 (占窗口宽度30%)
        control_frame = QFrame()
        control_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        control_frame.setObjectName("ControlFrame")
        control_layout = QVBoxLayout(control_frame)
        control_layout.setAlignment(Qt.AlignTop)
        control_layout.setSpacing(self.base_padding - 2)  # 减少间距

        # 应用标题
        app_title = QLabel("Spectrometer Pro")
        app_title.setFont(QFont("Arial", self.base_font_size + 4, QFont.Bold))
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setStyleSheet("""
            color: #007AFF;
            margin-bottom: 15px;
            padding: 8px;
            border-bottom: 1px solid #E0E0E0;
        """)
        control_layout.addWidget(app_title)

        # 串口设置
        serial_group = QFrame()
        serial_group.setObjectName("SerialGroup")
        serial_layout = QVBoxLayout(serial_group)
        serial_layout.setSpacing(self.base_padding - 5)

        serial_title = QLabel("SERIAL PORT")
        serial_title.setFont(QFont("Arial", self.base_font_size + 1, QFont.Bold))
        serial_title.setStyleSheet("color: #5F6368;")
        serial_layout.addWidget(serial_title)

        # 串口选择与刷新
        port_layout = QHBoxLayout()
        port_layout.setSpacing(self.base_padding - 10)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(32)  # 减小按钮高度
        self.port_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                padding: {self.base_padding - 7}px;
                font-size: {self.base_font_size}pt;
                font-family: Calibri;
                selection-background-color: #E3F2FD;
            }}
            QComboBox::drop-down {{
                width: 25px;
                border-left: 1px solid #D1D5DB;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                background-color: #FFFFFF;
                font-family: Calibri;
                font-size: {self.base_font_size}pt;
                selection-background-color: #E3F2FD;
            }}
        """)
        port_layout.addWidget(self.port_combo, 70)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.setIconSize(QSize(18, 18))
        self.refresh_btn.setMinimumSize(32, 32)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F3F4;
                border-radius: 10px;
                min-width: 32px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #E8EAED;
            }}
        """)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn, 30)

        serial_layout.addLayout(port_layout)

        # 连接按钮
        self.connect_btn = QPushButton("Connect Device")
        self.connect_btn.setMinimumHeight(35)
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #007AFF;
                color: white;
                border-radius: 10px;
                padding: {self.base_padding - 7}px;
                font-size: {self.base_font_size}pt;
                font-family: Calibri;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0A84FF;
            }}
            QPushButton:pressed {{
                background-color: #0062CC;
            }}
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        serial_layout.addWidget(self.connect_btn)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin: 12px 0; border: 1px solid #E0E0E0;")
        serial_layout.addWidget(separator)

        # 采集控制
        capture_title = QLabel("DATA CAPTURE")
        capture_title.setFont(QFont("Arial", self.base_font_size + 1, QFont.Bold))
        capture_title.setStyleSheet("color: #5F6368;")
        serial_layout.addWidget(capture_title)

        self.capture_btn = QPushButton("Start Capture")
        self.capture_btn.setMinimumHeight(35)
        self.capture_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #34C759;
                color: white;
                border-radius: 10px;
                padding: {self.base_padding - 7}px;
                font-size: {self.base_font_size}pt;
                font-family: Calibri;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #30D158;
            }}
            QPushButton:pressed {{
                background-color: #2CAE50;
            }}
        """)
        self.capture_btn.clicked.connect(self.toggle_capture)
        self.capture_btn.setEnabled(False)
        serial_layout.addWidget(self.capture_btn)

        control_layout.addWidget(serial_group)

        # 数据显示区域
        data_group = QFrame()
        data_group.setObjectName("DataGroup")
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(self.base_padding - 5)

        data_title = QLabel("DATA STATISTICS")
        data_title.setFont(QFont("Arial", self.base_font_size + 1, QFont.Bold))
        data_title.setStyleSheet("color: #5F6368;")
        data_layout.addWidget(data_title)

        # 创建统计数据显示标签
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"""
            QLabel {{
                background-color: #FFFFFF;
                border-radius: 14px;
                padding: {self.base_padding - 3}px;
                font-family: Calibri;
                font-size: {self.base_font_size}pt;
                border: 1px solid #E0E0E0;
            }}
        """)
        self.stats_label.setTextFormat(Qt.RichText)
        self.update_stats_display()  # 初始化显示
        data_layout.addWidget(self.stats_label)

        # 状态指示器
        status_layout = QHBoxLayout()
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(14, 14)
        self.status_indicator.setStyleSheet("""
            background-color: #E0E0E0;
            border-radius: 7px;
        """)
        status_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Not connected")
        self.status_label.setStyleSheet("color: #5F6368; font-family: Arial; font-size: 10pt;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        data_layout.addLayout(status_layout)
        control_layout.addWidget(data_group)

        # 右侧绘图区域 (占窗口宽度70%)
        plot_frame = QFrame()
        plot_frame.setObjectName("PlotFrame")
        plot_layout = QVBoxLayout(plot_frame)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        # 绘图区域标题
        plot_title = QLabel("Spectral Analysis")
        plot_title.setFont(QFont("Arial", self.base_font_size + 4, QFont.Bold))
        plot_title.setAlignment(Qt.AlignCenter)
        plot_title.setStyleSheet("""
            color: #007AFF;
            margin-bottom: 12px;
            padding: 8px;
        """)
        plot_layout.addWidget(plot_title)

        self.figure = Figure(figsize=(8, 5), dpi=150)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)

        # 设置图表字体为Arial
        title_font = {'fontname': 'Arial', 'fontsize': self.base_font_size + 2}
        label_font = {'fontname': 'Arial', 'fontsize': self.base_font_size + 1}
        tick_font = {'fontname': 'Arial', 'fontsize': self.base_font_size - 1}

        self.ax.set_title("Spectral Distribution", **title_font)
        self.ax.set_xlabel("Pixel Index", **label_font)
        self.ax.set_ylabel("ADC Value (0-1023)", **label_font)
        self.ax.tick_params(axis='both', which='major', labelsize=tick_font['fontsize'])

        # 设置网格线样式
        self.ax.grid(True, linestyle='-', alpha=0.2)

        # 设置坐标轴颜色
        self.ax.spines['bottom'].set_color('#007AFF')
        self.ax.spines['top'].set_color('#007AFF')
        self.ax.spines['right'].set_color('#007AFF')
        self.ax.spines['left'].set_color('#007AFF')

        # 细化X轴刻度
        self.ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
        self.ax.xaxis.set_minor_locator(ticker.MultipleLocator(5))

        self.line, = self.ax.plot([], [], '#007AFF', linewidth=1.8, alpha=0.8)
        self.ax.set_xlim(0, 127)
        self.ax.set_ylim(0, 1023)

        # 设置背景透明
        self.figure.patch.set_alpha(0.0)
        self.ax.patch.set_alpha(0.0)

        plot_layout.addWidget(self.canvas)

        # 添加布局
        self.main_layout.addWidget(control_frame, 30)  # 30% 宽度
        self.main_layout.addWidget(plot_frame, 70)  # 70% 宽度

        self.setCentralWidget(main_widget)
        self.refresh_ports()

    def resizeEvent(self, event: QResizeEvent):
        """窗口大小变化时调整UI元素"""
        # 根据窗口大小调整字体大小
        scale_factor = min(event.size().width() / 1200, event.size().height() / 900)
        new_font_size = max(9, int(self.base_font_size * scale_factor * 0.9))  # 最小9pt
        new_padding = max(8, int(self.base_padding * scale_factor * 0.8))  # 最小8px

        # 更新控件样式
        self.update_ui_scale(new_font_size, new_padding)
        super().resizeEvent(event)

    def update_ui_scale(self, font_size: int, padding: int):
        """根据当前窗口大小更新UI元素尺寸"""
        # 更新按钮样式
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #007AFF;
                color: white;
                border-radius: 10px;
                padding: {padding - 7}px;
                font-size: {font_size}pt;
                font-family: Calibri;
                font-weight: bold;
                min-height: 35px;
            }}
        """)

        self.capture_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #34C759;
                color: white;
                border-radius: 10px;
                padding: {padding - 7}px;
                font-size: {font_size}pt;
                font-family: Calibri;
                font-weight: bold;
                min-height: 35px;
            }}
        """)

        # 更新下拉框样式
        self.port_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                padding: {padding - 7}px;
                font-size: {font_size}pt;
                font-family: Calibri;
                min-height: 32px;
                selection-background-color: #E3F2FD;
            }}
        """)

        # 更新统计数据区域样式
        self.stats_label.setStyleSheet(f"""
            QLabel {{
                background-color: #FFFFFF;
                border-radius: 14px;
                padding: {padding - 3}px;
                font-size: {font_size}pt;
                font-family: Calibri;
                border: 1px solid #E0E0E0;
            }}
        """)

        # 更新标题字体
        titles = [
            "Spectrometer Pro", "SERIAL PORT",
            "DATA CAPTURE", "DATA STATISTICS",
            "Spectral Analysis"
        ]
        for title in self.findChildren(QLabel, options=Qt.FindDirectChildrenOnly):
            if title.text() in titles:
                if title.text() == "Spectrometer Pro":
                    title.setFont(QFont("Arial", font_size + 4, QFont.Bold))
                elif title.text() == "Spectral Analysis":
                    title.setFont(QFont("Arial", font_size + 4, QFont.Bold))
                else:
                    title.setFont(QFont("Arial", font_size + 1, QFont.Bold))

        # 更新图表字体
        if hasattr(self, 'ax'):
            title_font = font_size + 2
            label_font = font_size + 1
            tick_font = font_size - 1

            self.ax.title.set_fontsize(title_font)
            self.ax.title.set_fontfamily('Arial')
            self.ax.xaxis.label.set_fontsize(label_font)
            self.ax.xaxis.label.set_fontfamily('Arial')
            self.ax.yaxis.label.set_fontsize(label_font)
            self.ax.yaxis.label.set_fontfamily('Arial')
            self.ax.tick_params(axis='both', which='major', labelsize=tick_font)
            self.figure.tight_layout()
            self.canvas.draw()

    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combo.clear()
        available_ports = []

        # 获取所有可用串口
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if re.match(r'^COM\d+$', port.device, re.IGNORECASE):
                try:
                    # 尝试打开端口以验证是否真正可用
                    with serial.Serial(port.device):
                        available_ports.append(port.device)
                except serial.SerialException:
                    continue

        if available_ports:
            self.port_combo.addItems(available_ports)
            self.port_combo.setCurrentIndex(0)
        else:
            self.port_combo.addItem("No COM ports available")

    def toggle_connection(self):
        """连接/断开设备"""
        if self.serial_thread and self.serial_thread.isRunning():
            # 如果正在采集，先停止采集
            if self.is_capturing:
                self.toggle_capture()

            self.disconnect_device()
            self.connect_btn.setText("Connect Device")
            self.capture_btn.setEnabled(False)
            self.capture_btn.setText("Start Capture")
            self.status_label.setText("Not connected")
            self.status_indicator.setStyleSheet("background-color: #E0E0E0; border-radius: 7px;")
        else:
            port = self.port_combo.currentText()
            if port and port != "No COM ports available":
                self.connect_device(port)
                self.connect_btn.setText("Disconnect")
                self.capture_btn.setEnabled(True)
                self.status_label.setText("Connected")
                self.status_indicator.setStyleSheet("background-color: #34C759; border-radius: 7px;")

    def toggle_capture(self):
        """开始/停止采集"""
        if self.capture_btn.text() == "Start Capture":
            self.capture_btn.setText("Stop Capture")
            self.capture_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FF9500;
                    color: white;
                    border-radius: 10px;
                    padding: {self.base_padding - 7}px;
                    font-size: {self.base_font_size}pt;
                    font-family: Calibri;
                    font-weight: bold;
                    min-height: 35px;
                }}
            """)
            if self.serial_thread:
                self.serial_thread.start_capture()
                self.is_capturing = True
                self.status_label.setText("Capturing data...")
                self.status_indicator.setStyleSheet("background-color: #FF9500; border-radius: 7px;")
        else:
            self.capture_btn.setText("Start Capture")
            self.capture_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #34C759;
                    color: white;
                    border-radius: 10px;
                    padding: {self.base_padding - 7}px;
                    font-size: {self.base_font_size}pt;
                    font-family: Calibri;
                    font-weight: bold;
                    min-height: 35px;
                }}
            """)
            if self.serial_thread:
                self.serial_thread.stop_capture()
                self.is_capturing = False
                self.status_label.setText("Connected")
                self.status_indicator.setStyleSheet("background-color: #34C759; border-radius: 7px;")

    def connect_device(self, port):
        """连接串口设备"""
        self.serial_thread = SerialThread(port)
        self.serial_thread.dataReceived.connect(self.update_plot)
        self.serial_thread.start()

    def disconnect_device(self):
        """断开串口连接"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None

    def update_stats_display(self, stats=None):
        """更新统计数据展示"""
        if stats is None:
            html = f"""
            <div style='font-family: Calibri; font-size: {self.base_font_size}pt;'>
                <div style='color: #888; text-align: center; padding: 15px;'>
                    Waiting for data...
                </div>
            </div>
            """
        else:
            max_val, min_val, mean_val, std_val, peak_pos = stats
            html = f"""
            <div style='font-family: Calibri; font-size: {self.base_font_size}pt;'>
                <div style='display: flex; justify-content: space-between; border-bottom: 1px solid #E0E0E0; padding: 8px 0;'>
                    <div style='color: #5F6368;'>Max Value</div>
                    <div style='color: #007AFF; font-weight: bold;'>{max_val} <span style='font-size: {self.base_font_size - 1}pt; color: #666;'>(Pixel {np.argmax(stats[0])})</span></div>
                </div>

                <div style='display: flex; justify-content: space-between; border-bottom: 1px solid #E0E0E0; padding: 8px 0;'>
                    <div style='color: #5F6368;'>Min Value</div>
                    <div style='color: #FF2D55; font-weight: bold;'>{min_val}</div>
                </div>

                <div style='display: flex; justify-content: space-between; border-bottom: 1px solid #E0E0E0; padding: 8px 0;'>
                    <div style='color: #5F6368;'>Average</div>
                    <div style='color: #34C759; font-weight: bold;'>{mean_val:.2f}</div>
                </div>

                <div style='display: flex; justify-content: space-between; border-bottom: 1px solid #E0E0E0; padding: 8px 0;'>
                    <div style='color: #5F6368;'>Standard Deviation</div>
                    <div style='color: #AF52DE; font-weight: bold;'>{std_val:.2f}</div>
                </div>

                <div style='display: flex; justify-content: space-between; padding: 8px 0;'>
                    <div style='color: #5F6368;'>Peak Position</div>
                    <div style='color: #FF9500; font-weight: bold;'>{peak_pos}</div>
                </div>
            </div>
            """
        self.stats_label.setText(html)

    @Slot(list)
    def update_plot(self, data):
        """更新光谱图和统计数据"""
        # 数据处理：剔除前12帧和后3帧的数据
        if len(data) == 128:
            # 去除暗电流影响
            processed_data = data[12:-3]  # 保留第13帧到第125帧
        else:
            processed_data = data  # 如果数据长度不是128，则使用原始数据

        # 更新绘图数据
        x = np.arange(len(processed_data))
        self.line.set_data(x, processed_data)

        # 更新X轴范围
        self.ax.set_xlim(0, len(processed_data) - 1)
        self.canvas.draw()

        # 计算统计数据
        max_val = max(processed_data)
        min_val = min(processed_data)
        mean_val = np.mean(processed_data)
        std_val = np.std(processed_data)
        peak_pos = np.argmax(processed_data)

        # 更新数据统计显示
        self.update_stats_display((max_val, min_val, mean_val, std_val, peak_pos))


if __name__ == "__main__":
    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # 全局样式
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F5F7F9;
        }

        #ControlFrame, #PlotFrame, #SerialGroup, #DataGroup {
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 18px;
            border: none;
            padding: 12px;
        }

        #ControlFrame {
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        }

        #PlotFrame {
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.05);
        }

        #SerialGroup, #DataGroup {
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
            border: 1px solid #E0E0E0;
        }

        QLabel {
            color: #000000;
            font-family: Arial;
        }
        
        QFrame {
            background-color: transparent;
        }
        
        QComboBox {
            selection-background-color: #E3F2FD;
            font-family: Calibri;
        }
        
        QComboBox::down-arrow {
            image: url(none);
        }
    """)

    window = SpectrometerApp()
    window.show()
    sys.exit(app.exec())

