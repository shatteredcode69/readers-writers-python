"""
Visualization components for the simulation
Custom Qt widgets for animated visualization of threads and resource access
"""
from typing import Dict, List, Optional
import math

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
                        QPainterPath, QFontMetrics, QRadialGradient)


class ThreadWidget(QWidget):
    """
    Widget representing a single thread (reader or writer).
    
    Shows thread status with color coding and animation.
    """
    
    # Colors for different states
    COLORS = {
        'reader': {
            'idle': QColor(100, 150, 255),      # Blue
            'waiting': QColor(255, 193, 7),     # Yellow
            'active': QColor(76, 175, 80),      # Green
            'completed': QColor(156, 39, 176),  # Purple
            'border': QColor(30, 80, 180)       # Dark blue
        },
        'writer': {
            'idle': QColor(255, 100, 100),      # Red
            'waiting': QColor(255, 193, 7),     # Yellow
            'active': QColor(244, 67, 54),      # Red
            'completed': QColor(156, 39, 176),  # Purple
            'border': QColor(180, 30, 30)       # Dark red
        }
    }
    
    def __init__(self, thread_id: int, thread_type: str, parent=None):
        """Initialize thread widget."""
        super().__init__(parent)
        
        self.thread_id = thread_id
        self.thread_type = thread_type  # 'reader' or 'writer'
        self.status = 'idle'
        self.action = ''
        self.progress = 0
        self.pulse_value = 0
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_pulse)
        self.animation_timer.start(50)  # 20 FPS
        
        # Size
        self.setMinimumSize(80, 100)
        self.setMaximumSize(120, 140)
        
        # Font
        self.font = QFont()
        self.font.setBold(True)
        
    def update_status(self, status: str, action: str = ''):
        """Update thread status and action."""
        self.status = status
        self.action = action
        self.update()
        
    def set_progress(self, progress: float):
        """Set operation progress (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))
        self.update()
        
    def update_pulse(self):
        """Update pulse animation for waiting/active threads."""
        if self.status in ['waiting', 'active']:
            self.pulse_value = (self.pulse_value + 0.1) % (2 * math.pi)
            self.update()
        
    def paintEvent(self, event):
        """Paint the thread widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Get colors based on thread type and status
        colors = self.COLORS[self.thread_type]
        base_color = colors.get(self.status, colors['idle'])
        border_color = colors['border']
        
        # Draw thread representation based on status
        if self.status == 'waiting':
            self.draw_waiting_thread(painter, width, height, base_color, border_color)
        elif self.status == 'active':
            self.draw_active_thread(painter, width, height, base_color, border_color)
        elif self.status == 'completed':
            self.draw_completed_thread(painter, width, height, base_color, border_color)
        else:
            self.draw_idle_thread(painter, width, height, base_color, border_color)
        
        # Draw thread info
        self.draw_thread_info(painter, width, height)
        
        # Draw progress bar for active operations
        if self.status == 'active' and self.progress > 0:
            self.draw_progress_bar(painter, width, height)
        
        painter.end()
        
    def draw_idle_thread(self, painter: QPainter, width: int, height: int, 
                        color: QColor, border_color: QColor):
        """Draw idle thread representation."""
        # Draw circular thread icon
        center_x = width // 2
        center_y = height // 2 - 10
        radius = min(width, height) // 3 - 5
        
        # Create gradient
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(1, color.darker(150))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 2))
        painter.drawEllipse(center_x - radius, center_y - radius, 
                           radius * 2, radius * 2)
        
        # Draw thread symbol inside
        symbol = "R" if self.thread_type == 'reader' else "W"
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self.font)
        painter.drawText(center_x - 5, center_y + 5, symbol)
        
    def draw_waiting_thread(self, painter: QPainter, width: int, height: int,
                           color: QColor, border_color: QColor):
        """Draw waiting thread with pulsing animation."""
        center_x = width // 2
        center_y = height // 2 - 10
        base_radius = min(width, height) // 3 - 5
        
        # Calculate pulse radius
        pulse = abs(math.sin(self.pulse_value)) * 5
        radius = base_radius + pulse
        
        # Create pulsing gradient
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, color.lighter(200))
        gradient.setColorAt(0.7, color)
        gradient.setColorAt(1, color.darker(150))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 2))
        painter.drawEllipse(center_x - radius, center_y - radius,
                           radius * 2, radius * 2)
        
        # Draw waiting symbol (hourglass)
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        hourglass_size = radius * 0.6
        self.draw_hourglass(painter, center_x, center_y, hourglass_size)
        
    def draw_active_thread(self, painter: QPainter, width: int, height: int,
                          color: QColor, border_color: QColor):
        """Draw active thread with animation."""
        center_x = width // 2
        center_y = height // 2 - 10
        base_radius = min(width, height) // 3 - 5
        
        # Calculate animation
        pulse = abs(math.sin(self.pulse_value * 2)) * 3
        radius = base_radius + pulse
        
        # Create active gradient
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, QColor(255, 255, 255))
        gradient.setColorAt(0.3, color.lighter(150))
        gradient.setColorAt(1, color.darker(100))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 3))
        painter.drawEllipse(center_x - radius, center_y - radius,
                           radius * 2, radius * 2)
        
        # Draw active symbol (gear)
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        gear_size = radius * 0.7
        self.draw_gear(painter, center_x, center_y, gear_size)
        
    def draw_completed_thread(self, painter: QPainter, width: int, height: int,
                             color: QColor, border_color: QColor):
        """Draw completed thread."""
        center_x = width // 2
        center_y = height // 2 - 10
        radius = min(width, height) // 3 - 5
        
        # Create completed gradient
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(1, color.darker(100))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 2))
        painter.drawEllipse(center_x - radius, center_y - radius,
                           radius * 2, radius * 2)
        
        # Draw checkmark
        painter.setPen(QPen(Qt.GlobalColor.white, 3))
        check_size = radius * 0.7
        self.draw_checkmark(painter, center_x, center_y, check_size)
        
    def draw_thread_info(self, painter: QPainter, width: int, height: int):
        """Draw thread ID and status text."""
        # Draw thread ID
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(self.font)
        id_text = f"{self.thread_type[0].upper()}{self.thread_id}"
        painter.drawText(0, height - 30, width, 20,
                        Qt.AlignmentFlag.AlignCenter, id_text)
        
        # Draw status
        status_font = QFont()
        status_font.setPointSize(8)
        painter.setFont(status_font)
        
        status_text = self.status.capitalize()
        if self.action:
            status_text = f"{status_text}\n{self.action}"
            
        painter.drawText(0, height - 10, width, 20,
                        Qt.AlignmentFlag.AlignCenter, status_text)
        
    def draw_progress_bar(self, painter: QPainter, width: int, height: int):
        """Draw progress bar at bottom of widget."""
        bar_height = 6
        bar_width = width - 20
        bar_x = 10
        bar_y = height - 40
        
        # Draw background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(200, 200, 200, 150)))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 3, 3)
        
        # Draw progress
        progress_width = int(bar_width * self.progress)
        if progress_width > 0:
            gradient = QLinearGradient(bar_x, bar_y, bar_x + progress_width, bar_y)
            gradient.setColorAt(0, QColor(76, 175, 80))
            gradient.setColorAt(1, QColor(56, 142, 60))
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 3, 3)
            
    def draw_hourglass(self, painter: QPainter, x: int, y: int, size: float):
        """Draw hourglass symbol for waiting state."""
        half_size = size / 2
        
        # Draw top triangle
        top_path = QPainterPath()
        top_path.moveTo(x, y - half_size)
        top_path.lineTo(x - half_size * 0.7, y)
        top_path.lineTo(x + half_size * 0.7, y)
        top_path.closeSubpath()
        painter.drawPath(top_path)
        
        # Draw bottom triangle
        bottom_path = QPainterPath()
        bottom_path.moveTo(x, y + half_size)
        bottom_path.lineTo(x - half_size * 0.7, y)
        bottom_path.lineTo(x + half_size * 0.7, y)
        bottom_path.closeSubpath()
        painter.drawPath(bottom_path)
        
    def draw_gear(self, painter: QPainter, x: int, y: int, size: float):
        """Draw gear symbol for active state."""
        teeth = 8
        inner_radius = size * 0.4
        outer_radius = size * 0.6
        
        path = QPainterPath()
        
        for i in range(teeth):
            angle = 2 * math.pi * i / teeth
            next_angle = 2 * math.pi * (i + 0.5) / teeth
            
            # Outer point
            ox = x + outer_radius * math.cos(angle)
            oy = y + outer_radius * math.sin(angle)
            
            # Inner point
            ix = x + inner_radius * math.cos(next_angle)
            iy = y + inner_radius * math.sin(next_angle)
            
            if i == 0:
                path.moveTo(ox, oy)
            else:
                path.lineTo(ox, oy)
                
            path.lineTo(ix, iy)
            
        path.closeSubpath()
        painter.drawPath(path)
        
    def draw_checkmark(self, painter: QPainter, x: int, y: int, size: float):
        """Draw checkmark symbol for completed state."""
        path = QPainterPath()
        
        # Draw checkmark
        offset = size * 0.2
        path.moveTo(x - size / 2 + offset, y)
        path.lineTo(x - offset, y + size / 2 - offset)
        path.lineTo(x + size / 2 - offset, y - size / 2 + offset)
        
        painter.drawPath(path)


