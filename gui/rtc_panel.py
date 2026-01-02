"""
RTC Panel - Real-Time Clock display and control
Supports PCF85063A (HackerGadgets AIO) and DS3231
Optimized for HackerGadgets uConsole AIO Extension Board
"""

import logging
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTimeEdit, QDateEdit,
                             QComboBox, QMessageBox)
from PyQt5.QtCore import QTimer, QTime, QDate
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

# PCF85063A Register definitions
PCF85063A_ADDR = 0x51
PCF85063A_REG_CTRL1 = 0x00
PCF85063A_REG_CTRL2 = 0x01
PCF85063A_REG_SECONDS = 0x04
PCF85063A_REG_MINUTES = 0x05
PCF85063A_REG_HOURS = 0x06
PCF85063A_REG_DAYS = 0x07
PCF85063A_REG_WEEKDAYS = 0x08
PCF85063A_REG_MONTHS = 0x09
PCF85063A_REG_YEARS = 0x0A

# DS3231 Register definitions (for compatibility)
DS3231_ADDR = 0x68
DS3231_REG_SECONDS = 0x00
DS3231_REG_TEMP_MSB = 0x11


def bcd_to_dec(bcd):
    """Convert BCD to decimal"""
    return ((bcd >> 4) * 10) + (bcd & 0x0F)


