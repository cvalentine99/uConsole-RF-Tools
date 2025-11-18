"""
RTC Panel - Real-Time Clock display and control
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTimeEdit, QDateEdit)
from PyQt5.QtCore import QTimer, QTime, QDate
from PyQt5.QtGui import QFont
from datetime import datetime


class RTCPanel(QWidget):
    """RTC module control panel"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.rtc_active = False

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Time display group
        time_group = QGroupBox("Current Time")
        time_layout = QVBoxLayout()

        self.time_label = QLabel("--:--:--")
        self.time_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.time_label.setStyleSheet("color: #00ff00;")
        time_layout.addWidget(self.time_label)

        self.date_label = QLabel("----/--/--")
        self.date_label.setFont(QFont("Arial", 18))
        time_layout.addWidget(self.date_label)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Temperature (DS3231 only)
        temp_group = QGroupBox("Temperature (DS3231)")
        temp_layout = QHBoxLayout()

        self.temp_label = QLabel("-- °C")
        self.temp_label.setFont(QFont("Arial", 14))
        temp_layout.addWidget(self.temp_label)

        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)

        # Set time group
        set_group = QGroupBox("Set Time")
        set_layout = QVBoxLayout()

        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Time:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        time_row.addWidget(self.time_edit)
        set_layout.addLayout(time_row)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        date_row.addWidget(self.date_edit)
        set_layout.addLayout(date_row)

        button_row = QHBoxLayout()
        set_btn = QPushButton("Set RTC Time")
        set_btn.clicked.connect(self.set_rtc_time)
        button_row.addWidget(set_btn)

        sync_btn = QPushButton("Sync from System")
        sync_btn.clicked.connect(self.sync_from_system)
        button_row.addWidget(sync_btn)

        set_layout.addLayout(button_row)
        set_group.setLayout(set_layout)
        layout.addWidget(set_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect RTC")
        self.connect_btn.clicked.connect(self.toggle_rtc)
        button_layout.addWidget(self.connect_btn)

        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)

    def initialize(self):
        """Initialize RTC"""
        if self.config.get('enabled', False):
            self.toggle_rtc()

    def toggle_rtc(self):
        """Connect/disconnect RTC"""
        if self.rtc_active:
            self.disconnect_rtc()
        else:
            self.connect_rtc()

    def connect_rtc(self):
        """Connect to RTC"""
        try:
            # Initialize RTC hardware
            self.rtc_active = True
            self.connect_btn.setText("Disconnect RTC")
            self.update_timer.start(1000)  # Update every second
        except Exception as e:
            print(f"RTC connection failed: {e}")

    def disconnect_rtc(self):
        """Disconnect RTC"""
        self.rtc_active = False
        self.connect_btn.setText("Connect RTC")
        self.update_timer.stop()

    def update_display(self):
        """Update time display"""
        if not self.rtc_active:
            return

        # Read RTC time (or use system time for demo)
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y-%m-%d (%A)"))

        # Update temperature (simulated)
        self.temp_label.setText("25.3 °C")

    def set_rtc_time(self):
        """Set RTC time"""
        time = self.time_edit.time()
        date = self.date_edit.date()

        # Set RTC hardware time
        print(f"Setting RTC: {date.toString()} {time.toString()}")

    def sync_from_system(self):
        """Sync RTC from system time"""
        now = datetime.now()
        self.time_edit.setTime(QTime(now.hour, now.minute, now.second))
        self.date_edit.setDate(QDate(now.year, now.month, now.day))

    def is_active(self):
        """Check if RTC is active"""
        return self.rtc_active

    def get_time_string(self):
        """Get time as string"""
        return self.time_label.text()

    def get_config(self):
        """Get configuration"""
        return self.config

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config

    def cleanup(self):
        """Cleanup resources"""
        self.disconnect_rtc()