class ThreadVisualizer(QWidget):
    """
    Visualizer for all threads in the simulation.
    
    Shows readers and writers in separate sections with their current status.
    """
    
    def __init__(self, parent=None):
        """Initialize thread visualizer."""
        super().__init__(parent)
        
        # Thread widgets storage
        self.reader_widgets: Dict[int, ThreadWidget] = {}
        self.writer_widgets: Dict[int, ThreadWidget] = {}
        
        # Layouts
        self.main_layout = QVBoxLayout(self)
        
        # Create sections
        self.create_reader_section()
        self.create_writer_section()
        
        # Timer for progress updates
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)  # Update progress 10 times per second
        
        # Progress values for active threads
        self.active_progress: Dict[tuple, float] = {}  # (type, id) -> progress
        
    def create_reader_section(self):
        """Create reader threads section."""
        reader_group = QGroupBox("Reader Threads")
        reader_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4CAF50;
            }
        """)
        
        self.reader_layout = QHBoxLayout()
        self.reader_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        reader_group.setLayout(self.reader_layout)
        self.main_layout.addWidget(reader_group)
        
    def create_writer_section(self):
        """Create writer threads section."""
        writer_group = QGroupBox("Writer Threads")
        writer_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f44336;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #f44336;
            }
        """)
        
        self.writer_layout = QHBoxLayout()
        self.writer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        writer_group.setLayout(self.writer_layout)
        self.main_layout.addWidget(writer_group)
        
    def update_thread(self, thread_data: Dict):
        """Update thread status based on simulation data."""
        thread_type = thread_data['thread_type']
        thread_id = thread_data['thread_id']
        status = thread_data['status']
        action = thread_data['action']
        
        if thread_type == 'reader':
            self.update_reader_thread(thread_id, status, action)
        else:
            self.update_writer_thread(thread_id, status, action)
            
    def update_reader_thread(self, thread_id: int, status: str, action: str):
        """Update specific reader thread."""
        if thread_id not in self.reader_widgets:
            # Create new reader widget
            widget = ThreadWidget(thread_id, 'reader')
            self.reader_widgets[thread_id] = widget
            self.reader_layout.addWidget(widget)
        
        widget = self.reader_widgets[thread_id]
        widget.update_status(status, action)
        
        # Update progress tracking
        key = ('reader', thread_id)
        if status == 'active':
            if action == 'read':
                # Start progress for read operation
                if key not in self.active_progress:
                    self.active_progress[key] = 0.0
        else:
            # Remove from active progress if not active
            if key in self.active_progress:
                del self.active_progress[key]
                
    def update_writer_thread(self, thread_id: int, status: str, action: str):
        """Update specific writer thread."""
        if thread_id not in self.writer_widgets:
            # Create new writer widget
            widget = ThreadWidget(thread_id, 'writer')
            self.writer_widgets[thread_id] = widget
            self.writer_layout.addWidget(widget)
        
        widget = self.writer_widgets[thread_id]
        widget.update_status(status, action)
        
        # Update progress tracking
        key = ('writer', thread_id)
        if status == 'active':
            if action == 'write':
                # Start progress for write operation
                if key not in self.active_progress:
                    self.active_progress[key] = 0.0
        else:
            # Remove from active progress if not active
            if key in self.active_progress:
                del self.active_progress[key]
                
    def update_progress(self):
        """Update progress for active threads."""
        # Increment progress for all active threads
        for key in list(self.active_progress.keys()):
            thread_type, thread_id = key
            
            # Different increment rates for read vs write
            increment = 0.02 if thread_type == 'reader' else 0.01
            
            self.active_progress[key] += increment
            
            # Cap at 1.0
            if self.active_progress[key] >= 1.0:
                del self.active_progress[key]
                continue
                
            # Update widget
            if thread_type == 'reader':
                if thread_id in self.reader_widgets:
                    self.reader_widgets[thread_id].set_progress(
                        self.active_progress[key]
                    )
            else:
                if thread_id in self.writer_widgets:
                    self.writer_widgets[thread_id].set_progress(
                        self.active_progress[key]
                    )
                    
    def reset(self):
        """Reset the visualizer."""
        # Clear all widgets
        for widget in list(self.reader_widgets.values()):
            self.reader_layout.removeWidget(widget)
            widget.deleteLater()
        self.reader_widgets.clear()
        
        for widget in list(self.writer_widgets.values()):
            self.writer_layout.removeWidget(widget)
            widget.deleteLater()
        self.writer_widgets.clear()
        
        self.active_progress.clear()