def dec_to_bcd(dec):
    """Convert decimal to BCD"""
    return ((dec // 10) << 4) | (dec % 10)


class RTCPanel(QWidget):
    """RTC module control panel with PCF85063A support"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.rtc_active = False
        self.i2c_bus = None
        self.rtc_type = config.get('type', 'pcf85063a')
        self.rtc_address = config.get('i2c_address', PCF85063A_ADDR)

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

        # RTC Info group
        info_group = QGroupBox("RTC Information")
        info_layout = QVBoxLayout()

        self.status_label = QLabel("Not Connected")
        self.status_label.setFont(QFont("Arial", 10))
        info_layout.addWidget(self.status_label)

        self.chip_label = QLabel("Chip: --")
        info_layout.addWidget(self.chip_label)

        self.battery_label = QLabel("Battery: --")
        info_layout.addWidget(self.battery_label)

        # RTC type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("RTC Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['PCF85063A (AIO)', 'DS3231', 'System RTC'])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        info_layout.addLayout(type_layout)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

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

        sync_to_sys_btn = QPushButton("Sync to System")
        sync_to_sys_btn.clicked.connect(self.sync_to_system)
        button_row.addWidget(sync_to_sys_btn)

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
        rtc_type = self.type_combo.currentText()

        if 'System' in rtc_type:
            self._connect_system_rtc()
        else:
            self._connect_i2c_rtc()

    def _connect_system_rtc(self):
        """Use system RTC (hwclock)"""
        try:
            # Check if we can access system RTC using subprocess
            result = subprocess.run(['hwclock', '-r'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                self.rtc_active = True
                self.rtc_type = 'system'
                self.connect_btn.setText("Disconnect RTC")
                self.status_label.setText("Connected to System RTC")
                self.status_label.setStyleSheet("color: green;")
                self.chip_label.setText("Chip: System hwclock")
                self.battery_label.setText("Battery: N/A")
                self.update_timer.start(1000)
                logger.info("Connected to system RTC")
            else:
                raise Exception("hwclock not accessible")
        except subprocess.TimeoutExpired:
            self.status_label.setText("System RTC: timeout")
            self.status_label.setStyleSheet("color: red;")
            logger.error("System RTC connection timed out")
        except Exception as e:
            self.status_label.setText(f"System RTC failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"System RTC connection failed: {e}")

    def _connect_i2c_rtc(self):
        """Connect to I2C RTC (PCF85063A or DS3231)"""
        try:
            import smbus2

            # Determine I2C bus
            i2c_bus_num = self.config.get('i2c_bus', 1)

            # Try to find the correct bus
            # On uConsole AIO, PCF85063A might be on a specific bus
            possible_buses = [i2c_bus_num, 1, 22, 11, 3]

            rtc_type = self.type_combo.currentText()
            if 'PCF85063A' in rtc_type:
                self.rtc_address = PCF85063A_ADDR
                self.rtc_type = 'pcf85063a'
            else:
                self.rtc_address = DS3231_ADDR
                self.rtc_type = 'ds3231'

            connected = False
            for bus_num in possible_buses:
                try:
                    self.i2c_bus = smbus2.SMBus(bus_num)
                    # Try to read from the RTC
                    if self.rtc_type == 'pcf85063a':
                        self.i2c_bus.read_byte_data(self.rtc_address, PCF85063A_REG_SECONDS)
                    else:
                        self.i2c_bus.read_byte_data(self.rtc_address, DS3231_REG_SECONDS)
                    connected = True
                    logger.info(f"Found RTC on I2C bus {bus_num} at address 0x{self.rtc_address:02x}")
                    break
                except Exception:
                    if self.i2c_bus:
                        self.i2c_bus.close()
                    continue

            if not connected:
                raise Exception(f"RTC not found at address 0x{self.rtc_address:02x}")

            self.rtc_active = True
            self.connect_btn.setText("Disconnect RTC")
            self.status_label.setText(f"Connected (bus {bus_num}, addr 0x{self.rtc_address:02x})")
            self.status_label.setStyleSheet("color: green;")

            if self.rtc_type == 'pcf85063a':
                self.chip_label.setText("Chip: NXP PCF85063A")
                self.battery_label.setText("Battery: CR1220")
                self._check_pcf85063a_status()
            else:
                self.chip_label.setText("Chip: Maxim DS3231")
                self.battery_label.setText("Battery: CR2032")

            self.update_timer.start(1000)
            logger.info(f"Connected to {self.rtc_type.upper()} RTC")

        except ImportError:
            self.status_label.setText("smbus2 not installed")
            self.status_label.setStyleSheet("color: red;")
            logger.error("smbus2 library not installed")
        except Exception as e:
            self.status_label.setText(f"Connection failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"I2C RTC connection failed: {e}")

    def _check_pcf85063a_status(self):
        """Check PCF85063A status registers"""
        if not self.i2c_bus:
            return

        try:
            ctrl1 = self.i2c_bus.read_byte_data(self.rtc_address, PCF85063A_REG_CTRL1)
            seconds = self.i2c_bus.read_byte_data(self.rtc_address, PCF85063A_REG_SECONDS)

            # Check oscillator stop flag (bit 7 of seconds)
            if seconds & 0x80:
                self.battery_label.setText("Battery: LOW (oscillator stopped)")
                self.battery_label.setStyleSheet("color: orange;")
                logger.warning("PCF85063A oscillator was stopped - battery may be low")
            else:
                self.battery_label.setText("Battery: OK")
                self.battery_label.setStyleSheet("color: green;")

        except Exception as e:
            logger.error(f"Error checking PCF85063A status: {e}")

    def disconnect_rtc(self):
        """Disconnect RTC"""
        self.rtc_active = False
        self.update_timer.stop()

        if self.i2c_bus:
            try:
                self.i2c_bus.close()
            except:
                pass
            self.i2c_bus = None

        self.connect_btn.setText("Connect RTC")
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray;")
        self.time_label.setText("--:--:--")
        self.date_label.setText("----/--/--")

        logger.info("RTC disconnected")

    def update_display(self):
        """Update time display"""
        if not self.rtc_active:
            return

        try:
            if self.rtc_type == 'system':
                self._read_system_rtc()
            elif self.rtc_type == 'pcf85063a':
                self._read_pcf85063a()
            elif self.rtc_type == 'ds3231':
                self._read_ds3231()
        except Exception as e:
            logger.error(f"RTC read error: {e}")
            self.status_label.setText(f"Read error: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: red;")

    def _read_system_rtc(self):
        """Read time from system RTC"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y-%m-%d (%A)"))

    def _read_pcf85063a(self):
        """Read time from PCF85063A RTC"""
        if not self.i2c_bus:
            return

        # Read time registers (0x04 - 0x0A)
        data = self.i2c_bus.read_i2c_block_data(self.rtc_address, PCF85063A_REG_SECONDS, 7)

        seconds = bcd_to_dec(data[0] & 0x7F)  # Mask OS bit
        minutes = bcd_to_dec(data[1] & 0x7F)
        hours = bcd_to_dec(data[2] & 0x3F)  # 24-hour format
        days = bcd_to_dec(data[3] & 0x3F)
        weekday = data[4] & 0x07
        months = bcd_to_dec(data[5] & 0x1F)
        years = bcd_to_dec(data[6]) + 2000

        weekday_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weekday_name = weekday_names[weekday] if weekday < 7 else 'Unknown'

        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.date_label.setText(f"{years}-{months:02d}-{days:02d} ({weekday_name})")

    def _read_ds3231(self):
        """Read time from DS3231 RTC"""
        if not self.i2c_bus:
            return

        # Read time registers (0x00 - 0x06)
        data = self.i2c_bus.read_i2c_block_data(self.rtc_address, DS3231_REG_SECONDS, 7)

        seconds = bcd_to_dec(data[0] & 0x7F)
        minutes = bcd_to_dec(data[1])
        hours = bcd_to_dec(data[2] & 0x3F)  # Assuming 24-hour format
        weekday = data[3]
        days = bcd_to_dec(data[4])
        months = bcd_to_dec(data[5] & 0x1F)
        years = bcd_to_dec(data[6]) + 2000

        # DS3231 uses 1-7 for weekday (1=Sunday, 7=Saturday)
        weekday_names = ['Unknown', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weekday_name = weekday_names[weekday] if 1 <= weekday <= 7 else 'Unknown'

        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.date_label.setText(f"{years}-{months:02d}-{days:02d} ({weekday_name})")

    def set_rtc_time(self):
        """Set RTC time from UI inputs"""
        if not self.rtc_active:
            QMessageBox.warning(self, "Not Connected", "Please connect to RTC first.")
            return

        time = self.time_edit.time()
        date = self.date_edit.date()

        try:
            if self.rtc_type == 'system':
                self._set_system_rtc(date, time)
            elif self.rtc_type == 'pcf85063a':
                self._set_pcf85063a(date, time)
            elif self.rtc_type == 'ds3231':
                self._set_ds3231(date, time)

            QMessageBox.information(self, "Success", "RTC time set successfully!")
            logger.info(f"RTC time set to {date.toString()} {time.toString()}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set RTC time:\n{str(e)}")
            logger.error(f"Failed to set RTC time: {e}")

    def _set_system_rtc(self, date, time):
        """Set system RTC time (safe from command injection)"""
        # Format datetime string safely - no user input reaches the shell
        datetime_str = f"{date.year()}-{date.month():02d}-{date.day():02d} {time.hour():02d}:{time.minute():02d}:{time.second():02d}"
        # Use subprocess with list args to avoid shell injection
        result = subprocess.run(
            ['sudo', 'hwclock', '--set', f'--date={datetime_str}'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise Exception(f"hwclock failed: {result.stderr}")

    def _set_pcf85063a(self, date, time):
        """Set PCF85063A RTC time"""
        if not self.i2c_bus:
            raise Exception("I2C bus not connected")

        # Calculate weekday (0 = Sunday)
        import calendar
        weekday = calendar.weekday(date.year(), date.month(), date.day())
        weekday = (weekday + 1) % 7  # Convert Monday=0 to Sunday=0

        # Prepare data
        data = [
            dec_to_bcd(time.second()),
            dec_to_bcd(time.minute()),
            dec_to_bcd(time.hour()),
            dec_to_bcd(date.day()),
            weekday,
            dec_to_bcd(date.month()),
            dec_to_bcd(date.year() - 2000)
        ]

        # Write to RTC
        self.i2c_bus.write_i2c_block_data(self.rtc_address, PCF85063A_REG_SECONDS, data)

        # Clear oscillator stop flag
        ctrl1 = self.i2c_bus.read_byte_data(self.rtc_address, PCF85063A_REG_CTRL1)
        self.i2c_bus.write_byte_data(self.rtc_address, PCF85063A_REG_CTRL1, ctrl1 & 0x7F)

    def _set_ds3231(self, date, time):
        """Set DS3231 RTC time"""
        if not self.i2c_bus:
            raise Exception("I2C bus not connected")

        import calendar
        weekday = calendar.weekday(date.year(), date.month(), date.day())
        weekday = weekday + 1  # DS3231 uses 1-7 for day of week

        data = [
            dec_to_bcd(time.second()),
            dec_to_bcd(time.minute()),
            dec_to_bcd(time.hour()),
            weekday,
            dec_to_bcd(date.day()),
            dec_to_bcd(date.month()),
            dec_to_bcd(date.year() - 2000)
        ]

        self.i2c_bus.write_i2c_block_data(self.rtc_address, DS3231_REG_SECONDS, data)

    def sync_from_system(self):
        """Sync RTC time edit fields from system time"""
        now = datetime.now()
        self.time_edit.setTime(QTime(now.hour, now.minute, now.second))
        self.date_edit.setDate(QDate(now.year, now.month, now.day))

    def sync_to_system(self):
        """Sync system time from RTC"""
        if not self.rtc_active:
            QMessageBox.warning(self, "Not Connected", "Please connect to RTC first.")
            return

        try:
            if self.rtc_type == 'system':
                QMessageBox.information(self, "Info", "Already using system RTC.")
                return

            # Read RTC time and set system clock using subprocess
            result = subprocess.run(
                ['sudo', 'hwclock', '--hctosys'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                QMessageBox.information(self, "Success", "System time synchronized from RTC!")
                logger.info("System time synchronized from RTC")
            else:
                raise Exception(result.stderr)
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Error", "Sync operation timed out")
            logger.error("Sync to system timed out")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to sync:\n{str(e)}")
            logger.error(f"Failed to sync system time from RTC: {e}")

    def is_active(self):
        """Check if RTC is active"""
        return self.rtc_active

    def get_time_string(self):
        """Get time as string"""
        return self.time_label.text()

    def get_config(self):
        """Get configuration"""
        config = self.config.copy()
        config['type'] = self.rtc_type
        return config

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config
        rtc_type = config.get('type', 'pcf85063a')
        if rtc_type == 'pcf85063a':
            self.type_combo.setCurrentIndex(0)
        elif rtc_type == 'ds3231':
            self.type_combo.setCurrentIndex(1)
        else:
            self.type_combo.setCurrentIndex(2)

    def rescan(self):
        """Rescan for RTC devices"""
        logger.info("Scanning for RTC devices...")
        # Could scan I2C buses for known RTC addresses

    def cleanup(self):
        """Cleanup resources"""
        # Stop timer first to prevent callbacks on destroyed widgets
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
        self.disconnect_rtc()
