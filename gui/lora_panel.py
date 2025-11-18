"""
LoRa Panel - LoRa radio control and messaging
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTextEdit, QLineEdit,
                             QSpinBox, QComboBox, QGridLayout)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from datetime import datetime


class LoRaPanel(QWidget):
    """LoRa module control panel"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.lora_device = None
        self.last_rssi = -120
        self.last_snr = 0

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Status group
        status_group = QGroupBox("LoRa Status")
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Not Initialized")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        self.rssi_label = QLabel("RSSI: -- dBm")
        status_layout.addWidget(self.rssi_label)

        self.snr_label = QLabel("SNR: -- dB")
        status_layout.addWidget(self.snr_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Configuration group
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()

        config_layout.addWidget(QLabel("Frequency (MHz):"), 0, 0)
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(400, 1000)
        self.freq_spin.setValue(915)
        self.freq_spin.setSuffix(" MHz")
        config_layout.addWidget(self.freq_spin, 0, 1)

        config_layout.addWidget(QLabel("Spreading Factor:"), 1, 0)
        self.sf_combo = QComboBox()
        self.sf_combo.addItems(['7', '8', '9', '10', '11', '12'])
        config_layout.addWidget(self.sf_combo, 1, 1)

        config_layout.addWidget(QLabel("Bandwidth (kHz):"), 2, 0)
        self.bw_combo = QComboBox()
        self.bw_combo.addItems(['125', '250', '500'])
        config_layout.addWidget(self.bw_combo, 2, 1)

        config_layout.addWidget(QLabel("TX Power (dBm):"), 3, 0)
        self.power_spin = QSpinBox()
        self.power_spin.setRange(2, 20)
        self.power_spin.setValue(17)
        config_layout.addWidget(self.power_spin, 3, 1)

        self.apply_config_btn = QPushButton("Apply Configuration")
        self.apply_config_btn.clicked.connect(self.apply_lora_config)
        config_layout.addWidget(self.apply_config_btn, 4, 0, 1, 2)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Transmit group
        tx_group = QGroupBox("Transmit")
        tx_layout = QVBoxLayout()

        self.tx_input = QLineEdit()
        self.tx_input.setPlaceholderText("Enter message to send...")
        self.tx_input.returnPressed.connect(self.send_message)
        tx_layout.addWidget(self.tx_input)

        self.send_btn = QPushButton("Send Message")
        self.send_btn.clicked.connect(self.send_message)
        tx_layout.addWidget(self.send_btn)

        tx_group.setLayout(tx_layout)
        layout.addWidget(tx_group)

        # Receive group
        rx_group = QGroupBox("Received Messages")
        rx_layout = QVBoxLayout()

        self.rx_log = QTextEdit()
        self.rx_log.setReadOnly(True)
        self.rx_log.setFont(QFont("Courier", 9))
        rx_layout.addWidget(self.rx_log)

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.rx_log.clear)
        rx_layout.addWidget(clear_btn)

        rx_group.setLayout(rx_layout)
        layout.addWidget(rx_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.init_btn = QPushButton("Initialize LoRa")
        self.init_btn.clicked.connect(self.toggle_lora)
        button_layout.addWidget(self.init_btn)

        self.listen_btn = QPushButton("Start Listening")
        self.listen_btn.clicked.connect(self.toggle_listening)
        self.listen_btn.setEnabled(False)
        button_layout.addWidget(self.listen_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Update timer for RX
        self.rx_timer = QTimer()
        self.rx_timer.timeout.connect(self.check_messages)

    def initialize(self):
        """Initialize LoRa module"""
        if self.config.get('enabled', False):
            self.toggle_lora()

    def toggle_lora(self):
        """Initialize/deinitialize LoRa"""
        if self.lora_device:
            self.deinit_lora()
        else:
            self.init_lora()

    def init_lora(self):
        """Initialize LoRa radio"""
        try:
            # Here you would initialize actual LoRa hardware
            # For now, simulate
            self.lora_device = True

            self.status_label.setText("LoRa Ready")
            self.status_label.setStyleSheet("color: green;")
            self.init_btn.setText("Deinitialize LoRa")
            self.listen_btn.setEnabled(True)
            self.send_btn.setEnabled(True)

            self.log_message("LoRa initialized successfully")

        except Exception as e:
            self.status_label.setText(f"Init failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def deinit_lora(self):
        """Deinitialize LoRa"""
        self.lora_device = None
        self.status_label.setText("Not Initialized")
        self.status_label.setStyleSheet("color: gray;")
        self.init_btn.setText("Initialize LoRa")
        self.listen_btn.setEnabled(False)
        self.send_btn.setEnabled(False)

        if self.rx_timer.isActive():
            self.rx_timer.stop()
            self.listen_btn.setText("Start Listening")

    def apply_lora_config(self):
        """Apply LoRa configuration"""
        freq = self.freq_spin.value() * 1000000  # MHz to Hz
        sf = int(self.sf_combo.currentText())
        bw = int(self.bw_combo.currentText()) * 1000  # kHz to Hz
        power = self.power_spin.value()

        # Apply configuration to hardware
        self.log_message(f"Configuration: {freq/1e6} MHz, SF{sf}, BW{bw/1e3} kHz, {power} dBm")

    def send_message(self):
        """Send LoRa message"""
        if not self.lora_device:
            return

        message = self.tx_input.text()
        if not message:
            return

        try:
            # Send message via LoRa hardware
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_message(f"[{timestamp}] TX: {message}")
            self.tx_input.clear()

        except Exception as e:
            self.log_message(f"Send failed: {str(e)}")

    def toggle_listening(self):
        """Start/stop listening for messages"""
        if self.rx_timer.isActive():
            self.rx_timer.stop()
            self.listen_btn.setText("Start Listening")
        else:
            self.rx_timer.start(100)  # Check every 100ms
            self.listen_btn.setText("Stop Listening")

    def check_messages(self):
        """Check for received messages"""
        if not self.lora_device:
            return

        # Check for received messages from LoRa hardware
        # Simulated for now
        pass

    def log_message(self, message):
        """Add message to RX log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.rx_log.append(f"[{timestamp}] {message}")

    def is_active(self):
        """Check if LoRa is active"""
        return self.lora_device is not None

    def get_last_rssi(self):
        """Get last packet RSSI"""
        return self.last_rssi

    def get_config(self):
        """Get current configuration"""
        return {
            'enabled': self.lora_device is not None,
            'frequency': self.freq_spin.value() * 1000000,
            'spreading_factor': int(self.sf_combo.currentText()),
            'bandwidth': int(self.bw_combo.currentText()) * 1000,
            'tx_power': self.power_spin.value(),
        }

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config
        if 'frequency' in config:
            self.freq_spin.setValue(config['frequency'] // 1000000)
        if 'spreading_factor' in config:
            self.sf_combo.setCurrentText(str(config['spreading_factor']))

    def cleanup(self):
        """Cleanup resources"""
        self.deinit_lora()
