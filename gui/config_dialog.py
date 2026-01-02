"""
Configuration Dialog
Optimized for HackerGadgets uConsole AIO Extension Board
"""

import copy
import logging

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox,
                             QPushButton, QGroupBox, QGridLayout, QComboBox)

logger = logging.getLogger(__name__)


class ConfigDialog(QDialog):
    """Configuration dialog for all modules"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        # Deep copy to prevent modifying original config
        self.config = copy.deepcopy(config)

        self.setWindowTitle("Configuration - uConsole AIO")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)

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
        layout = QVBoxLayout()

        # Enable checkbox
        self.gps_enabled = QCheckBox("Enable GPS")
        self.gps_enabled.setChecked(self.config.get('gps', {}).get('enabled', False))
        layout.addWidget(self.gps_enabled)

        # Mode group
        mode_group = QGroupBox("Connection Mode")
        mode_layout = QGridLayout()

        mode_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.gps_mode = QComboBox()
        self.gps_mode.addItems(['gpsd (recommended)', 'Direct Serial'])
        mode = self.config.get('gps', {}).get('mode', 'gpsd')
        self.gps_mode.setCurrentIndex(0 if mode == 'gpsd' else 1)
        mode_layout.addWidget(self.gps_mode, 0, 1)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # gpsd settings
        gpsd_group = QGroupBox("gpsd Settings")
        gpsd_layout = QGridLayout()

        gpsd_layout.addWidget(QLabel("Host:"), 0, 0)
        self.gps_gpsd_host = QLineEdit(self.config.get('gps', {}).get('gpsd_host', 'localhost'))
        gpsd_layout.addWidget(self.gps_gpsd_host, 0, 1)

        gpsd_layout.addWidget(QLabel("Port:"), 1, 0)
        self.gps_gpsd_port = QSpinBox()
        self.gps_gpsd_port.setRange(1, 65535)
        self.gps_gpsd_port.setValue(self.config.get('gps', {}).get('gpsd_port', 2947))
        gpsd_layout.addWidget(self.gps_gpsd_port, 1, 1)

        gpsd_group.setLayout(gpsd_layout)
        layout.addWidget(gpsd_group)

        # Serial settings
        serial_group = QGroupBox("Serial Settings (Direct Mode)")
        serial_layout = QGridLayout()

        serial_layout.addWidget(QLabel("Device:"), 0, 0)
        self.gps_device = QLineEdit(self.config.get('gps', {}).get('device', '/dev/ttyAMA10'))
        serial_layout.addWidget(self.gps_device, 0, 1)

        serial_layout.addWidget(QLabel("Baud Rate:"), 1, 0)
        self.gps_baud = QSpinBox()
        self.gps_baud.setRange(4800, 115200)
        self.gps_baud.setValue(self.config.get('gps', {}).get('baud_rate', 9600))
        serial_layout.addWidget(self.gps_baud, 1, 1)

        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_lora_tab(self):
        """Create LoRa configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.lora_enabled = QCheckBox("Enable LoRa")
        self.lora_enabled.setChecked(self.config.get('lora', {}).get('enabled', False))
        layout.addWidget(self.lora_enabled)

        # Mode group
        mode_group = QGroupBox("Connection Mode")
        mode_layout = QGridLayout()

        mode_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.lora_mode = QComboBox()
        self.lora_mode.addItems(['Meshtastic API (recommended)', 'Direct SPI'])
        mode = self.config.get('lora', {}).get('mode', 'meshtastic')
        self.lora_mode.setCurrentIndex(0 if mode == 'meshtastic' else 1)
        mode_layout.addWidget(self.lora_mode, 0, 1)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Meshtastic settings
        mesh_group = QGroupBox("Meshtastic Settings")
        mesh_layout = QGridLayout()

        mesh_layout.addWidget(QLabel("Host:"), 0, 0)
        self.lora_mesh_host = QLineEdit(self.config.get('lora', {}).get('meshtastic_host', 'localhost'))
        mesh_layout.addWidget(self.lora_mesh_host, 0, 1)

        mesh_layout.addWidget(QLabel("Port:"), 1, 0)
        self.lora_mesh_port = QSpinBox()
        self.lora_mesh_port.setRange(1, 65535)
        self.lora_mesh_port.setValue(self.config.get('lora', {}).get('meshtastic_port', 443))
        mesh_layout.addWidget(self.lora_mesh_port, 1, 1)

        mesh_group.setLayout(mesh_layout)
        layout.addWidget(mesh_group)

        # Radio settings
        radio_group = QGroupBox("Radio Settings (SX1262)")
        radio_layout = QGridLayout()

        radio_layout.addWidget(QLabel("SPI Device:"), 0, 0)
        self.lora_spi = QLineEdit(self.config.get('lora', {}).get('spi_device', '/dev/spidev1.0'))
        radio_layout.addWidget(self.lora_spi, 0, 1)

        radio_layout.addWidget(QLabel("Frequency (MHz):"), 1, 0)
        self.lora_freq = QSpinBox()
        self.lora_freq.setRange(400, 1000)
        self.lora_freq.setValue(self.config.get('lora', {}).get('frequency', 915000000) // 1000000)
        radio_layout.addWidget(self.lora_freq, 1, 1)

        radio_layout.addWidget(QLabel("TX Power (dBm):"), 2, 0)
        self.lora_power = QSpinBox()
        self.lora_power.setRange(2, 22)
        self.lora_power.setValue(self.config.get('lora', {}).get('tx_power', 17))
        radio_layout.addWidget(self.lora_power, 2, 1)

        radio_group.setLayout(radio_layout)
        layout.addWidget(radio_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_rtlsdr_tab(self):
        """Create RTL-SDR configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.sdr_enabled = QCheckBox("Enable RTL-SDR")
        self.sdr_enabled.setChecked(self.config.get('rtlsdr', {}).get('enabled', False))
        layout.addWidget(self.sdr_enabled)

        # Device settings
        device_group = QGroupBox("Device Settings")
        device_layout = QGridLayout()

        device_layout.addWidget(QLabel("Device Index:"), 0, 0)
        self.sdr_index = QSpinBox()
        self.sdr_index.setRange(0, 10)
        self.sdr_index.setValue(self.config.get('rtlsdr', {}).get('device_index', 0))
        device_layout.addWidget(self.sdr_index, 0, 1)

        device_group.setLayout(device_layout)
        layout.addWidget(device_group)

        # Default settings
        defaults_group = QGroupBox("Default Settings")
        defaults_layout = QGridLayout()

        defaults_layout.addWidget(QLabel("Frequency (MHz):"), 0, 0)
        self.sdr_freq = QSpinBox()
        self.sdr_freq.setRange(24, 1766)
        self.sdr_freq.setValue(self.config.get('rtlsdr', {}).get('frequency', 100000000) // 1000000)
        defaults_layout.addWidget(self.sdr_freq, 0, 1)

        defaults_layout.addWidget(QLabel("Sample Rate:"), 1, 0)
        self.sdr_sample_rate = QComboBox()
        self.sdr_sample_rate.addItems(['1.024 MHz', '2.048 MHz', '2.4 MHz'])
        sr = self.config.get('rtlsdr', {}).get('sample_rate', 2048000)
        if sr == 1024000:
            self.sdr_sample_rate.setCurrentIndex(0)
        elif sr == 2400000:
            self.sdr_sample_rate.setCurrentIndex(2)
        else:
            self.sdr_sample_rate.setCurrentIndex(1)
        defaults_layout.addWidget(self.sdr_sample_rate, 1, 1)

        defaults_layout.addWidget(QLabel("Gain:"), 2, 0)
        self.sdr_gain = QComboBox()
        self.sdr_gain.addItems(['Auto', '10 dB', '20 dB', '30 dB', '40 dB'])
        defaults_layout.addWidget(self.sdr_gain, 2, 1)

        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_rtc_tab(self):
        """Create RTC configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.rtc_enabled = QCheckBox("Enable RTC")
        self.rtc_enabled.setChecked(self.config.get('rtc', {}).get('enabled', False))
        layout.addWidget(self.rtc_enabled)

        # RTC settings
        rtc_group = QGroupBox("RTC Settings")
        rtc_layout = QGridLayout()

        rtc_layout.addWidget(QLabel("RTC Type:"), 0, 0)
        self.rtc_type = QComboBox()
        self.rtc_type.addItems(['pcf85063a', 'ds3231', 'system'])
        self.rtc_type.setCurrentText(self.config.get('rtc', {}).get('type', 'pcf85063a'))
        rtc_layout.addWidget(self.rtc_type, 0, 1)

        rtc_layout.addWidget(QLabel("I2C Bus:"), 1, 0)
        self.rtc_i2c_bus = QSpinBox()
        self.rtc_i2c_bus.setRange(0, 30)
        self.rtc_i2c_bus.setValue(self.config.get('rtc', {}).get('i2c_bus', 22))
        rtc_layout.addWidget(self.rtc_i2c_bus, 1, 1)

        rtc_layout.addWidget(QLabel("I2C Address:"), 2, 0)
        self.rtc_i2c_addr = QLineEdit(hex(self.config.get('rtc', {}).get('i2c_address', 0x51)))
        rtc_layout.addWidget(self.rtc_i2c_addr, 2, 1)

        rtc_group.setLayout(rtc_layout)
        layout.addWidget(rtc_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_usb_tab(self):
        """Create USB configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.usb_enabled = QCheckBox("Enable USB Device Management")
        self.usb_enabled.setChecked(self.config.get('usb', {}).get('enabled', True))
        layout.addWidget(self.usb_enabled)

        # Info label
        info_label = QLabel(
            "USB device enumeration allows viewing connected USB devices.\n\n"
            "No additional configuration required."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def get_config(self):
        """Get updated configuration - preserves all fields"""
        # Start with deep copy of original config
        config = copy.deepcopy(self.config)

        # Update GPS settings
        config.setdefault('gps', {})
        config['gps']['enabled'] = self.gps_enabled.isChecked()
        config['gps']['mode'] = 'gpsd' if self.gps_mode.currentIndex() == 0 else 'serial'
        config['gps']['gpsd_host'] = self.gps_gpsd_host.text()
        config['gps']['gpsd_port'] = self.gps_gpsd_port.value()
        config['gps']['device'] = self.gps_device.text()
        config['gps']['baud_rate'] = self.gps_baud.value()

        # Update LoRa settings
        config.setdefault('lora', {})
        config['lora']['enabled'] = self.lora_enabled.isChecked()
        config['lora']['mode'] = 'meshtastic' if self.lora_mode.currentIndex() == 0 else 'direct'
        config['lora']['meshtastic_host'] = self.lora_mesh_host.text()
        config['lora']['meshtastic_port'] = self.lora_mesh_port.value()
        config['lora']['spi_device'] = self.lora_spi.text()
        config['lora']['frequency'] = self.lora_freq.value() * 1000000
        config['lora']['tx_power'] = self.lora_power.value()

        # Update RTL-SDR settings
        config.setdefault('rtlsdr', {})
        config['rtlsdr']['enabled'] = self.sdr_enabled.isChecked()
        config['rtlsdr']['device_index'] = self.sdr_index.value()
        config['rtlsdr']['frequency'] = self.sdr_freq.value() * 1000000

        sr_text = self.sdr_sample_rate.currentText()
        if '1.024' in sr_text:
            config['rtlsdr']['sample_rate'] = 1024000
        elif '2.4' in sr_text:
            config['rtlsdr']['sample_rate'] = 2400000
        else:
            config['rtlsdr']['sample_rate'] = 2048000

        gain_text = self.sdr_gain.currentText()
        if 'Auto' in gain_text:
            config['rtlsdr']['gain'] = 'auto'
        else:
            config['rtlsdr']['gain'] = int(gain_text.replace(' dB', ''))

        # Update RTC settings
        config.setdefault('rtc', {})
        config['rtc']['enabled'] = self.rtc_enabled.isChecked()
        config['rtc']['type'] = self.rtc_type.currentText()
        config['rtc']['i2c_bus'] = self.rtc_i2c_bus.value()
        try:
            config['rtc']['i2c_address'] = int(self.rtc_i2c_addr.text(), 16)
        except ValueError:
            config['rtc']['i2c_address'] = 0x51

        # Update USB settings
        config.setdefault('usb', {})
        config['usb']['enabled'] = self.usb_enabled.isChecked()

        return config
