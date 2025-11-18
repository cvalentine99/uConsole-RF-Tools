"""
GPS Panel - Real-time GPS data display and control
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QTextEdit, QCheckBox, QFileDialog)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import serial
import pynmea2
from datetime import datetime


class GPSPanel(QWidget):
    """GPS module control panel"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.serial_port = None
        self.is_logging = False
        self.log_file = None

        # GPS data
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.satellites = 0
        self.fix_quality = 0

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Status group
        status_group = QGroupBox("GPS Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Not Connected")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Position group
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout()

        self.lat_label = QLabel("Latitude: --")
        self.lon_label = QLabel("Longitude: --")
        self.alt_label = QLabel("Altitude: --")
        self.speed_label = QLabel("Speed: --")

        for label in [self.lat_label, self.lon_label, self.alt_label, self.speed_label]:
            label.setFont(QFont("Courier", 10))
            position_layout.addWidget(label)

        position_group.setLayout(position_layout)
        layout.addWidget(position_group)

        # Satellites group
        sat_group = QGroupBox("Satellites")
        sat_layout = QVBoxLayout()

        self.sat_count_label = QLabel("In View: 0 | Used: 0")
        self.sat_count_label.setFont(QFont("Arial", 10))
        sat_layout.addWidget(self.sat_count_label)

        self.sat_table = QTableWidget(0, 4)
        self.sat_table.setHorizontalHeaderLabels(['PRN', 'Elevation', 'Azimuth', 'SNR'])
        self.sat_table.setMaximumHeight(150)
        sat_layout.addWidget(self.sat_table)

        sat_group.setLayout(sat_layout)
        layout.addWidget(sat_group)

        # NMEA log group
        log_group = QGroupBox("NMEA Log")
        log_layout = QVBoxLayout()

        self.nmea_log = QTextEdit()
        self.nmea_log.setReadOnly(True)
        self.nmea_log.setMaximumHeight(100)
        self.nmea_log.setFont(QFont("Courier", 8))
        log_layout.addWidget(self.nmea_log)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        button_layout.addWidget(self.connect_btn)

        self.log_btn = QPushButton("Start Logging")
        self.log_btn.clicked.connect(self.toggle_logging)
        self.log_btn.setEnabled(False)
        button_layout.addWidget(self.log_btn)

        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)

    def initialize(self):
        """Initialize GPS module"""
        if self.config.get('enabled', False):
            self.toggle_connection()

    def toggle_connection(self):
        """Connect/disconnect GPS"""
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_gps()
        else:
            self.connect_gps()

    def connect_gps(self):
        """Connect to GPS device"""
        device = self.config.get('device', '/dev/ttyUSB0')
        baud_rate = self.config.get('baud_rate', 9600)

        try:
            self.serial_port = serial.Serial(device, baud_rate, timeout=1)
            self.status_label.setText(f"Connected to {device}")
            self.status_label.setStyleSheet("color: green;")
            self.connect_btn.setText("Disconnect")
            self.log_btn.setEnabled(True)
            self.update_timer.start(100)  # Update every 100ms
        except Exception as e:
            self.status_label.setText(f"Connection failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def disconnect_gps(self):
        """Disconnect from GPS"""
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray;")
        self.connect_btn.setText("Connect")
        self.log_btn.setEnabled(False)
        self.update_timer.stop()

        if self.is_logging:
            self.toggle_logging()

    def update_data(self):
        """Read and parse GPS data"""
        if not self.serial_port or not self.serial_port.is_open:
            return

        try:
            if self.serial_port.in_waiting:
                line = self.serial_port.readline().decode('ascii', errors='replace').strip()

                if line.startswith('$'):
                    self.nmea_log.append(line)

                    # Keep log at reasonable size
                    if self.nmea_log.document().lineCount() > 100:
                        cursor = self.nmea_log.textCursor()
                        cursor.movePosition(cursor.Start)
                        cursor.select(cursor.LineUnderCursor)
                        cursor.removeSelectedText()
                        cursor.deleteChar()  # Remove newline

                    # Parse NMEA
                    try:
                        msg = pynmea2.parse(line)
                        self.process_nmea(msg)
                    except:
                        pass

                    # Log to file if enabled
                    if self.is_logging and self.log_file:
                        self.log_file.write(line + '\n')
                        self.log_file.flush()

        except Exception as e:
            print(f"GPS update error: {e}")

    def process_nmea(self, msg):
        """Process NMEA message"""
        if isinstance(msg, pynmea2.GGA):
            # Position fix
            if msg.latitude and msg.longitude:
                self.latitude = msg.latitude
                self.longitude = msg.longitude
                self.altitude = msg.altitude if msg.altitude else 0.0

                self.lat_label.setText(f"Latitude:  {self.latitude:10.6f}°")
                self.lon_label.setText(f"Longitude: {self.longitude:10.6f}°")
                self.alt_label.setText(f"Altitude:  {self.altitude:8.1f} m")

                self.satellites = int(msg.num_sats) if msg.num_sats else 0
                self.fix_quality = int(msg.gps_qual) if msg.gps_qual else 0

                fix_types = ["No Fix", "GPS Fix", "DGPS Fix", "PPS Fix",
                           "RTK Fix", "Float RTK", "Dead Reckoning"]
                fix_str = fix_types[self.fix_quality] if self.fix_quality < len(fix_types) else "Unknown"

                self.status_label.setText(f"{fix_str} | {self.satellites} satellites")

                if self.fix_quality > 0:
                    self.status_label.setStyleSheet("color: green;")
                else:
                    self.status_label.setStyleSheet("color: orange;")

        elif isinstance(msg, pynmea2.RMC):
            # Speed and course
            if msg.spd_over_grnd:
                self.speed = float(msg.spd_over_grnd) * 1.852  # knots to km/h
                self.speed_label.setText(f"Speed:     {self.speed:6.1f} km/h")

        elif isinstance(msg, pynmea2.GSV):
            # Satellites in view
            # Update satellite table (simplified version)
            pass

    def toggle_logging(self):
        """Start/stop GPS track logging"""
        if self.is_logging:
            # Stop logging
            if self.log_file:
                self.log_file.close()
                self.log_file = None

            self.is_logging = False
            self.log_btn.setText("Start Logging")
        else:
            # Start logging
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save GPS Log", "", "NMEA Files (*.nmea);;All Files (*)"
            )

            if filename:
                try:
                    self.log_file = open(filename, 'w')
                    self.is_logging = True
                    self.log_btn.setText("Stop Logging")

                    # Write header
                    self.log_file.write(f"# GPS Log - Started {datetime.now()}\n")
                except Exception as e:
                    print(f"Failed to open log file: {e}")

    def clear_log(self):
        """Clear NMEA log display"""
        self.nmea_log.clear()

    def is_active(self):
        """Check if GPS is active"""
        return self.serial_port and self.serial_port.is_open

    def has_fix(self):
        """Check if GPS has valid fix"""
        return self.fix_quality > 0

    def get_satellite_count(self):
        """Get number of satellites"""
        return self.satellites

    def get_config(self):
        """Get current configuration"""
        return self.config

    def apply_config(self, config):
        """Apply new configuration"""
        self.config = config

    def rescan(self):
        """Rescan for GPS devices"""
        # Could scan /dev/ttyUSB* and /dev/ttyACM*
        pass

    def cleanup(self):
        """Cleanup resources"""
        self.disconnect_gps()
