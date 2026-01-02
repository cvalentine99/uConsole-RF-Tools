#!/usr/bin/env python3
"""
Hardware Control Center - Unified GUI Application
Optimized for HackerGadgets uConsole AIO Extension Board

A comprehensive graphical interface for managing:
- RTL-SDR (Software Defined Radio) - RTL2832U + R860
- LoRa (Long Range Radio) - SX1262 via Meshtastic
- GPS (Global Positioning System) - via gpsd
- RTC (Real-Time Clock) - PCF85063A
- USB Hub (Device Management)

Requirements:
    pip install -r requirements.txt

Usage:
    python3 main.py [--config config.json]
"""

import sys
import os
import json
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QStatusBar, QAction, QMessageBox, QFileDialog,
                             QDialog, QVBoxLayout, QLabel)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

# Import GUI modules
from gui.rtlsdr_panel import RTLSDRPanel
from gui.lora_panel import LoRaPanel
from gui.gps_panel import GPSPanel
from gui.rtc_panel import RTCPanel
from gui.usb_panel import USBPanel
from gui.config_dialog import ConfigDialog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HardwareControlCenter(QMainWindow):
    """Main application window"""

    def __init__(self, config_file=None):
        super().__init__()

        self.config_file = config_file or "configs/default.json"
        self.config = self.load_config()
        self.status_timer = None

        self.init_ui()
        self.init_modules()
        self.init_timers()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Hardware Control Center - uConsole AIO")
        self.setGeometry(100, 100, 1200, 800)

        # Create central tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create module panels
        self.rtlsdr_panel = RTLSDRPanel(self.config.get('rtlsdr', {}))
        self.lora_panel = LoRaPanel(self.config.get('lora', {}))
        self.gps_panel = GPSPanel(self.config.get('gps', {}))
        self.rtc_panel = RTCPanel(self.config.get('rtc', {}))
        self.usb_panel = USBPanel(self.config.get('usb', {}))

        # Add tabs
        self.tabs.addTab(self.gps_panel, "GPS")
        self.tabs.addTab(self.lora_panel, "LoRa")
        self.tabs.addTab(self.rtlsdr_panel, "RTL-SDR")
        self.tabs.addTab(self.rtc_panel, "RTC")
        self.tabs.addTab(self.usb_panel, "USB Devices")

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Apply stylesheet
        self.apply_stylesheet()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        open_config_action = QAction('Open Configuration...', self)
        open_config_action.triggered.connect(self.open_configuration)
        file_menu.addAction(open_config_action)

        save_config_action = QAction('Save Configuration...', self)
        save_config_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_config_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('View')

        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')

        settings_action = QAction('Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        rescan_action = QAction('Rescan Devices', self)
        rescan_action.setShortcut('F5')
        rescan_action.triggered.connect(self.rescan_devices)
        tools_menu.addAction(rescan_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        docs_action = QAction('Documentation', self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)

    def init_modules(self):
        """Initialize hardware modules"""
        init_status = []

        try:
            if self.config.get('gps', {}).get('enabled', False):
                try:
                    self.gps_panel.initialize()
                    init_status.append("GPS: OK")
                    logger.info("GPS initialized successfully")
                except Exception as e:
                    init_status.append(f"GPS: Failed")
                    logger.error(f"GPS initialization failed: {e}")

            if self.config.get('lora', {}).get('enabled', False):
                try:
                    self.lora_panel.initialize()
                    init_status.append("LoRa: OK")
                    logger.info("LoRa initialized successfully")
                except Exception as e:
                    init_status.append(f"LoRa: Failed")
                    logger.error(f"LoRa initialization failed: {e}")

            if self.config.get('rtlsdr', {}).get('enabled', False):
                try:
                    self.rtlsdr_panel.initialize()
                    init_status.append("SDR: OK")
                    logger.info("RTL-SDR initialized successfully")
                except Exception as e:
                    init_status.append(f"SDR: Failed")
                    logger.error(f"RTL-SDR initialization failed: {e}")

            if self.config.get('rtc', {}).get('enabled', False):
                try:
                    self.rtc_panel.initialize()
                    init_status.append("RTC: OK")
                    logger.info("RTC initialized successfully")
                except Exception as e:
                    init_status.append(f"RTC: Failed")
                    logger.error(f"RTC initialization failed: {e}")

            if self.config.get('usb', {}).get('enabled', False):
                try:
                    self.usb_panel.initialize()
                    init_status.append("USB: OK")
                    logger.info("USB initialized successfully")
                except Exception as e:
                    init_status.append(f"USB: Failed")
                    logger.error(f"USB initialization failed: {e}")

            # Show combined status
            if init_status:
                self.statusBar.showMessage(" | ".join(init_status), 5000)
            else:
                self.statusBar.showMessage("No modules enabled", 3000)

        except Exception as e:
            logger.error(f"Module initialization error: {e}")
            QMessageBox.critical(self, "Initialization Error",
                               f"Failed to initialize modules:\n{str(e)}")

    def init_timers(self):
        """Initialize update timers"""
        # Status update timer (every second)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def update_status(self):
        """Update status bar with module information"""
        status_parts = []

        try:
            if self.gps_panel.is_active():
                fix = "FIX" if self.gps_panel.has_fix() else "NO FIX"
                sats = self.gps_panel.get_satellite_count()
                status_parts.append(f"GPS: {fix} ({sats} sats)")

            if self.lora_panel.is_active():
                rssi = self.lora_panel.get_last_rssi()
                if rssi is not None:
                    status_parts.append(f"LoRa: {rssi} dBm")
                else:
                    status_parts.append("LoRa: Ready")

            if self.rtlsdr_panel.is_active():
                freq = self.rtlsdr_panel.get_frequency()
                if freq:
                    status_parts.append(f"SDR: {freq/1e6:.1f} MHz")

            if self.rtc_panel.is_active():
                time_str = self.rtc_panel.get_time_string()
                status_parts.append(f"RTC: {time_str}")

            if status_parts:
                self.statusBar.showMessage(" | ".join(status_parts))
        except Exception as e:
            logger.error(f"Status update error: {e}")

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_file}")
                    return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            logger.warning(f"Config file not found: {self.config_file}, using defaults")
            return self.get_default_config()

    def get_default_config(self):
        """Get default configuration for HackerGadgets AIO board"""
        return {
            'rtlsdr': {
                'enabled': True,
                'device_index': 0,
                'sample_rate': 2048000,
                'frequency': 100000000,
                'gain': 'auto',
            },
            'lora': {
                'enabled': False,
                'mode': 'meshtastic',  # 'meshtastic' or 'direct'
                'meshtastic_host': 'localhost',
                'meshtastic_port': 443,
                'spi_device': '/dev/spidev1.0',
                'frequency': 915000000,
                'spreading_factor': 7,
                'bandwidth': 125000,
                'tx_power': 17,
                'gpio_busy': 24,
                'gpio_reset': 25,
                'gpio_irq': 26,
            },
            'gps': {
                'enabled': True,
                'mode': 'gpsd',  # 'gpsd' or 'serial'
                'gpsd_host': 'localhost',
                'gpsd_port': 2947,
                'device': '/dev/ttyAMA10',
                'baud_rate': 9600,
            },
            'rtc': {
                'enabled': True,
                'type': 'pcf85063a',
                'i2c_bus': 22,  # i2c_csi_dsi0
                'i2c_address': 0x51,
            },
            'usb': {
                'enabled': True,
            },
            'logging': {
                'level': 'info',
                'console': True,
            },
        }

    def save_config(self, filename=None):
        """Save configuration to file"""
        filename = filename or self.config_file

        # Gather config from all panels
        config = {
            'rtlsdr': self.rtlsdr_panel.get_config(),
            'lora': self.lora_panel.get_config(),
            'gps': self.gps_panel.get_config(),
            'rtc': self.rtc_panel.get_config(),
            'usb': self.usb_panel.get_config(),
            'logging': self.config.get('logging', {'level': 'info', 'console': True}),
        }

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            self.statusBar.showMessage(f"Configuration saved to {filename}", 3000)
            logger.info(f"Configuration saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            QMessageBox.critical(self, "Save Error",
                               f"Failed to save configuration:\n{str(e)}")
            return False

    def open_configuration(self):
        """Open configuration file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Configuration", "", "JSON Files (*.json);;All Files (*)"
        )

        if filename:
            self.config_file = filename
            self.config = self.load_config()
            self.apply_config()
            self.reinit_modules()
            self.statusBar.showMessage(f"Loaded configuration from {filename}", 3000)

    def save_configuration(self):
        """Save configuration file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", self.config_file,
            "JSON Files (*.json);;All Files (*)"
        )

        if filename:
            self.save_config(filename)

    def apply_config(self):
        """Apply configuration to all panels"""
        self.rtlsdr_panel.apply_config(self.config.get('rtlsdr', {}))
        self.lora_panel.apply_config(self.config.get('lora', {}))
        self.gps_panel.apply_config(self.config.get('gps', {}))
        self.rtc_panel.apply_config(self.config.get('rtc', {}))
        self.usb_panel.apply_config(self.config.get('usb', {}))

    def reinit_modules(self):
        """Reinitialize all modules after config change"""
        # Cleanup existing connections
        self.rtlsdr_panel.cleanup()
        self.lora_panel.cleanup()
        self.gps_panel.cleanup()
        self.rtc_panel.cleanup()
        self.usb_panel.cleanup()

        # Reinitialize
        self.init_modules()

    def show_settings(self):
        """Show settings dialog"""
        dialog = ConfigDialog(self.config, self)
        if dialog.exec_():
            new_config = dialog.get_config()

            # Check if enabled states changed
            needs_reinit = False
            for module in ['gps', 'lora', 'rtlsdr', 'rtc', 'usb']:
                old_enabled = self.config.get(module, {}).get('enabled', False)
                new_enabled = new_config.get(module, {}).get('enabled', False)
                if old_enabled != new_enabled:
                    needs_reinit = True
                    break

            self.config = new_config
            self.apply_config()

            if needs_reinit:
                self.reinit_modules()

    def rescan_devices(self):
        """Rescan all hardware devices"""
        self.statusBar.showMessage("Rescanning devices...")
        logger.info("Rescanning all devices")

        # Rescan all panels
        self.gps_panel.rescan()
        self.lora_panel.rescan()
        self.rtlsdr_panel.rescan()
        self.rtc_panel.rescan()
        self.usb_panel.rescan()

        self.statusBar.showMessage("Rescan complete", 3000)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Hardware Control Center</h2>
        <p>Version 2.0 - uConsole AIO Edition</p>
        <p>Optimized for HackerGadgets All-In-One Extension Board</p>
        <br>
        <p><b>Supported Hardware:</b></p>
        <ul>
        <li>RTL-SDR (RTL2832U + R860)</li>
        <li>LoRa (SX1262 via Meshtastic)</li>
        <li>GPS (Multi-GNSS via gpsd)</li>
        <li>RTC (PCF85063A)</li>
        <li>USB Hub</li>
        </ul>
        <br>
        <p><b>Built with:</b> PyQt5, Python 3</p>
        <p><b>License:</b> MIT</p>
        """

        QMessageBox.about(self, "About Hardware Control Center", about_text)

    def show_documentation(self):
        """Show documentation"""
        docs_text = """
        <h3>Hardware Control Center - uConsole AIO</h3>

        <h4>Quick Start:</h4>
        <ol>
        <li>Ensure gpsd is running for GPS</li>
        <li>Meshtasticd provides LoRa access</li>
        <li>RTL-SDR works directly via USB</li>
        <li>RTC is accessed via I2C</li>
        </ol>

        <h4>Device Paths:</h4>
        <ul>
        <li><b>GPS:</b> /dev/ttyAMA10 (via gpsd on port 2947)</li>
        <li><b>LoRa:</b> /dev/spidev1.0 (GPIO 24/25/26)</li>
        <li><b>RTL-SDR:</b> USB device index 0</li>
        <li><b>RTC:</b> I2C bus, address 0x51</li>
        </ul>

        <h4>Services:</h4>
        <ul>
        <li><b>gpsd:</b> GPS daemon (port 2947)</li>
        <li><b>meshtasticd:</b> LoRa mesh (port 443)</li>
        </ul>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Documentation")
        msg.setTextFormat(Qt.RichText)
        msg.setText(docs_text)
        msg.exec_()

    def apply_stylesheet(self):
        """Apply application stylesheet"""
        stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
        }

        QTabWidget::pane {
            border: 1px solid #3a3a3a;
            background-color: #2b2b2b;
        }

        QTabBar::tab {
            background-color: #3a3a3a;
            color: #ffffff;
            padding: 8px 20px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #4a4a4a;
        }

        QTabBar::tab:hover {
            background-color: #5a5a5a;
        }

        QGroupBox {
            color: #ffffff;
            border: 1px solid #4a4a4a;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        QLabel {
            color: #ffffff;
        }

        QPushButton {
            background-color: #4a4a4a;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 5px 15px;
            border-radius: 3px;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #5a5a5a;
        }

        QPushButton:pressed {
            background-color: #3a3a3a;
        }

        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
        }

        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #4a4a4a;
            padding: 3px;
        }

        QTableWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            gridline-color: #4a4a4a;
        }

        QTableWidget::item {
            padding: 5px;
        }

        QHeaderView::section {
            background-color: #3a3a3a;
            color: #ffffff;
            padding: 5px;
            border: 1px solid #4a4a4a;
        }

        QStatusBar {
            background-color: #3a3a3a;
            color: #ffffff;
        }

        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QMenuBar::item:selected {
            background-color: #4a4a4a;
        }

        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #4a4a4a;
        }

        QMenu::item:selected {
            background-color: #4a4a4a;
        }

        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
        }

        QScrollBar::handle:vertical {
            background-color: #4a4a4a;
            min-height: 20px;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """

        self.setStyleSheet(stylesheet)

    def closeEvent(self, event):
        """Handle application close"""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.info("Application closing...")

            # Stop timers first to prevent callbacks on destroyed objects
            if self.status_timer:
                self.status_timer.stop()
                self.status_timer = None

            # Cleanup modules
            self.rtlsdr_panel.cleanup()
            self.lora_panel.cleanup()
            self.gps_panel.cleanup()
            self.rtc_panel.cleanup()
            self.usb_panel.cleanup()

            logger.info("Cleanup complete")
            event.accept()
        else:
            event.ignore()


def main():
    """Main application entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Hardware Control Center - uConsole AIO')
    parser.add_argument('--config', help='Configuration file path',
                       default='configs/default.json')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Start in fullscreen mode')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    app = QApplication(sys.argv)
    app.setApplicationName("Hardware Control Center")
    app.setOrganizationName("uConsole AIO")

    window = HardwareControlCenter(config_file=args.config)

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
