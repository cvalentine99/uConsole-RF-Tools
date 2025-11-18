# Hardware Control Center

A comprehensive graphical user interface for managing multiple hardware modules in embedded Linux systems.

## Features

### Integrated Hardware Support
- **GPS Module** - Real-time position tracking, satellite display, NMEA logging
- **LoRa Radio** - Message transmission/reception, signal monitoring
- **RTL-SDR** - Software Defined Radio control and spectrum display
- **RTC** - Real-time clock with alarm and temperature monitoring
- **USB Hub** - Device enumeration and power management

### Key Capabilities
- **Real-time Data Display** - Live updates from all modules
- **Configuration Management** - JSON-based configuration files
- **Event Logging** - Track all hardware events
- **Dark Theme** - Professional UI optimized for long-term use
- **Multi-Tab Interface** - Easy navigation between modules

## Screenshots

![Hardware Control Center](resources/screenshot.png)

## Installation

### Prerequisites

```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-pyqt5 \
    libusb-1.0-0 \
    i2c-tools \
    libi2c-dev

# Add user to required groups
sudo usermod -a -G dialout,i2c,spi,plugdev $USER
# Logout and login for group changes to take effect
```

### Python Dependencies

```bash
# Install Python packages
pip3 install -r requirements.txt

# Or install individually:
pip3 install PyQt5 pyserial pynmea2 pyusb pyudev pyqtgraph numpy spidev smbus2
```

## Usage

### Basic Usage

```bash
# Run with default configuration
python3 main.py

# Run with custom configuration
python3 main.py --config my_config.json

# Run in fullscreen mode
python3 main.py --fullscreen
```

### Configuration

Create a configuration file (e.g., `configs/my_config.json`):

```json
{
  "gps": {
    "enabled": true,
    "device": "/dev/ttyUSB0",
    "baud_rate": 9600
  },
  "lora": {
    "enabled": true,
    "spi_device": "/dev/spidev0.0",
    "frequency": 915000000,
    "spreading_factor": 7,
    "bandwidth": 125000,
    "tx_power": 17
  },
  "rtlsdr": {
    "enabled": false,
    "device_index": 0,
    "sample_rate": 2048000,
    "frequency": 100000000
  },
  "rtc": {
    "enabled": true,
    "type": "ds3231",
    "i2c_device": "/dev/i2c-1"
  },
  "usb": {
    "enabled": true
  }
}
```

### Module Operation

#### GPS Tab
1. Click **Connect** to connect to GPS module
2. Wait for GPS fix (status will turn green)
3. View real-time position, satellites, and speed
4. Click **Start Logging** to save NMEA data to file
5. Logged data saved in standard NMEA format

#### LoRa Tab
1. Click **Initialize LoRa** to start LoRa radio
2. Configure frequency, spreading factor, and power
3. Click **Apply Configuration** to update settings
4. Type message and click **Send Message** to transmit
5. Click **Start Listening** to receive messages
6. Received messages appear in log with RSSI/SNR

#### RTL-SDR Tab
1. Click **Initialize SDR** to start RTL-SDR
2. Set desired frequency and sample rate
3. Click **Apply Settings** to update
4. Click **Start Capture** to begin reception
5. Spectrum display shows real-time waterfall (if pyqtgraph installed)

#### RTC Tab
1. Click **Connect RTC** to initialize real-time clock
2. View current date and time
3. View temperature (DS3231 only)
4. Set time manually or sync from system
5. Configure alarms (future enhancement)

#### USB Tab
1. View all connected USB devices
2. See vendor/product IDs and descriptions
3. Click **Refresh** to rescan devices
4. Device power management (future enhancement)

## Keyboard Shortcuts

- **F5** - Rescan devices
- **F11** - Toggle fullscreen
- **Ctrl+Q** - Quit application

## Menu Options

### File Menu
- **Open Configuration** - Load configuration from file
- **Save Configuration** - Save current settings
- **Exit** - Close application

### View Menu
- **Fullscreen** - Toggle fullscreen mode

### Tools Menu
- **Settings** - Open configuration dialog
- **Rescan Devices** - Refresh all hardware connections

