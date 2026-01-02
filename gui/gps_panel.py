"""
GPS Panel - Real-time GPS data display and control
Supports gpsd (recommended) and direct serial connection
Optimized for HackerGadgets uConsole AIO Extension Board
"""

import json
import logging
import socket
import threading
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QTextEdit, QFileDialog, QComboBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class GPSPanel(QWidget):
    """GPS module control panel with gpsd support"""

    # Signals for thread-safe UI updates
    data_updated = pyqtSignal(dict)
    log_message_signal = pyqtSignal(str)  # Thread-safe log updates

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.gpsd_socket = None
        self.gpsd_thread = None
        self.serial_port = None  # Initialize serial_port attribute
        self.running = False
        self.is_logging = False
        self.log_file = None
        self._config_enabled = config.get('enabled', False)  # Track configured state

        # GPS data
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.track = 0.0
        self.satellites = 0
        self.satellites_used = 0
        self.fix_mode = 0  # 0=unknown, 1=no fix, 2=2D, 3=3D
        self.hdop = 0.0
        self.time_utc = ""
        self.satellite_list = []

        self.init_ui()

        # Connect signals for thread-safe updates
        self.data_updated.connect(self._update_ui_from_data)
        self.log_message_signal.connect(self._do_append_log)

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Status group
        status_group = QGroupBox("GPS Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Not Connected")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        # Connection mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['gpsd (recommended)', 'Direct Serial'])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        status_layout.addLayout(mode_layout)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Position group
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout()

        self.lat_label = QLabel("Latitude:  --")
        self.lon_label = QLabel("Longitude: --")
        self.alt_label = QLabel("Altitude:  --")
        self.speed_label = QLabel("Speed:     --")
        self.track_label = QLabel("Track:     --")
        self.time_label = QLabel("UTC Time:  --")
        self.hdop_label = QLabel("HDOP:      --")

        for label in [self.lat_label, self.lon_label, self.alt_label,
                      self.speed_label, self.track_label, self.time_label,
                      self.hdop_label]:
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

        self.sat_table = QTableWidget(0, 5)
        self.sat_table.setHorizontalHeaderLabels(['PRN', 'Elevation', 'Azimuth', 'SNR', 'Used'])
        self.sat_table.setMaximumHeight(150)
        self.sat_table.horizontalHeader().setStretchLastSection(True)
        sat_layout.addWidget(self.sat_table)

        sat_group.setLayout(sat_layout)
        layout.addWidget(sat_group)

        # Raw data log group
        log_group = QGroupBox("Raw Data")
        log_layout = QVBoxLayout()

        self.raw_log = QTextEdit()
        self.raw_log.setReadOnly(True)
        self.raw_log.setMaximumHeight(100)
        self.raw_log.setFont(QFont("Courier", 8))
        log_layout.addWidget(self.raw_log)

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

    def initialize(self):
        """Initialize GPS module"""
        if self.config.get('enabled', False):
            self.toggle_connection()

    def toggle_connection(self):
        """Connect/disconnect GPS"""
        if self.running:
            self.disconnect_gps()
        else:
            self.connect_gps()

    def connect_gps(self):
        """Connect to GPS via gpsd or serial"""
        # Use combo box as single source of truth for mode
        if self.mode_combo.currentIndex() == 0:
            self._connect_gpsd()
        else:
            self._connect_serial()

    def _connect_gpsd(self):
        """Connect to gpsd daemon"""
        host = self.config.get('gpsd_host', 'localhost')
        port = self.config.get('gpsd_port', 2947)

        try:
            self.gpsd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.gpsd_socket.settimeout(5.0)
            self.gpsd_socket.connect((host, port))

            # Enable watch mode
            watch_cmd = '?WATCH={"enable":true,"json":true}\n'
            self.gpsd_socket.send(watch_cmd.encode())

            self.running = True
            self.gpsd_thread = threading.Thread(target=self._gpsd_reader, daemon=True)
            self.gpsd_thread.start()

            self.status_label.setText(f"Connected to gpsd ({host}:{port})")
            self.status_label.setStyleSheet("color: green;")
            self.connect_btn.setText("Disconnect")
            self.log_btn.setEnabled(True)

            logger.info(f"Connected to gpsd at {host}:{port}")

        except Exception as e:
            self.status_label.setText(f"gpsd connection failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"gpsd connection failed: {e}")
            if self.gpsd_socket:
                self.gpsd_socket.close()
                self.gpsd_socket = None

    def _connect_serial(self):
        """Connect directly to GPS serial port (fallback)"""
        try:
            import serial
            device = self.config.get('device', '/dev/ttyAMA10')
            baud_rate = self.config.get('baud_rate', 9600)

            self.serial_port = serial.Serial(device, baud_rate, timeout=1)
            self.running = True

            self.gpsd_thread = threading.Thread(target=self._serial_reader, daemon=True)
            self.gpsd_thread.start()

            self.status_label.setText(f"Connected to {device}")
            self.status_label.setStyleSheet("color: green;")
            self.connect_btn.setText("Disconnect")
            self.log_btn.setEnabled(True)

            logger.info(f"Connected to serial GPS at {device}")

        except Exception as e:
            self.status_label.setText(f"Serial connection failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"Serial GPS connection failed: {e}")

    def _gpsd_reader(self):
        """Background thread to read from gpsd"""
        buffer = ""

        while self.running and self.gpsd_socket:
            try:
                self.gpsd_socket.settimeout(1.0)
                data = self.gpsd_socket.recv(4096).decode('utf-8', errors='replace')

                if not data:
                    continue

                buffer += data

                # Process complete JSON objects
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()

                    if line:
                        try:
                            msg = json.loads(line)
                            self._process_gpsd_message(msg)
                        except json.JSONDecodeError:
                            pass

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"gpsd read error: {e}")
                break

    def _serial_reader(self):
        """Background thread to read from serial port"""
        try:
            import pynmea2
        except ImportError:
            logger.error("pynmea2 not installed for serial GPS")
            return

        while self.running and hasattr(self, 'serial_port') and self.serial_port.is_open:
            try:
                line = self.serial_port.readline().decode('ascii', errors='replace').strip()

                if line.startswith('$'):
                    try:
                        msg = pynmea2.parse(line)
                        self._process_nmea(msg, line)
                    except pynmea2.ParseError as e:
                        logger.debug(f"NMEA parse error: {e}")

            except Exception as e:
                if self.running:
                    logger.error(f"Serial read error: {e}")
                break

    def _process_gpsd_message(self, msg):
        """Process a gpsd JSON message"""
        msg_class = msg.get('class', '')

        if msg_class == 'TPV':
            # Time-Position-Velocity report
            data = {
                'latitude': msg.get('lat', 0.0),
                'longitude': msg.get('lon', 0.0),
                'altitude': msg.get('altMSL', msg.get('alt', 0.0)),
                'speed': msg.get('speed', 0.0) * 3.6 if msg.get('speed') else 0.0,  # m/s to km/h
                'track': msg.get('track', 0.0),
                'fix_mode': msg.get('mode', 0),
                'time_utc': msg.get('time', ''),
                'hdop': msg.get('hdop', 0.0),
            }
            self.data_updated.emit(data)

            # Log raw data
            self._append_log(f"TPV: lat={data['latitude']:.6f} lon={data['longitude']:.6f}")

        elif msg_class == 'SKY':
            # Satellite report
            satellites = msg.get('satellites', [])
            used = sum(1 for s in satellites if s.get('used', False))

            data = {
                'satellites': len(satellites),
                'satellites_used': used,
                'satellite_list': satellites,
            }
            self.data_updated.emit(data)

        elif msg_class == 'VERSION':
            logger.info(f"gpsd version: {msg.get('release', 'unknown')}")

    def _process_nmea(self, msg, raw_line):
        """Process NMEA message from serial"""
        import pynmea2

        self._append_log(raw_line)

        if isinstance(msg, pynmea2.GGA):
            if msg.latitude and msg.longitude:
                data = {
                    'latitude': msg.latitude,
                    'longitude': msg.longitude,
                    'altitude': float(msg.altitude) if msg.altitude else 0.0,
                    'satellites_used': int(msg.num_sats) if msg.num_sats else 0,
                    'hdop': float(msg.horizontal_dil) if msg.horizontal_dil else 0.0,
                    'fix_mode': 3 if int(msg.gps_qual or 0) > 0 else 1,
                }
                self.data_updated.emit(data)

        elif isinstance(msg, pynmea2.RMC):
            if msg.spd_over_grnd:
                data = {
                    'speed': float(msg.spd_over_grnd) * 1.852,  # knots to km/h
                    'track': float(msg.true_course) if msg.true_course else 0.0,
                }
                self.data_updated.emit(data)

        elif isinstance(msg, pynmea2.GSV):
            # Satellite in view - simplified handling
            pass

    def _update_ui_from_data(self, data):
        """Update UI elements from GPS data (called from main thread)"""
        if 'latitude' in data:
            self.latitude = data['latitude']
            self.lat_label.setText(f"Latitude:  {self.latitude:12.7f}°")

        if 'longitude' in data:
            self.longitude = data['longitude']
            self.lon_label.setText(f"Longitude: {self.longitude:12.7f}°")

        if 'altitude' in data:
            self.altitude = data['altitude']
            self.alt_label.setText(f"Altitude:  {self.altitude:8.1f} m")

        if 'speed' in data:
            self.speed = data['speed']
            self.speed_label.setText(f"Speed:     {self.speed:8.1f} km/h")

        if 'track' in data:
            self.track = data['track']
            self.track_label.setText(f"Track:     {self.track:8.1f}°")

        if 'time_utc' in data:
            self.time_utc = data['time_utc']
            # Format time nicely - extract time part after 'T'
            if self.time_utc and 'T' in self.time_utc:
                time_part = self.time_utc.split('T')[1].split('.')[0]
                self.time_label.setText(f"UTC Time:  {time_part}")
            elif self.time_utc:
                self.time_label.setText(f"UTC Time:  {self.time_utc}")

        if 'hdop' in data:
            self.hdop = data['hdop']
            self.hdop_label.setText(f"HDOP:      {self.hdop:.1f}")

        if 'fix_mode' in data:
            self.fix_mode = data['fix_mode']
            self._update_fix_status()

        if 'satellites' in data:
            self.satellites = data['satellites']
            # Update display when either value changes
            self.sat_count_label.setText(f"In View: {self.satellites} | Used: {self.satellites_used}")

        if 'satellites_used' in data:
            self.satellites_used = data['satellites_used']
            # Update display when either value changes
            self.sat_count_label.setText(f"In View: {self.satellites} | Used: {self.satellites_used}")

        if 'satellite_list' in data:
            self._update_satellite_table(data['satellite_list'])

    def _update_fix_status(self):
        """Update fix status display"""
        fix_names = {0: "Unknown", 1: "No Fix", 2: "2D Fix", 3: "3D Fix"}
        fix_str = fix_names.get(self.fix_mode, "Unknown")

        if self.fix_mode >= 2:
            self.status_label.setText(f"{fix_str} | {self.satellites_used} satellites")
            self.status_label.setStyleSheet("color: #00ff00;")  # Bright green
        elif self.fix_mode == 1:
            self.status_label.setText(f"Acquiring | {self.satellites} in view")
            self.status_label.setStyleSheet("color: orange;")
        else:
            self.status_label.setText("Searching for satellites...")
            self.status_label.setStyleSheet("color: yellow;")

    def _update_satellite_table(self, satellites):
        """Update the satellite table"""
        self.sat_table.setRowCount(len(satellites))

        for row, sat in enumerate(satellites):
            prn = str(sat.get('PRN', sat.get('prn', '--')))
            el = str(sat.get('el', '--'))
            az = str(sat.get('az', '--'))
            snr = str(sat.get('ss', sat.get('snr', '--')))
            used = "Yes" if sat.get('used', False) else "No"

            self.sat_table.setItem(row, 0, QTableWidgetItem(prn))
            self.sat_table.setItem(row, 1, QTableWidgetItem(el))
            self.sat_table.setItem(row, 2, QTableWidgetItem(az))
            self.sat_table.setItem(row, 3, QTableWidgetItem(snr))
            self.sat_table.setItem(row, 4, QTableWidgetItem(used))

    def _append_log(self, text):
        """Append text to raw log (thread-safe via signal)"""
        # Emit signal for thread-safe UI update
        self.log_message_signal.emit(text)

        # Write to file if logging (file I/O is safe from background thread)
        if self.is_logging and self.log_file:
            try:
                self.log_file.write(f"{datetime.now().isoformat()} {text}\n")
                self.log_file.flush()
            except Exception as e:
                logger.error(f"Log write error: {e}")

    def _do_append_log(self, text):
        """Actually append text to raw log (called from main thread)"""
        # Limit log size
        if self.raw_log.document().lineCount() > 100:
            cursor = self.raw_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 10)
            cursor.removeSelectedText()

        self.raw_log.append(text)

    def disconnect_gps(self):
        """Disconnect from GPS"""
        self.running = False

        if self.gpsd_socket:
            try:
                self.gpsd_socket.close()
            except:
                pass
            self.gpsd_socket = None

        if hasattr(self, 'serial_port') and self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None

        if self.gpsd_thread:
            self.gpsd_thread.join(timeout=2.0)
            self.gpsd_thread = None

        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray;")
        self.connect_btn.setText("Connect")
        self.log_btn.setEnabled(False)

        if self.is_logging:
            self.toggle_logging()

        logger.info("GPS disconnected")

    def toggle_logging(self):
        """Start/stop GPS data logging"""
        if self.is_logging:
            # Stop logging
            if self.log_file:
                try:
                    self.log_file.close()
                except:
                    pass
                self.log_file = None

            self.is_logging = False
            self.log_btn.setText("Start Logging")
            logger.info("GPS logging stopped")
        else:
            # Start logging
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save GPS Log", f"gps_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;NMEA Files (*.nmea);;All Files (*)"
            )

            if filename:
                try:
                    self.log_file = open(filename, 'w')
                    self.log_file.write(f"# GPS Log - Started {datetime.now().isoformat()}\n")
                    self.log_file.write(f"# Device: HackerGadgets AIO - gpsd mode\n\n")
                    self.is_logging = True
                    self.log_btn.setText("Stop Logging")
                    logger.info(f"GPS logging to {filename}")
                except Exception as e:
                    logger.error(f"Failed to open log file: {e}")

    def clear_log(self):
        """Clear raw data log display"""
        self.raw_log.clear()

    def is_active(self):
        """Check if GPS is active"""
        return self.running

    def has_fix(self):
        """Check if GPS has valid fix"""
        return self.fix_mode >= 2

    def get_satellite_count(self):
        """Get number of satellites used"""
        return self.satellites_used

    def get_position(self):
        """Get current position as tuple (lat, lon, alt)"""
        return (self.latitude, self.longitude, self.altitude)

    def get_config(self):
        """Get current configuration"""
        config = self.config.copy()
        config['mode'] = 'gpsd' if self.mode_combo.currentIndex() == 0 else 'serial'
        return config

    def apply_config(self, config):
        """Apply new configuration"""
        self.config = config
        mode = config.get('mode', 'gpsd')
        self.mode_combo.setCurrentIndex(0 if mode == 'gpsd' else 1)

    def rescan(self):
        """Rescan for GPS devices"""
        # Check if gpsd is available
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1.0)
            host = self.config.get('gpsd_host', 'localhost')
            port = self.config.get('gpsd_port', 2947)
            test_socket.connect((host, port))
            test_socket.close()
            logger.info(f"gpsd available at {host}:{port}")
        except:
            logger.warning("gpsd not available")

    def cleanup(self):
        """Cleanup resources"""
        self.disconnect_gps()
