"""
RTL-SDR Panel - Software Defined Radio control
Real implementation using pyrtlsdr
Optimized for HackerGadgets uConsole AIO Extension Board (RTL2832U + R860)
"""

import logging
import threading
import numpy as np
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QSpinBox, QComboBox, QGridLayout,
                             QCheckBox, QSlider, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class RTLSDRPanel(QWidget):
    """RTL-SDR module control panel with real hardware support"""

    # Signals for thread-safe UI updates
    spectrum_updated = pyqtSignal(object)  # numpy array
    status_changed = pyqtSignal(str, str)  # text, color
    power_updated = pyqtSignal(float, float, float)  # avg_power, peak_power, peak_freq

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.sdr = None
        self.sdr_active = False
        self.capture_thread = None
        self.running = False
        self._config_enabled = config.get('enabled', False)  # Track configured state

        self.current_freq = 100000000  # 100 MHz default
        self.sample_rate = 2048000
        self.gain = 'auto'

        self.init_ui()

        # Connect signals
        self.status_changed.connect(self._on_status_changed)
        self.power_updated.connect(self._on_power_updated)

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Status group
        status_group = QGroupBox("SDR Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Not Initialized")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        self.device_label = QLabel("Device: --")
        status_layout.addWidget(self.device_label)

        self.tuner_label = QLabel("Tuner: --")
        status_layout.addWidget(self.tuner_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Configuration group
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()

        # Frequency
        config_layout.addWidget(QLabel("Frequency (MHz):"), 0, 0)
        freq_layout = QHBoxLayout()
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(24, 1766)
        self.freq_spin.setValue(100)
        self.freq_spin.setSuffix(" MHz")
        freq_layout.addWidget(self.freq_spin)

        # Quick frequency buttons
        self.freq_presets = QComboBox()
        self.freq_presets.addItems([
            'Custom', 'FM 88.1', 'FM 100.1', 'Air 118.0', 'Air 121.5',
            'Marine 156.8', 'NOAA 162.4', 'ISM 433', 'ISM 915'
        ])
        self.freq_presets.currentIndexChanged.connect(self._on_preset_changed)
        freq_layout.addWidget(self.freq_presets)
        config_layout.addLayout(freq_layout, 0, 1)

        # Connect freq_spin to reset preset to Custom when manually changed
        self.freq_spin.valueChanged.connect(self._on_freq_manually_changed)

        # Sample rate
        config_layout.addWidget(QLabel("Sample Rate:"), 1, 0)
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems([
            '250 kHz', '1.024 MHz', '1.4 MHz', '1.8 MHz',
            '2.048 MHz', '2.4 MHz', '2.56 MHz', '2.88 MHz', '3.2 MHz'
        ])
        self.sample_rate_combo.setCurrentIndex(4)  # 2.048 MHz default
        config_layout.addWidget(self.sample_rate_combo, 1, 1)

        # Gain
        config_layout.addWidget(QLabel("Gain:"), 2, 0)
        gain_layout = QHBoxLayout()
        self.gain_combo = QComboBox()
        self.gain_combo.addItems(['Auto'])
        gain_layout.addWidget(self.gain_combo)

        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 50)
        self.gain_slider.setValue(25)
        self.gain_slider.setEnabled(False)
        gain_layout.addWidget(self.gain_slider)

        self.gain_label = QLabel("Auto")
        gain_layout.addWidget(self.gain_label)
        config_layout.addLayout(gain_layout, 2, 1)

        self.gain_combo.currentTextChanged.connect(self._on_gain_changed)
        self.gain_slider.valueChanged.connect(self._on_gain_slider_changed)

        # Apply button
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.clicked.connect(self.apply_settings)
        config_layout.addWidget(self.apply_btn, 3, 0, 1, 2)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Spectrum display placeholder
        spectrum_group = QGroupBox("Spectrum Display")
        spectrum_layout = QVBoxLayout()

        self.spectrum_label = QLabel("Initialize SDR to view spectrum\n\n(Spectrum visualization requires pyqtgraph)")
        self.spectrum_label.setAlignment(Qt.AlignCenter)
        self.spectrum_label.setMinimumHeight(150)
        self.spectrum_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #4a4a4a;")
        spectrum_layout.addWidget(self.spectrum_label)

        # Spectrum controls
        spec_ctrl_layout = QHBoxLayout()
        self.waterfall_check = QCheckBox("Waterfall")
        spec_ctrl_layout.addWidget(self.waterfall_check)

        self.peak_hold_check = QCheckBox("Peak Hold")
        spec_ctrl_layout.addWidget(self.peak_hold_check)

        spec_ctrl_layout.addStretch()
        spectrum_layout.addLayout(spec_ctrl_layout)

        spectrum_group.setLayout(spectrum_layout)
        layout.addWidget(spectrum_group)

        # Info group
        info_group = QGroupBox("Signal Info")
        info_layout = QHBoxLayout()

        self.power_label = QLabel("Power: -- dBFS")
        info_layout.addWidget(self.power_label)

        self.peak_label = QLabel("Peak: -- MHz")
        info_layout.addWidget(self.peak_label)

        info_layout.addStretch()
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.init_btn = QPushButton("Initialize SDR")
        self.init_btn.clicked.connect(self.toggle_sdr)
        button_layout.addWidget(self.init_btn)

        self.start_btn = QPushButton("Start Capture")
        self.start_btn.clicked.connect(self.toggle_capture)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_preset_changed(self, index):
        """Handle frequency preset change"""
        presets = {
            1: 88.1, 2: 100.1, 3: 118.0, 4: 121.5,
            5: 156.8, 6: 162.4, 7: 433, 8: 915
        }
        if index in presets:
            # Block signals to prevent triggering _on_freq_manually_changed
            self.freq_spin.blockSignals(True)
            self.freq_spin.setValue(int(presets[index]))
            self.freq_spin.blockSignals(False)

    def _on_freq_manually_changed(self, value):
        """Handle manual frequency change - reset preset to Custom"""
        # Only change preset if not at index 0 and value doesn't match any preset
        presets = {88: 1, 100: 2, 118: 3, 121: 4, 156: 5, 162: 6, 433: 7, 915: 8}
        if value not in presets or presets.get(value) != self.freq_presets.currentIndex():
            self.freq_presets.blockSignals(True)
            self.freq_presets.setCurrentIndex(0)  # Set to "Custom"
            self.freq_presets.blockSignals(False)

    def _on_gain_changed(self, text):
        """Handle gain mode change"""
        if text == 'Auto':
            self.gain_slider.setEnabled(False)
            self.gain_label.setText("Auto")
            self.gain = 'auto'
        else:
            self.gain_slider.setEnabled(True)

    def _on_gain_slider_changed(self, value):
        """Handle gain slider change"""
        # Map to actual gain values
        self.gain_label.setText(f"{value} dB")
        self.gain = value

    def _on_status_changed(self, text, color):
        """Update status label (thread-safe)"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def _on_power_updated(self, avg_power, peak_power, peak_freq):
        """Update power labels (thread-safe)"""
        self.power_label.setText(f"Power: {avg_power:.1f} dBFS")
        self.peak_label.setText(f"Peak: {peak_freq/1e6:.3f} MHz ({peak_power:.1f} dB)")

    def initialize(self):
        """Initialize RTL-SDR"""
        if self.config.get('enabled', False):
            self.toggle_sdr()

    def toggle_sdr(self):
        """Initialize/deinitialize SDR"""
        if self.sdr_active:
            self.deinit_sdr()
        else:
            self.init_sdr()

    def init_sdr(self):
        """Initialize SDR hardware"""
        try:
            from rtlsdr import RtlSdr

            device_index = self.config.get('device_index', 0)

            self.sdr = RtlSdr(device_index)

            # Get device info
            self.device_label.setText(f"Device: RTL2832U (index {device_index})")

            # Get tuner type
            tuner_types = {1: 'E4000', 2: 'FC0012', 3: 'FC0013', 4: 'FC2580',
                         5: 'R820T', 6: 'R828D', 7: 'R860'}
            tuner_type = self.sdr.get_tuner_type()
            tuner_name = tuner_types.get(tuner_type, f'Unknown ({tuner_type})')
            self.tuner_label.setText(f"Tuner: {tuner_name}")

            # Get supported gains
            gains = self.sdr.get_gains()
            self.gain_combo.clear()
            self.gain_combo.addItem('Auto')
            for g in gains:
                self.gain_combo.addItem(f'{g/10:.1f} dB')

            # Set gain slider range based on supported gains
            if gains:
                self.gain_slider.setRange(int(gains[0]/10), int(gains[-1]/10))

            # Apply initial settings
            self._apply_sdr_settings()

            self.sdr_active = True
            self.status_label.setText("SDR Ready")
            self.status_label.setStyleSheet("color: green;")
            self.init_btn.setText("Deinitialize SDR")
            self.start_btn.setEnabled(True)

            logger.info(f"RTL-SDR initialized: {tuner_name} tuner")

        except ImportError:
            self.status_label.setText("pyrtlsdr not installed")
            self.status_label.setStyleSheet("color: red;")
            logger.error("pyrtlsdr library not installed")
            QMessageBox.critical(self, "Error",
                "pyrtlsdr library not installed.\n\n"
                "Install with: pip install pyrtlsdr")
        except Exception as e:
            self.status_label.setText(f"Init failed: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"RTL-SDR initialization failed: {e}")

    def deinit_sdr(self):
        """Deinitialize SDR"""
        self.stop_capture()

        if self.sdr:
            try:
                self.sdr.close()
            except:
                pass
            self.sdr = None

        self.sdr_active = False
        self.status_label.setText("Not Initialized")
        self.status_label.setStyleSheet("color: gray;")
        self.init_btn.setText("Initialize SDR")
        self.start_btn.setEnabled(False)
        self.device_label.setText("Device: --")
        self.tuner_label.setText("Tuner: --")

        logger.info("RTL-SDR deinitialized")

    def _apply_sdr_settings(self):
        """Apply current settings to SDR"""
        if not self.sdr:
            return

        # Set frequency
        freq_mhz = self.freq_spin.value()
        self.current_freq = freq_mhz * 1000000
        self.sdr.center_freq = self.current_freq

        # Set sample rate
        sample_rate_text = self.sample_rate_combo.currentText()
        if 'kHz' in sample_rate_text:
            self.sample_rate = int(float(sample_rate_text.replace(' kHz', '')) * 1000)
        else:
            self.sample_rate = int(float(sample_rate_text.replace(' MHz', '')) * 1000000)
        self.sdr.sample_rate = self.sample_rate

        # Set gain
        if self.gain == 'auto':
            self.sdr.gain = 'auto'
        else:
            self.sdr.gain = self.gain

        logger.info(f"SDR settings: {freq_mhz} MHz, {self.sample_rate/1e6:.3f} MSPS, gain={self.gain}")

    def apply_settings(self):
        """Apply settings button handler"""
        if self.sdr_active:
            self._apply_sdr_settings()
            self.status_label.setText(f"Tuned to {self.freq_spin.value()} MHz")
            self.status_label.setStyleSheet("color: green;")

    def toggle_capture(self):
        """Start/stop capture"""
        if self.running:
            self.stop_capture()
        else:
            self.start_capture()

    def start_capture(self):
        """Start SDR capture"""
        if not self.sdr:
            return

        self.running = True
        self.start_btn.setText("Stop Capture")

        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

        self.status_label.setText("Capturing...")
        self.status_label.setStyleSheet("color: #00ff00;")

        logger.info("SDR capture started")

    def stop_capture(self):
        """Stop SDR capture"""
        self.running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            self.capture_thread = None

        if self.sdr_active:
            self.status_label.setText("SDR Ready")
            self.status_label.setStyleSheet("color: green;")

        self.start_btn.setText("Start Capture")

        logger.info("SDR capture stopped")

    def _capture_loop(self):
        """Background capture loop"""
        samples_per_read = 256 * 1024  # 256k samples

        while self.running and self.sdr:
            try:
                # Read samples
                samples = self.sdr.read_samples(samples_per_read)

                # Calculate power spectrum
                fft_size = 1024
                spectrum = np.fft.fft(samples[:fft_size])
                spectrum = np.fft.fftshift(spectrum)
                power_db = 20 * np.log10(np.abs(spectrum) + 1e-10)

                # Calculate signal metrics
                avg_power = np.mean(power_db)
                peak_power = np.max(power_db)
                peak_idx = np.argmax(power_db)
                peak_freq = self.current_freq + (peak_idx - fft_size/2) * self.sample_rate / fft_size

                # Emit for UI update
                self.spectrum_updated.emit(power_db)
                self.power_updated.emit(float(avg_power), float(peak_power), float(peak_freq))

            except Exception as e:
                if self.running:
                    logger.error(f"Capture error: {e}")
                    self.status_changed.emit(f"Error: {str(e)[:20]}", "red")
                break

    def is_active(self):
        """Check if SDR is active"""
        return self.sdr_active

    def get_frequency(self):
        """Get current frequency"""
        return self.current_freq

    def get_config(self):
        """Get configuration (returns configured state, not runtime state)"""
        # Parse sample rate
        sample_rate_text = self.sample_rate_combo.currentText()
        if 'kHz' in sample_rate_text:
            sample_rate = int(float(sample_rate_text.replace(' kHz', '')) * 1000)
        else:
            sample_rate = int(float(sample_rate_text.replace(' MHz', '')) * 1000000)

        return {
            'enabled': self._config_enabled,  # Return configured state, not runtime
            'device_index': self.config.get('device_index', 0),
            'frequency': self.freq_spin.value() * 1000000,
            'sample_rate': sample_rate,
            'gain': self.gain,
        }

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config
        self._config_enabled = config.get('enabled', False)  # Track configured state

        if 'frequency' in config:
            self.freq_spin.setValue(config['frequency'] // 1000000)

        if 'sample_rate' in config:
            sr = config['sample_rate']
            if sr < 1000000:
                sr_text = f'{sr/1000:.0f} kHz'
            else:
                sr_text = f'{sr/1000000:.3f} MHz'
            idx = self.sample_rate_combo.findText(sr_text)
            if idx >= 0:
                self.sample_rate_combo.setCurrentIndex(idx)

    def rescan(self):
        """Rescan for SDR devices"""
        try:
            from rtlsdr import RtlSdr
            count = RtlSdr.get_device_count()
            logger.info(f"Found {count} RTL-SDR device(s)")

            for i in range(count):
                name = RtlSdr.get_device_name(i)
                serial = RtlSdr.get_device_serial_addresses()
                logger.info(f"  Device {i}: {name}")

        except ImportError:
            logger.error("pyrtlsdr not installed")
        except Exception as e:
            logger.error(f"SDR scan error: {e}")

    def cleanup(self):
        """Cleanup resources"""
        self.deinit_sdr()