### Help Menu
- **About** - Application information
- **Documentation** - Quick help guide

## Troubleshooting

### GPS Not Connecting

```bash
# Check device exists
ls -l /dev/ttyUSB*

# Check permissions
sudo usermod -a -G dialout $USER
# Logout and login

# Test with screen
screen /dev/ttyUSB0 9600
```

### LoRa Not Working

```bash
# Check SPI is enabled
ls -l /dev/spidev*

# Enable SPI (Raspberry Pi)
sudo raspi-config
# Interface Options > SPI > Enable
```

### RTC Not Responding

```bash
# Check I2C devices
i2cdetect -y 1

# Should show 0x68 for DS3231
# Enable I2C if not visible
sudo raspi-config
# Interface Options > I2C > Enable
```

### USB Devices Not Showing

```bash
# Install pyusb
pip3 install pyusb

# Check USB devices from command line
lsusb

# Fix permissions
sudo usermod -a -G plugdev $USER
```

### Permission Denied Errors

All hardware access requires appropriate permissions:

```bash
# Add to all required groups
sudo usermod -a -G dialout,i2c,spi,plugdev,gpio $USER

# Logout and login for changes to take effect

# Or run with sudo (not recommended for regular use)
sudo python3 main.py
```

## Development

### Project Structure

```
hardware-control-center/
├── main.py                    # Main application entry point
├── gui/                       # GUI modules
│   ├── __init__.py
│   ├── gps_panel.py          # GPS control panel
│   ├── lora_panel.py         # LoRa control panel
│   ├── rtc_panel.py          # RTC control panel
│   ├── rtlsdr_panel.py       # RTL-SDR control panel
│   ├── usb_panel.py          # USB management panel
│   └── config_dialog.py      # Configuration dialog
├── modules/                   # Hardware interface modules
├── utils/                     # Utility functions
├── resources/                 # Icons and images
├── configs/                   # Configuration files
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Adding New Features

To add a new module panel:

1. Create new panel file in `gui/` directory
2. Inherit from `QWidget`
3. Implement `initialize()`, `get_config()`, `apply_config()`, `cleanup()` methods
4. Add to main.py tab widget

Example:

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyPanel(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("My Panel"))
        self.setLayout(layout)

    def initialize(self):
        # Initialize hardware
        pass

    def get_config(self):
        return self.config

    def apply_config(self, config):
        self.config = config

    def cleanup(self):
        # Cleanup resources
        pass
```

## Hardware Requirements

### Minimum
- **CPU**: ARM Cortex-A7 or better (Raspberry Pi 3+)
- **RAM**: 1GB
- **OS**: Linux with Python 3.7+
- **Display**: 800x600 minimum

### Recommended
- **CPU**: ARM Cortex-A72 or better (Raspberry Pi 4)
- **RAM**: 2GB+
- **OS**: Raspberry Pi OS (Debian-based)
- **Display**: 1024x768 or higher

### Supported Hardware
- **GPS**: Any NMEA-compatible GPS (USB or UART)
- **LoRa**: SX1276/SX1278-based modules (SPI)
- **RTL-SDR**: RTL2832U-based SDR dongles
- **RTC**: DS3231, DS1307, PCF8523, RV3028 (I2C)
- **USB**: Built-in USB host

## License

MIT License - Free to use for commercial and personal projects.

## Related Projects

- [RTL-SDR API Examples](../rtl-sdr-api-examples/)
- [LoRa API Examples](../lora-api-examples/)
- [GPS API Examples](../gps-api-examples/)
- [RTC API Examples](../rtc-api-examples/)
- [USB Hub API Examples](../usb-hub-api-examples/)
- [Unified API Examples](../unified-api-examples/)

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Review module-specific documentation
3. Check system logs: `dmesg | tail`
4. Verify hardware connections

## Credits

Built with:
- **PyQt5** - GUI framework
- **pyserial** - Serial communication
- **pyusb** - USB device access
- **pynmea2** - GPS NMEA parsing

## Version History

### 1.0.0 (2025-11-18)
- Initial release
- Support for GPS, LoRa, RTL-SDR, RTC, USB modules
- JSON configuration
- Dark theme UI
- Real-time data display
