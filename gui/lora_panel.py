"""
LoRa Panel - LoRa radio control and messaging
Supports Meshtastic API (recommended) and direct SX1262 control
Optimized for HackerGadgets uConsole AIO Extension Board (SX1262)
"""

import json
import logging
import threading
import time
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTextEdit, QLineEdit,
                             QSpinBox, QComboBox, QGridLayout, QMessageBox,
                             QCheckBox)
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class LoRaPanel(QWidget):
    """LoRa module control panel with Meshtastic support"""

    # Signal for thread-safe UI updates
    message_received = pyqtSignal(str, int, int)  # message, rssi, snr
    status_changed = pyqtSignal(str, str)  # status text, color

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.lora_active = False
        self.meshtastic_session = None
        self.polling_thread = None
        self.running = False

        self.last_rssi = None
        self.last_snr = None
        self.node_info = {}

        self.init_ui()

        # Connect signals
        self.message_received.connect(self._on_message_received)
        self.status_changed.connect(self._on_status_changed)

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Status group
        status_group = QGroupBox("LoRa Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Not Connected")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        # Signal info
        signal_layout = QHBoxLayout()
        self.rssi_label = QLabel("RSSI: -- dBm")
        signal_layout.addWidget(self.rssi_label)
        self.snr_label = QLabel("SNR: -- dB")
        signal_layout.addWidget(self.snr_label)
        signal_layout.addStretch()
        status_layout.addLayout(signal_layout)

        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['Meshtastic API (recommended)', 'Direct SPI (advanced)'])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        status_layout.addLayout(mode_layout)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Node info group
        node_group = QGroupBox("Node Information")
        node_layout = QVBoxLayout()

        self.node_label = QLabel("Node: --")
        node_layout.addWidget(self.node_label)

        self.channel_label = QLabel("Channel: --")
        node_layout.addWidget(self.channel_label)

        self.region_label = QLabel("Region: --")
        node_layout.addWidget(self.region_label)

        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # Configuration group (for direct mode)
        self.config_group = QGroupBox("Radio Configuration")
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
        self.power_spin.setRange(2, 22)
        self.power_spin.setValue(17)
        config_layout.addWidget(self.power_spin, 3, 1)

        self.config_group.setLayout(config_layout)
        self.config_group.setVisible(False)  # Hidden by default in Meshtastic mode
        layout.addWidget(self.config_group)

        # Transmit group
        tx_group = QGroupBox("Send Message")
        tx_layout = QVBoxLayout()

        self.tx_input = QLineEdit()
        self.tx_input.setPlaceholderText("Enter message to send...")
        self.tx_input.returnPressed.connect(self.send_message)
        tx_layout.addWidget(self.tx_input)

        tx_btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send Message")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        tx_btn_layout.addWidget(self.send_btn)

        self.broadcast_check = QCheckBox("Broadcast")
        self.broadcast_check.setChecked(True)
        tx_btn_layout.addWidget(self.broadcast_check)

        tx_layout.addLayout(tx_btn_layout)
        tx_group.setLayout(tx_layout)
        layout.addWidget(tx_group)

        # Receive group
        rx_group = QGroupBox("Messages")
        rx_layout = QVBoxLayout()

        self.rx_log = QTextEdit()
        self.rx_log.setReadOnly(True)
        self.rx_log.setFont(QFont("Courier", 9))
        rx_layout.addWidget(self.rx_log)

        rx_btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.rx_log.clear)
        rx_btn_layout.addWidget(clear_btn)

        rx_layout.addLayout(rx_btn_layout)
        rx_group.setLayout(rx_layout)
        layout.addWidget(rx_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_lora)
        button_layout.addWidget(self.connect_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_mode_changed(self, index):
        """Handle mode change"""
        self.config_group.setVisible(index == 1)  # Show config for direct mode

    def initialize(self):
        """Initialize LoRa module"""
        if self.config.get('enabled', False):
            self.toggle_lora()

    def toggle_lora(self):
        """Connect/disconnect LoRa"""
        if self.lora_active:
            self.disconnect_lora()
        else:
            self.connect_lora()

    def connect_lora(self):
        """Connect to LoRa radio"""
        mode = self.mode_combo.currentIndex()

        if mode == 0:
            self._connect_meshtastic()
        else:
            self._connect_direct()

    def _connect_meshtastic(self):
        """Connect via Meshtastic HTTP API"""
        try:
            import requests

            host = self.config.get('meshtastic_host', 'localhost')
            port = self.config.get('meshtastic_port', 443)

            # Create session for connection reuse
            self.meshtastic_session = requests.Session()
            self.meshtastic_session.verify = False  # Self-signed cert

            # Suppress InsecureRequestWarning
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Test connection by getting node info
            url = f"https://{host}:{port}/api/v1/fromradio?all=false"
            response = self.meshtastic_session.get(url, timeout=5)

            if response.status_code == 200:
                self.lora_active = True
                self.running = True

                self.status_label.setText(f"Connected to Meshtastic ({host})")
                self.status_label.setStyleSheet("color: green;")
                self.connect_btn.setText("Disconnect")
                self.send_btn.setEnabled(True)

                # Get node info
                self._get_meshtastic_info()

                # Start polling for messages
                self.polling_thread = threading.Thread(target=self._poll_meshtastic, daemon=True)
                self.polling_thread.start()

                self.log_message("Connected to Meshtastic")
                logger.info(f"Connected to Meshtastic at {host}:{port}")

            else:
                raise Exception(f"API returned status {response.status_code}")

        except ImportError:
            self.status_label.setText("requests library not installed")
            self.status_label.setStyleSheet("color: red;")
            logger.error("requests library not installed")
        except Exception as e:
            self.status_label.setText(f"Connection failed: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"Meshtastic connection failed: {e}")

    def _get_meshtastic_info(self):
        """Get node information from Meshtastic"""
        if not self.meshtastic_session:
            return

        try:
            host = self.config.get('meshtastic_host', 'localhost')
            port = self.config.get('meshtastic_port', 443)

            # Try to get my node info
            url = f"https://{host}:{port}/api/v1/fromradio?all=true"
            response = self.meshtastic_session.get(url, timeout=5)

            if response.status_code == 200:
                # Parse protobuf response (simplified - actual would need protobuf)
                self.node_label.setText("Node: Local Meshtastic Node")
                self.channel_label.setText("Channel: Primary")
                self.region_label.setText("Region: US (915 MHz)")

        except Exception as e:
            logger.error(f"Failed to get Meshtastic info: {e}")

    def _poll_meshtastic(self):
        """Poll Meshtastic for new messages"""
        host = self.config.get('meshtastic_host', 'localhost')
        port = self.config.get('meshtastic_port', 443)

        while self.running and self.meshtastic_session:
            try:
                url = f"https://{host}:{port}/api/v1/fromradio?all=false"
                response = self.meshtastic_session.get(url, timeout=10)

                if response.status_code == 200 and response.content:
                    # Process received data
                    # In a full implementation, this would decode protobuf messages
                    pass

            except Exception as e:
                if self.running:
                    logger.debug(f"Meshtastic poll: {e}")

            time.sleep(1)

    def _connect_direct(self):
        """Connect directly to SX1262 via SPI"""
        # Warn user about meshtasticd conflict
        reply = QMessageBox.warning(
            self,
            "Direct SPI Mode",
            "Direct SPI mode requires meshtasticd to be stopped.\n\n"
            "Run: sudo systemctl stop meshtasticd\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            import spidev

            spi_device = self.config.get('spi_device', '/dev/spidev1.0')
            bus, device = 1, 0  # Default for spidev1.0

            if 'spidev' in spi_device:
                parts = spi_device.replace('/dev/spidev', '').split('.')
                if len(parts) == 2:
                    bus, device = int(parts[0]), int(parts[1])

            self.spi = spidev.SpiDev()
            self.spi.open(bus, device)
            self.spi.max_speed_hz = 1000000
            self.spi.mode = 0

            # Try to read SX1262 version register
            # SX1262 uses different commands than SX127x
            # This is simplified - full implementation would need complete driver

            self.lora_active = True
            self.status_label.setText("SPI Connected (SX1262)")
            self.status_label.setStyleSheet("color: green;")
            self.connect_btn.setText("Disconnect")
            self.send_btn.setEnabled(True)

            self.log_message("Direct SPI mode - SX1262")
            logger.info("Connected to SX1262 via SPI")

        except ImportError:
            self.status_label.setText("spidev not installed")
            self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.status_label.setText(f"SPI failed: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"SPI connection failed: {e}")

    def disconnect_lora(self):
        """Disconnect LoRa"""
        self.running = False
        self.lora_active = False

        if self.polling_thread:
            self.polling_thread.join(timeout=2.0)
            self.polling_thread = None

        if self.meshtastic_session:
            self.meshtastic_session.close()
            self.meshtastic_session = None

        if hasattr(self, 'spi') and self.spi:
            try:
                self.spi.close()
            except:
                pass
            self.spi = None

        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray;")
        self.connect_btn.setText("Connect")
        self.send_btn.setEnabled(False)

        logger.info("LoRa disconnected")

    def send_message(self):
        """Send message via LoRa"""
        if not self.lora_active:
            return

        message = self.tx_input.text().strip()
        if not message:
            return

        try:
            if self.meshtastic_session:
                self._send_meshtastic(message)
            else:
                self._send_direct(message)

            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_message(f"[{timestamp}] TX: {message}")
            self.tx_input.clear()

        except Exception as e:
            self.log_message(f"Send failed: {str(e)}")
            logger.error(f"LoRa send failed: {e}")

    def _send_meshtastic(self, message):
        """Send message via Meshtastic API"""
        host = self.config.get('meshtastic_host', 'localhost')
        port = self.config.get('meshtastic_port', 443)

        # Meshtastic HTTP API for sending text
        url = f"https://{host}:{port}/api/v1/sendtext"

        data = {
            "text": message,
        }

        if self.broadcast_check.isChecked():
            data["to"] = "^all"

        response = self.meshtastic_session.post(url, json=data, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Send failed: {response.status_code}")

    def _send_direct(self, message):
        """Send message via direct SPI"""
        # Simplified - full implementation would encode and transmit via SX1262
        self.log_message("Direct TX (SX1262) - Not fully implemented")

    def _on_message_received(self, message, rssi, snr):
        """Handle received message (called from main thread)"""
        self.last_rssi = rssi
        self.last_snr = snr

        self.rssi_label.setText(f"RSSI: {rssi} dBm")
        self.snr_label.setText(f"SNR: {snr} dB")

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_message(f"[{timestamp}] RX ({rssi} dBm): {message}")

    def _on_status_changed(self, text, color):
        """Handle status change (called from main thread)"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.rx_log.append(f"[{timestamp}] {message}")

    def is_active(self):
        """Check if LoRa is active"""
        return self.lora_active

    def get_last_rssi(self):
        """Get last packet RSSI"""
        return self.last_rssi

    def get_config(self):
        """Get current configuration"""
        return {
            'enabled': self.lora_active,
            'mode': 'meshtastic' if self.mode_combo.currentIndex() == 0 else 'direct',
            'meshtastic_host': self.config.get('meshtastic_host', 'localhost'),
            'meshtastic_port': self.config.get('meshtastic_port', 443),
            'spi_device': self.config.get('spi_device', '/dev/spidev1.0'),
            'frequency': self.freq_spin.value() * 1000000,
            'spreading_factor': int(self.sf_combo.currentText()),
            'bandwidth': int(self.bw_combo.currentText()) * 1000,
            'tx_power': self.power_spin.value(),
            'gpio_busy': self.config.get('gpio_busy', 24),
            'gpio_reset': self.config.get('gpio_reset', 25),
            'gpio_irq': self.config.get('gpio_irq', 26),
        }

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config

        mode = config.get('mode', 'meshtastic')
        self.mode_combo.setCurrentIndex(0 if mode == 'meshtastic' else 1)

        if 'frequency' in config:
            self.freq_spin.setValue(config['frequency'] // 1000000)
        if 'spreading_factor' in config:
            idx = self.sf_combo.findText(str(config['spreading_factor']))
            if idx >= 0:
                self.sf_combo.setCurrentIndex(idx)
        if 'bandwidth' in config:
            bw_khz = config['bandwidth'] // 1000
            idx = self.bw_combo.findText(str(bw_khz))
            if idx >= 0:
                self.bw_combo.setCurrentIndex(idx)
        if 'tx_power' in config:
            self.power_spin.setValue(config['tx_power'])

    def rescan(self):
        """Rescan for LoRa devices"""
        logger.info("Scanning for LoRa/Meshtastic...")

        # Check if meshtasticd is running
        import subprocess
        try:
            result = subprocess.run(['systemctl', 'is-active', 'meshtasticd'],
                                  capture_output=True, text=True, timeout=5)
            if result.stdout.strip() == 'active':
                logger.info("Meshtasticd is running - Meshtastic mode available")
            else:
                logger.info("Meshtasticd not running - Direct SPI mode available")
        except:
            pass

    def cleanup(self):
        """Cleanup resources"""
        self.disconnect_lora()
