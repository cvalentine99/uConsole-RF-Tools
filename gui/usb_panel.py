"""
USB Panel - USB device management
"""

import logging

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer

logger = logging.getLogger(__name__)

# Try to import pyusb, handle gracefully if not installed
try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    logger.warning("pyusb not installed - USB device enumeration will be limited")


class USBPanel(QWidget):
    """USB device management panel"""

    def __init__(self, config):
        super().__init__()
        self.config = config

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Device list group
        devices_group = QGroupBox("USB Devices")
        devices_layout = QVBoxLayout()

        self.device_table = QTableWidget(0, 5)
        self.device_table.setHorizontalHeaderLabels([
            'Bus', 'Device', 'ID', 'Manufacturer', 'Product'
        ])
        self.device_table.setColumnWidth(2, 100)
        self.device_table.setColumnWidth(3, 200)
        self.device_table.setColumnWidth(4, 200)

        devices_layout.addWidget(self.device_table)

        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)

        # Control buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_devices)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def initialize(self):
        """Initialize USB management"""
        self.refresh_devices()

    def refresh_devices(self):
        """Refresh USB device list"""
        self.device_table.setRowCount(0)

        if not USB_AVAILABLE:
            # Show message when pyusb is not installed
            self.device_table.insertRow(0)
            self.device_table.setItem(0, 0, QTableWidgetItem("--"))
            self.device_table.setItem(0, 1, QTableWidgetItem("--"))
            self.device_table.setItem(0, 2, QTableWidgetItem("--"))
            self.device_table.setItem(0, 3, QTableWidgetItem("pyusb not installed"))
            self.device_table.setItem(0, 4, QTableWidgetItem("pip install pyusb"))
            return

        try:
            devices = usb.core.find(find_all=True)

            for dev in devices:
                row = self.device_table.rowCount()
                self.device_table.insertRow(row)

                self.device_table.setItem(row, 0, QTableWidgetItem(f"{dev.bus:03d}"))
                self.device_table.setItem(row, 1, QTableWidgetItem(f"{dev.address:03d}"))
                self.device_table.setItem(row, 2,
                    QTableWidgetItem(f"{dev.idVendor:04x}:{dev.idProduct:04x}"))

                try:
                    manufacturer = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else ""
                    product = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else ""
                except:
                    manufacturer = ""
                    product = ""

                self.device_table.setItem(row, 3, QTableWidgetItem(manufacturer))
                self.device_table.setItem(row, 4, QTableWidgetItem(product))

        except Exception as e:
            logger.error(f"Error refreshing USB devices: {e}")

    def is_active(self):
        """Check if USB panel is active"""
        return True  # USB enumeration is always available

    def get_config(self):
        """Get configuration"""
        return self.config

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config

    def rescan(self):
        """Rescan devices"""
        self.refresh_devices()

    def cleanup(self):
        """Cleanup resources"""
        pass
