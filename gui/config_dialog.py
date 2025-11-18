"""
Configuration Dialog
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox,
                             QPushButton, QGroupBox, QGridLayout, QComboBox)


class ConfigDialog(QDialog):
    """Configuration dialog for all modules"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()

        self.setWindowTitle("Configuration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Create tabs for each module
        tabs = QTabWidget()

        tabs.addTab(self.create_gps_tab(), "GPS")
        tabs.addTab(self.create_lora_tab(), "LoRa")
        tabs.addTab(self.create_rtlsdr_tab(), "RTL-SDR")
        tabs.addTab(self.create_rtc_tab(), "RTC")
        tabs.addTab(self.create_usb_tab(), "USB")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def create_gps_tab(self):
        """Create GPS configuration tab"""
        widget = QWidget()
        layout = QGridLayout()

        self.gps_enabled = QCheckBox("Enable GPS")
        self.gps_enabled.setChecked(self.config.get('gps', {}).get('enabled', False))
        layout.addWidget(self.gps_enabled, 0, 0, 1, 2)

        layout.addWidget(QLabel("Device:"), 1, 0)
        self.gps_device = QLineEdit(self.config.get('gps', {}).get('device', '/dev/ttyUSB0'))
        layout.addWidget(self.gps_device, 1, 1)

        layout.addWidget(QLabel("Baud Rate:"), 2, 0)
        self.gps_baud = QSpinBox()
        self.gps_baud.setRange(4800, 115200)
        self.gps_baud.setValue(self.config.get('gps', {}).get('baud_rate', 9600))
        layout.addWidget(self.gps_baud, 2, 1)

        widget.setLayout(layout)
        return widget

    def create_lora_tab(self):
        """Create LoRa configuration tab"""
        widget = QWidget()
        layout = QGridLayout()

        self.lora_enabled = QCheckBox("Enable LoRa")
        self.lora_enabled.setChecked(self.config.get('lora', {}).get('enabled', False))
        layout.addWidget(self.lora_enabled, 0, 0, 1, 2)

        layout.addWidget(QLabel("SPI Device:"), 1, 0)
        self.lora_spi = QLineEdit(self.config.get('lora', {}).get('spi_device', '/dev/spidev0.0'))
        layout.addWidget(self.lora_spi, 1, 1)

        layout.addWidget(QLabel("Frequency (MHz):"), 2, 0)
        self.lora_freq = QSpinBox()
        self.lora_freq.setRange(400, 1000)
        self.lora_freq.setValue(self.config.get('lora', {}).get('frequency', 915000000) // 1000000)
        layout.addWidget(self.lora_freq, 2, 1)

        widget.setLayout(layout)
        return widget

    def create_rtlsdr_tab(self):
        """Create RTL-SDR configuration tab"""
        widget = QWidget()
        layout = QGridLayout()

        self.sdr_enabled = QCheckBox("Enable RTL-SDR")
        self.sdr_enabled.setChecked(self.config.get('rtlsdr', {}).get('enabled', False))
        layout.addWidget(self.sdr_enabled, 0, 0, 1, 2)

        layout.addWidget(QLabel("Device Index:"), 1, 0)
        self.sdr_index = QSpinBox()
        self.sdr_index.setRange(0, 10)
        self.sdr_index.setValue(self.config.get('rtlsdr', {}).get('device_index', 0))
        layout.addWidget(self.sdr_index, 1, 1)

        widget.setLayout(layout)
        return widget

    def create_rtc_tab(self):
        """Create RTC configuration tab"""
        widget = QWidget()
        layout = QGridLayout()

        self.rtc_enabled = QCheckBox("Enable RTC")
        self.rtc_enabled.setChecked(self.config.get('rtc', {}).get('enabled', False))
        layout.addWidget(self.rtc_enabled, 0, 0, 1, 2)

        layout.addWidget(QLabel("RTC Type:"), 1, 0)
        self.rtc_type = QComboBox()
        self.rtc_type.addItems(['ds3231', 'ds1307', 'pcf8523', 'rv3028'])
        self.rtc_type.setCurrentText(self.config.get('rtc', {}).get('type', 'ds3231'))
        layout.addWidget(self.rtc_type, 1, 1)

        layout.addWidget(QLabel("I2C Device:"), 2, 0)
        self.rtc_i2c = QLineEdit(self.config.get('rtc', {}).get('i2c_device', '/dev/i2c-1'))
        layout.addWidget(self.rtc_i2c, 2, 1)

        widget.setLayout(layout)
        return widget

    def create_usb_tab(self):
        """Create USB configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.usb_enabled = QCheckBox("Enable USB Management")
        self.usb_enabled.setChecked(self.config.get('usb', {}).get('enabled', False))
        layout.addWidget(self.usb_enabled)

        widget.setLayout(layout)
        return widget

    def get_config(self):
        """Get updated configuration"""
        return {
            'gps': {
                'enabled': self.gps_enabled.isChecked(),
                'device': self.gps_device.text(),
                'baud_rate': self.gps_baud.value(),
            },
            'lora': {
                'enabled': self.lora_enabled.isChecked(),
                'spi_device': self.lora_spi.text(),
                'frequency': self.lora_freq.value() * 1000000,
            },
            'rtlsdr': {
                'enabled': self.sdr_enabled.isChecked(),
                'device_index': self.sdr_index.value(),
            },
            'rtc': {
                'enabled': self.rtc_enabled.isChecked(),
                'type': self.rtc_type.currentText(),
                'i2c_device': self.rtc_i2c.text(),
            },
            'usb': {
                'enabled': self.usb_enabled.isChecked(),
            },
        }