class ResourceVisualizer(QWidget):
    """
    Visualizer for the shared resource (database).
    
    Shows current access state and animation of readers/writers entering/exiting.
    """
    
    def __init__(self, parent=None):
        """Initialize resource visualizer."""
        super().__init__(parent)
        
        # Resource state
        self.reader_active = False
        self.writer_active = False
        self.active_count = 0
        
        # Animation values
        self.pulse_value = 0
        self.access_animation = 0
        self.rotation_angle = 0
        
        # Colors
        self.idle_color = QColor(200, 200, 200)
        self.reader_color = QColor(76, 175, 80)     # Green
        self.writer_color = QColor(244, 67, 54)     # Red
        self.conflict_color = QColor(255, 193, 7)   # Yellow
        
        # Timer for animations
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(30)  # ~33 FPS
        
        # Access history
        self.access_history = []
        
        # Set size
        self.setMinimumHeight(150)
        
    def set_reader_active(self, active: bool):
        """Set reader active state."""
        self.reader_active = active
        if active:
            self.active_count += 1
            self.access_animation = 1.0
            self.access_history.append(('reader', self.active_count))
        self.update()
        
    def set_writer_active(self, active: bool):
        """Set writer active state."""
        self.writer_active = active
        if active:
            self.active_count += 1
            self.access_animation = 1.0
            self.access_history.append(('writer', self.active_count))
        self.update()
        
    def update_animation(self):
        """Update animation values."""
        # Update pulse for active state
        if self.reader_active or self.writer_active:
            self.pulse_value = (self.pulse_value + 0.1) % (2 * math.pi)
            
        # Update access animation
        if self.access_animation > 0:
            self.access_animation -= 0.05
            
        # Update rotation for visual interest
        self.rotation_angle = (self.rotation_angle + 1) % 360
            
        self.update()
        
    def paintEvent(self, event):
        """Paint the resource visualizer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        self.draw_background(painter, width, height)
        
        # Draw resource representation
        self.draw_resource(painter, width, height)
        
        # Draw status text
        self.draw_status(painter, width, height)
        
        # Draw access animation
        if self.access_animation > 0:
            self.draw_access_animation(painter, width, height)
            
        painter.end()
        
    def draw_background(self, painter: QPainter, width: int, height: int):
        """Draw the background with gradient."""
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(240, 240, 240))
        gradient.setColorAt(1, QColor(220, 220, 220))
        
        painter.fillRect(0, 0, width, height, QBrush(gradient))
        
        # Draw border
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawRect(1, 1, width - 2, height - 2)
        
    def draw_resource(self, painter: QPainter, width: int, height: int):
        """Draw the resource (database) representation."""
        center_x = width // 2
        center_y = height // 2
        size = min(width, height) * 0.6
        
        # Determine current color based on access
        if self.writer_active:
            base_color = self.writer_color
            status = "Writing"
        elif self.reader_active:
            base_color = self.reader_color
            status = "Reading"
        else:
            base_color = self.idle_color
            status = "Idle"
            
        # Add pulse effect if active
        if self.reader_active or self.writer_active:
            pulse = abs(math.sin(self.pulse_value)) * 20
            size += pulse
            
            # Create animated gradient
            gradient = QRadialGradient(center_x, center_y, size / 2)
            if self.writer_active:
                gradient.setColorAt(0, self.writer_color.lighter(200))
                gradient.setColorAt(0.7, self.writer_color)
                gradient.setColorAt(1, self.writer_color.darker(150))
            else:
                gradient.setColorAt(0, self.reader_color.lighter(200))
                gradient.setColorAt(0.7, self.reader_color)
                gradient.setColorAt(1, self.reader_color.darker(150))
                
            brush = QBrush(gradient)
        else:
            # Static gradient for idle
            gradient = QRadialGradient(center_x, center_y, size / 2)
            gradient.setColorAt(0, base_color.lighter(150))
            gradient.setColorAt(1, base_color.darker(100))
            brush = QBrush(gradient)
            
        # Draw main resource circle
        painter.setBrush(brush)
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        painter.drawEllipse(center_x - size / 2, center_y - size / 2, size, size)
        
        # Draw database symbol
        self.draw_database_symbol(painter, center_x, center_y, size * 0.6)
        
        # Draw concurrent readers indicator
        if self.reader_active and self.active_count > 1:
            self.draw_concurrent_indicator(painter, center_x, center_y, size)
            
    def draw_database_symbol(self, painter: QPainter, x: int, y: int, size: float):
        """Draw database symbol (cylinder with lines)."""
        cylinder_height = size * 0.8
        cylinder_width = size * 0.6
        
        # Save painter state
        painter.save()
        
        # Draw cylinder body
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        
        # Draw oval top
        painter.drawEllipse(int(x - cylinder_width / 2), 
                          int(y - cylinder_height / 2), 
                          int(cylinder_width), int(cylinder_height / 3))
        
        # Draw sides
        left_x = x - cylinder_width / 2
        right_x = x + cylinder_width / 2
        top_y = y - cylinder_height / 2 + cylinder_height / 6
        bottom_y = y + cylinder_height / 2
        
        painter.drawLine(int(left_x), int(top_y), int(left_x), int(bottom_y))
        painter.drawLine(int(right_x), int(top_y), int(right_x), int(bottom_y))
        
        # Draw bottom oval
        painter.drawEllipse(int(x - cylinder_width / 2), 
                          int(bottom_y - cylinder_height / 6), 
                          int(cylinder_width), int(cylinder_height / 3))
        
        # Draw data lines inside
        painter.setPen(QPen(QColor(70, 130, 180), 1))
        line_spacing = cylinder_height / 6
        for i in range(1, 4):
            line_y = top_y + i * line_spacing
            painter.drawLine(int(left_x + 5), int(line_y), 
                           int(right_x - 5), int(line_y))
            
        # Restore painter
        painter.restore()
        
    def draw_concurrent_indicator(self, painter: QPainter, x: int, y: int, size: float):
        """Draw indicator for concurrent readers."""
        indicator_radius = size * 0.15
        angle_step = 2 * math.pi / self.active_count
        
        painter.save()
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(QPen(QColor(76, 175, 80), 2))
        
        for i in range(self.active_count):
            angle = i * angle_step
            indicator_x = x + (size * 0.4) * math.cos(angle)
            indicator_y = y + (size * 0.4) * math.sin(angle)
            
            painter.drawEllipse(int(indicator_x - indicator_radius),
                              int(indicator_y - indicator_radius),
                              int(indicator_radius * 2),
                              int(indicator_radius * 2))
                              
            # Draw "R" inside
            painter.setPen(QPen(QColor(76, 175, 80), 2))
            font = QFont()
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(int(indicator_x - 5), int(indicator_y + 5), "R")
            
        painter.restore()
        
    def draw_status(self, painter: QPainter, width: int, height: int):
        """Draw status text."""
        painter.save()
        
        # Determine status text
        if self.writer_active:
            status_text = "WRITER ACTIVE (Exclusive Access)"
            color = self.writer_color
        elif self.reader_active:
            if self.active_count > 1:
                status_text = f"{self.active_count} READERS ACTIVE (Concurrent)"
            else:
                status_text = "READER ACTIVE"
            color = self.reader_color
        else:
            status_text = "RESOURCE AVAILABLE"
            color = self.idle_color
            
        # Draw status
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        painter.setPen(QPen(color, 2))
        
        text_width = painter.fontMetrics().horizontalAdvance(status_text)
        painter.drawText(width // 2 - text_width // 2, 30, status_text)
        
        # Draw access count
        access_text = f"Total Accesses: {len(self.access_history)}"
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        
        text_width = painter.fontMetrics().horizontalAdvance(access_text)
        painter.drawText(width // 2 - text_width // 2, height - 10, access_text)
        
        painter.restore()
        
    def draw_access_animation(self, painter: QPainter, width: int, height: int):
        """Draw animation for new access."""
        if self.access_animation <= 0:
            return
            
        painter.save()
        
        center_x = width // 2
        center_y = height // 2
        max_radius = min(width, height) * 0.8
        
        # Calculate current radius based on animation progress
        radius = max_radius * self.access_animation
        
        # Set pen based on last access type
        if self.access_history:
            last_type, _ = self.access_history[-1]
            if last_type == 'writer':
                color = self.writer_color
            else:
                color = self.reader_color
        else:
            color = self.conflict_color
            
        pen = QPen(color, 3)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw expanding circle
        painter.drawEllipse(int(center_x - radius / 2),
                          int(center_y - radius / 2),
                          int(radius), int(radius))
                          
        painter.restore()
        
    def reset(self):
        """Reset the resource visualizer."""
        self.reader_active = False
        self.writer_active = False
        self.active_count = 0
        self.access_history.clear()
        self.update()