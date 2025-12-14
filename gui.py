"""
Main GUI Window - PyQt6 Interface
Handles all visual components and user interaction
"""
import sys
from datetime import datetime
from typing import Dict, List

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGroupBox, QPushButton, QLabel, QSlider, 
                            QTextEdit, QProgressBar, QComboBox, QSpinBox,
                            QScrollArea, QGridLayout, QFrame, QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPen, QLinearGradient

from simulation import SimulationManager
from visuals import ThreadVisualizer, ResourceVisualizer


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.simulation = None
        self.thread_visualizer = None
        self.resource_visualizer = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Readers-Writers Synchronization Simulator")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Controls and statistics
        top_widget = self.create_top_section()
        
        # Middle section: Visualization
        middle_widget = self.create_visualization_section()
        
        # Bottom section: Log
        bottom_widget = self.create_log_section()
        
        splitter.addWidget(top_widget)
        splitter.addWidget(middle_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([250, 400, 250])
        
        main_layout.addWidget(splitter)
        
    def create_top_section(self):
        """Create the top control panel"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left: Control panel
        control_group = QGroupBox("Simulation Controls")
        control_layout = QVBoxLayout()
        
        # Start/Pause/Stop buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.start_simulation)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_simulation)
        
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_simulation)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.reset_btn)
        control_layout.addLayout(btn_layout)
        
        # Priority selection
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority Mode:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Reader Priority", "Writer Priority"])
        self.priority_combo.setCurrentIndex(0)
        self.priority_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        priority_layout.addWidget(self.priority_combo)
        control_layout.addLayout(priority_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Middle: Configuration sliders
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Number of readers
        readers_layout = QHBoxLayout()
        readers_layout.addWidget(QLabel("Readers:"))
        self.readers_slider = QSlider(Qt.Orientation.Horizontal)
        self.readers_slider.setRange(1, 30)
        self.readers_slider.setValue(5)
        self.readers_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.readers_slider.setTickInterval(5)
        readers_layout.addWidget(self.readers_slider)
        self.readers_label = QLabel("5")
        readers_layout.addWidget(self.readers_label)
        self.readers_slider.valueChanged.connect(
            lambda v: self.readers_label.setText(str(v)))
        config_layout.addLayout(readers_layout)
        
        # Number of writers
        writers_layout = QHBoxLayout()
        writers_layout.addWidget(QLabel("Writers:"))
        self.writers_slider = QSlider(Qt.Orientation.Horizontal)
        self.writers_slider.setRange(1, 30)
        self.writers_slider.setValue(3)
        self.writers_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.writers_slider.setTickInterval(5)
        writers_layout.addWidget(self.writers_slider)
        self.writers_label = QLabel("3")
        writers_layout.addWidget(self.writers_label)
        self.writers_slider.valueChanged.connect(
            lambda v: self.writers_label.setText(str(v)))
        config_layout.addLayout(writers_layout)
        
        # Read delay
        read_delay_layout = QHBoxLayout()
        read_delay_layout.addWidget(QLabel("Read Delay (ms):"))
        self.read_delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.read_delay_slider.setRange(100, 5000)
        self.read_delay_slider.setValue(1000)
        self.read_delay_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.read_delay_slider.setTickInterval(1000)
        read_delay_layout.addWidget(self.read_delay_slider)
        self.read_delay_label = QLabel("1000")
        read_delay_layout.addWidget(self.read_delay_label)
        self.read_delay_slider.valueChanged.connect(
            lambda v: self.read_delay_label.setText(str(v)))
        config_layout.addLayout(read_delay_layout)
        
        # Write delay
        write_delay_layout = QHBoxLayout()
        write_delay_layout.addWidget(QLabel("Write Delay (ms):"))
        self.write_delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.write_delay_slider.setRange(100, 5000)
        self.write_delay_slider.setValue(2000)
        self.write_delay_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.write_delay_slider.setTickInterval(1000)
        write_delay_layout.addWidget(self.write_delay_slider)
        self.write_delay_label = QLabel("2000")
        write_delay_layout.addWidget(self.write_delay_label)
        self.write_delay_slider.valueChanged.connect(
            lambda v: self.write_delay_label.setText(str(v)))
        config_layout.addLayout(write_delay_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Right: Statistics
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QGridLayout()
        
        stats_font = QFont()
        stats_font.setBold(True)
        stats_font.setPointSize(12)
        
        # Active readers
        stats_layout.addWidget(QLabel("Active Readers:"), 0, 0)
        self.active_readers_label = QLabel("0")
        self.active_readers_label.setFont(stats_font)
        self.active_readers_label.setStyleSheet("color: #4CAF50;")
        stats_layout.addWidget(self.active_readers_label, 0, 1)
        
        # Waiting readers
        stats_layout.addWidget(QLabel("Waiting Readers:"), 1, 0)
        self.waiting_readers_label = QLabel("0")
        self.waiting_readers_label.setFont(stats_font)
        self.waiting_readers_label.setStyleSheet("color: #FFC107;")
        stats_layout.addWidget(self.waiting_readers_label, 1, 1)
        
        # Active writers
        stats_layout.addWidget(QLabel("Active Writers:"), 2, 0)
        self.active_writers_label = QLabel("0")
        self.active_writers_label.setFont(stats_font)
        self.active_writers_label.setStyleSheet("color: #f44336;")
        stats_layout.addWidget(self.active_writers_label, 2, 1)
        
        # Waiting writers
        stats_layout.addWidget(QLabel("Waiting Writers:"), 3, 0)
        self.waiting_writers_label = QLabel("0")
        self.waiting_writers_label.setFont(stats_font)
        self.waiting_writers_label.setStyleSheet("color: #FFC107;")
        stats_layout.addWidget(self.waiting_writers_label, 3, 1)
        
        # Throughput
        stats_layout.addWidget(QLabel("Reads Completed:"), 0, 2)
        self.reads_completed_label = QLabel("0")
        stats_layout.addWidget(self.reads_completed_label, 0, 3)
        
        stats_layout.addWidget(QLabel("Writes Completed:"), 1, 2)
        self.writes_completed_label = QLabel("0")
        stats_layout.addWidget(self.writes_completed_label, 1, 3)
        
        # Conflicts
        stats_layout.addWidget(QLabel("Access Conflicts:"), 2, 2)
        self.conflicts_label = QLabel("0")
        self.conflicts_label.setStyleSheet("color: #ff5722;")
        stats_layout.addWidget(self.conflicts_label, 2, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        return widget
    
    def create_visualization_section(self):
        """Create the visualization section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Resource visualization
        resource_group = QGroupBox("Shared Resource Access")
        resource_layout = QVBoxLayout()
        
        self.resource_visualizer = ResourceVisualizer()
        resource_layout.addWidget(self.resource_visualizer)
        resource_group.setLayout(resource_layout)
        layout.addWidget(resource_group)
        
        # Thread visualization
        thread_group = QGroupBox("Thread Status Visualization")
        thread_layout = QVBoxLayout()
        
        self.thread_visualizer = ThreadVisualizer()
        thread_layout.addWidget(self.thread_visualizer)
        thread_group.setLayout(thread_layout)
        layout.addWidget(thread_group)
        
        return widget
    
    def create_log_section(self):
        """Create the log section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        log_group = QGroupBox("Event Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                font-family: monospace;
                font-size: 10pt;
            }
        """)
        
        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_text.clear)
        
        log_layout.addWidget(self.log_text)
        log_layout.addWidget(clear_btn)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return widget
    
    def start_simulation(self):
        """Start the simulation"""
        if self.simulation and self.simulation.is_running():
            return
            
        # Get configuration values
        num_readers = self.readers_slider.value()
        num_writers = self.writers_slider.value()
        read_delay = self.read_delay_slider.value() / 1000.0  # Convert to seconds
        write_delay = self.write_delay_slider.value() / 1000.0
        writer_priority = self.priority_combo.currentIndex() == 1
        
        # Create simulation manager
        self.simulation = SimulationManager(
            num_readers=num_readers,
            num_writers=num_writers,
            read_delay=read_delay,
            write_delay=write_delay,
            writer_priority=writer_priority
        )
        
        # Connect signals
        self.simulation.status_update.connect(self.update_status)
        self.simulation.log_message.connect(self.add_log_message)
        self.simulation.reader_active.connect(self.resource_visualizer.set_reader_active)
        self.simulation.writer_active.connect(self.resource_visualizer.set_writer_active)
        self.simulation.thread_update.connect(self.thread_visualizer.update_thread)
        
        # Update button states
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # Start simulation
        self.simulation.start()
        
        self.add_log_message("Simulation started", "INFO")
        
    def toggle_pause(self):
        """Toggle simulation pause state"""
        if self.simulation:
            if self.simulation.is_paused():
                self.simulation.resume()
                self.pause_btn.setText("⏸ Pause")
                self.add_log_message("Simulation resumed", "INFO")
            else:
                self.simulation.pause()
                self.pause_btn.setText("▶ Resume")
                self.add_log_message("Simulation paused", "INFO")
    
    def stop_simulation(self):
        """Stop the simulation"""
        if self.simulation:
            self.simulation.stop()
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.pause_btn.setText("⏸ Pause")
            self.add_log_message("Simulation stopped", "INFO")
    
    def reset_simulation(self):
        """Reset the simulation"""
        self.stop_simulation()
        
        # Reset visualizations
        if self.thread_visualizer:
            self.thread_visualizer.reset()
        if self.resource_visualizer:
            self.resource_visualizer.reset()
        
        # Reset labels
        self.active_readers_label.setText("0")
        self.waiting_readers_label.setText("0")
        self.active_writers_label.setText("0")
        self.waiting_writers_label.setText("0")
        self.reads_completed_label.setText("0")
        self.writes_completed_label.setText("0")
        self.conflicts_label.setText("0")
        
        self.log_text.clear()
        self.add_log_message("Simulation reset", "INFO")
    
    @pyqtSlot(dict)
    def update_status(self, stats: Dict):
        """Update status labels from simulation"""
        self.active_readers_label.setText(str(stats['active_readers']))
        self.waiting_readers_label.setText(str(stats['waiting_readers']))
        self.active_writers_label.setText(str(stats['active_writers']))
        self.waiting_writers_label.setText(str(stats['waiting_writers']))
        self.reads_completed_label.setText(str(stats['reads_completed']))
        self.writes_completed_label.setText(str(stats['writes_completed']))
        self.conflicts_label.setText(str(stats['conflicts']))
    
    @pyqtSlot(str, str)
    def add_log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Color coding based on level
        if level == "ERROR":
            color = "#f44336"
            prefix = "[ERROR]"
        elif level == "WARNING":
            color = "#ff9800"
            prefix = "[WARN]"
        elif level == "DEBUG":
            color = "#9c27b0"
            prefix = "[DEBUG]"
        else:
            color = "#4CAF50"
            prefix = "[INFO]"
        
        log_entry = f'<span style="color: #888;">[{timestamp}]</span> '\
                   f'<span style="color: {color};">{prefix}</span> {message}'
        
        self.log_text.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.simulation and self.simulation.is_running():
            self.simulation.stop()
        event.accept()