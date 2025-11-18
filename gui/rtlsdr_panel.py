"""
RTL-SDR Panel - Software Defined Radio control
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QSpinBox, QComboBox, QGridLayout,
                             QCheckBox)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont


class RTLSDRPanel(QWidget):
    """RTL-SDR module control panel"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.sdr_active = False

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Status
        status_group = QGroupBox("SDR Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Not Initialized")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()

        config_layout.addWidget(QLabel("Frequency (MHz):"), 0, 0)
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(24, 1766)
        self.freq_spin.setValue(100)
        self.freq_spin.setSuffix(" MHz")
        config_layout.addWidget(self.freq_spin, 0, 1)

        config_layout.addWidget(QLabel("Sample Rate:"), 1, 0)
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(['250 kHz', '1.024 MHz', '2.048 MHz', '2.4 MHz'])
        self.sample_rate_combo.setCurrentIndex(2)
        config_layout.addWidget(self.sample_rate_combo, 1, 1)

        config_layout.addWidget(QLabel("Gain:"), 2, 0)
        self.gain_combo = QComboBox()
        self.gain_combo.addItems(['Auto', '0', '10', '20', '30', '40'])
        config_layout.addWidget(self.gain_combo, 2, 1)

        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.clicked.connect(self.apply_settings)
        config_layout.addWidget(self.apply_btn, 3, 0, 1, 2)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Spectrum placeholder
        spectrum_group = QGroupBox("Spectrum Display")
        spectrum_layout = QVBoxLayout()
        spectrum_layout.addWidget(QLabel("Spectrum visualization would go here\n(Requires pyqtgraph integration)"))
        spectrum_group.setLayout(spectrum_layout)
        layout.addWidget(spectrum_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.init_btn = QPushButton("Initialize SDR")
        self.init_btn.clicked.connect(self.toggle_sdr)
        button_layout.addWidget(self.init_btn)

        self.start_btn = QPushButton("Start Capture")
        self.start_btn.clicked.connect(self.start_capture)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)

        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

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
        """Initialize SDR"""
        try:
            # Initialize RTL-SDR hardware here
            self.sdr_active = True
            self.status_label.setText("SDR Ready")
            self.status_label.setStyleSheet("color: green;")
            self.init_btn.setText("Deinitialize SDR")
            self.start_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Init failed: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def deinit_sdr(self):
        """Deinitialize SDR"""
        self.sdr_active = False
        self.status_label.setText("Not Initialized")
        self.status_label.setStyleSheet("color: gray;")
        self.init_btn.setText("Initialize SDR")
        self.start_btn.setEnabled(False)

    def apply_settings(self):
        """Apply SDR settings"""
        freq = self.freq_spin.value() * 1000000
        # Apply to SDR hardware
        print(f"Setting frequency: {freq} Hz")

    def start_capture(self):
        """Start SDR capture"""
        print("Starting SDR capture")

    def get_config(self):
        """Get configuration"""
        return {
            'enabled': self.sdr_active,
            'frequency': self.freq_spin.value() * 1000000,
        }

    def apply_config(self, config):
        """Apply configuration"""
        self.config = config

    def cleanup(self):
        """Cleanup resources"""
        self.deinit_sdr()
