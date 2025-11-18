#!/usr/bin/env python3
"""
Hardware Control Center - Unified GUI Application

A comprehensive graphical interface for managing:
- RTL-SDR (Software Defined Radio)
- LoRa (Long Range Radio)
- GPS (Global Positioning System)
- RTC (Real-Time Clock)
- USB Hub (Device Management)

Requirements:
    pip install PyQt5 pyqtgraph numpy pyserial pyusb

Usage:
    python3 main.py [--config config.json]
"""

import sys
import os
import json
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

class HardwareControlCenter(QMainWindow):
    """Main application window"""

    def __init__(self, config_file=None):
        super().__init__()

        self.config_file = config_file or "configs/default.json"
        self.config = self.load_config()

        self.init_ui()
        self.init_modules()
        self.init_timers()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Hardware Control Center")
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
        try:
            # Initialize each panel's hardware
            if self.config.get('rtlsdr', {}).get('enabled', False):
                self.rtlsdr_panel.initialize()
                self.statusBar.showMessage("RTL-SDR initialized")

            if self.config.get('lora', {}).get('enabled', False):
                self.lora_panel.initialize()
                self.statusBar.showMessage("LoRa initialized")

            if self.config.get('gps', {}).get('enabled', False):
                self.gps_panel.initialize()
                self.statusBar.showMessage("GPS initialized")

            if self.config.get('rtc', {}).get('enabled', False):
                self.rtc_panel.initialize()
                self.statusBar.showMessage("RTC initialized")

            if self.config.get('usb', {}).get('enabled', False):
                self.usb_panel.initialize()
                self.statusBar.showMessage("USB initialized")

            self.statusBar.showMessage("All modules initialized", 3000)

        except Exception as e:
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

        if self.gps_panel.is_active():
            fix = "FIX" if self.gps_panel.has_fix() else "NO FIX"
            sats = self.gps_panel.get_satellite_count()
            status_parts.append(f"GPS: {fix} ({sats} sats)")

        if self.lora_panel.is_active():
            rssi = self.lora_panel.get_last_rssi()
            status_parts.append(f"LoRa: {rssi} dBm")

        if self.rtc_panel.is_active():
            time_str = self.rtc_panel.get_time_string()
            status_parts.append(f"RTC: {time_str}")

        if status_parts:
            self.statusBar.showMessage(" | ".join(status_parts))

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()

    def get_default_config(self):
        """Get default configuration"""
        return {
            'rtlsdr': {
                'enabled': False,
                'device_index': 0,
                'sample_rate': 2048000,
                'frequency': 100000000,
            },
            'lora': {
                'enabled': False,
                'spi_device': '/dev/spidev0.0',
                'frequency': 915000000,
                'spreading_factor': 7,
            },
            'gps': {
                'enabled': True,
                'device': '/dev/ttyUSB0',
                'baud_rate': 9600,
            },
            'rtc': {
                'enabled': True,
                'type': 'ds3231',
                'i2c_device': '/dev/i2c-1',
            },
            'usb': {
                'enabled': True,
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
        }

        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            self.statusBar.showMessage(f"Configuration saved to {filename}", 3000)
            return True
        except Exception as e:
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

    def show_settings(self):
        """Show settings dialog"""
        dialog = ConfigDialog(self.config, self)
        if dialog.exec_():
            self.config = dialog.get_config()
            self.apply_config()

    def rescan_devices(self):
        """Rescan all hardware devices"""
        self.statusBar.showMessage("Rescanning devices...")

        self.gps_panel.rescan()
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
        <p>Version 1.0</p>
        <p>A unified interface for managing hardware modules:</p>
        <ul>
        <li>RTL-SDR - Software Defined Radio</li>
        <li>LoRa - Long Range Radio</li>
        <li>GPS - Global Positioning System</li>
        <li>RTC - Real-Time Clock</li>
        <li>USB Hub - Device Management</li>
        </ul>
        <p><b>Built with:</b> PyQt5, Python 3</p>
        <p><b>License:</b> MIT</p>
        """

        QMessageBox.about(self, "About Hardware Control Center", about_text)

    def show_documentation(self):
        """Show documentation"""
        docs_text = """
        <h3>Hardware Control Center Documentation</h3>

        <h4>Quick Start:</h4>
        <ol>
        <li>Connect your hardware modules (GPS, LoRa, RTC, etc.)</li>
        <li>Configure each module using the Settings dialog</li>
        <li>Enable modules in the configuration</li>
        <li>Use the tabs to control each module</li>
        </ol>

        <h4>Features:</h4>
        <ul>
        <li><b>GPS Tab:</b> View position, satellites, and track logging</li>
        <li><b>LoRa Tab:</b> Send/receive messages, view signal stats</li>
        <li><b>RTL-SDR Tab:</b> Spectrum scanning and signal capture</li>
        <li><b>RTC Tab:</b> Time display, alarm configuration</li>
        <li><b>USB Tab:</b> Device enumeration and power control</li>
        </ul>

        <p>For complete documentation, see the README files in each module directory.</p>
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

        QLabel {
            color: #ffffff;
        }

        QPushButton {
            background-color: #4a4a4a;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 5px 15px;
            border-radius: 3px;
        }

        QPushButton:hover {
            background-color: #5a5a5a;
        }

        QPushButton:pressed {
            background-color: #3a3a3a;
        }

        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #4a4a4a;
            padding: 3px;
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
            # Cleanup modules
            self.rtlsdr_panel.cleanup()
            self.lora_panel.cleanup()
            self.gps_panel.cleanup()
            self.rtc_panel.cleanup()
            self.usb_panel.cleanup()

            event.accept()
        else:
            event.ignore()


def main():
    """Main application entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Hardware Control Center')
    parser.add_argument('--config', help='Configuration file path',
                       default='configs/default.json')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Start in fullscreen mode')

    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Hardware Control Center")
    app.setOrganizationName("Hardware API Examples")

    window = HardwareControlCenter(config_file=args.config)

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
