"""
Simulation Manager - Coordinates threads and synchronization
Handles thread creation, management, and communication with GUI
"""
import threading
import time
import queue
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from sync import ReaderWriterLock, DatabaseSimulator


class ThreadMessage:
    """Message sent from worker threads to GUI."""
    
    def __init__(self, thread_type: str, thread_id: int, 
                 action: str, status: str, data: Optional[str] = None):
        """
        Initialize thread message.
        
        Args:
            thread_type: 'reader' or 'writer'
            thread_id: Unique thread identifier
            action: What the thread is doing ('enter', 'read', 'write', 'exit', 'wait')
            status: Current status ('active', 'waiting', 'completed')
            data: Optional additional data
        """
        self.thread_type = thread_type
        self.thread_id = thread_id
        self.action = action
        self.status = status
        self.data = data
        self.timestamp = time.time()


class SimulationManager(QObject):
    """
    Manages the entire simulation.
    
    Creates and controls reader/writer threads, handles synchronization,
    and communicates with the GUI via signals.
    """
    
    # Signals for GUI updates
    status_update = pyqtSignal(dict)  # Statistics updates
    log_message = pyqtSignal(str, str)  # Log messages (message, level)
    thread_update = pyqtSignal(dict)  # Thread status updates
    reader_active = pyqtSignal(bool)  # Reader active in resource
    writer_active = pyqtSignal(bool)  # Writer active in resource
    
    def __init__(self, num_readers: int = 5, num_writers: int = 3,
                 read_delay: float = 1.0, write_delay: float = 2.0,
                 writer_priority: bool = False):
        """
        Initialize simulation manager.
        
        Args:
            num_readers: Number of reader threads
            num_writers: Number of writer threads
            read_delay: Simulated read operation time (seconds)
            write_delay: Simulated write operation time (seconds)
            writer_priority: True for writer priority, False for reader priority
        """
        super().__init__()
        
        # Configuration
        self.num_readers = num_readers
        self.num_writers = num_writers
        self.read_delay = read_delay
        self.write_delay = write_delay
        self.writer_priority = writer_priority
        
        # Synchronization primitives
        self.rw_lock = ReaderWriterLock(writer_priority)
        self.database = DatabaseSimulator()
        
        # Thread management
        self.reader_threads = []
        self.writer_threads = []
        self.thread_counter = 0
        
        # Control flags
        self.running = False
        self.paused = False
        self.pause_condition = threading.Condition()
        
        # Message queue for thread-GUI communication
        self.message_queue = queue.Queue()
        
        # Statistics timer
        self.stats_timer = None
        
        # Initialize thread IDs
        self.next_reader_id = 1
        self.next_writer_id = 1
        
    def start(self):
        """Start the simulation."""
        if self.running:
            self.log_message.emit("Simulation already running", "WARNING")
            return
        
        self.running = True
        self.paused = False
        
        # Create reader threads
        for i in range(self.num_readers):
            thread = threading.Thread(
                target=self.reader_worker,
                args=(self.next_reader_id,),
                daemon=True,
                name=f"Reader-{self.next_reader_id}"
            )
            self.reader_threads.append(thread)
            self.next_reader_id += 1
        
        # Create writer threads
        for i in range(self.num_writers):
            thread = threading.Thread(
                target=self.writer_worker,
                args=(self.next_writer_id,),
                daemon=True,
                name=f"Writer-{self.next_writer_id}"
            )
            self.writer_threads.append(thread)
            self.next_writer_id += 1
        
        # Start all threads
        for thread in self.reader_threads + self.writer_threads:
            thread.start()
        
        # Start statistics update timer
        self.stats_timer = threading.Thread(target=self.stats_worker, daemon=True)
        self.stats_timer.start()
        
        # Start message processor
        self.message_processor = threading.Thread(target=self.process_messages, daemon=True)
        self.message_processor.start()
        
        self.log_message.emit(f"Started {self.num_readers} readers and {self.num_writers} writers", "INFO")
        
    def pause(self):
        """Pause the simulation."""
        with self.pause_condition:
            self.paused = True
            self.log_message.emit("Simulation paused", "INFO")
    
    def resume(self):
        """Resume the simulation."""
        with self.pause_condition:
            self.paused = False
            self.pause_condition.notify_all()
            self.log_message.emit("Simulation resumed", "INFO")
    
    def stop(self):
        """Stop the simulation."""
        self.running = False
        
        # Resume if paused to allow threads to exit
        with self.pause_condition:
            self.paused = False
            self.pause_condition.notify_all()
        
        # Wait for threads to finish (with timeout)
        for thread in self.reader_threads + self.writer_threads:
            thread.join(timeout=1.0)
        
        # Clear thread lists
        self.reader_threads.clear()
        self.writer_threads.clear()
        
        self.log_message.emit("Simulation stopped", "INFO")
    
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self.running
    
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return self.paused
    
    def reader_worker(self, reader_id: int):
        """
        Reader thread worker function.
        
        Continuously attempts to read from the database.
        Follows the synchronization protocol.
        """
        read_count = 0
        
        while self.running:
            # Check if simulation is paused
            with self.pause_condition:
                while self.paused and self.running:
                    self.pause_condition.wait()
            
            if not self.running:
                break
            
            try:
                # Signal waiting to enter
                self.send_thread_message('reader', reader_id, 'enter', 'waiting')
                
                # Request read access
                wait_time = self.rw_lock.reader_enter(reader_id)
                
                if wait_time > 0:
                    self.log_message.emit(
                        f"Reader {reader_id} waited {wait_time:.2f}s to enter",
                        "DEBUG"
                    )
                
                # Signal active reading
                self.send_thread_message('reader', reader_id, 'read', 'active')
                self.reader_active.emit(True)
                
                # Perform read operation
                result = self.database.read(reader_id, self.read_delay)
                
                # Signal completion
                self.send_thread_message('reader', reader_id, 'exit', 'completed', result)
                self.reader_active.emit(False)
                
                # Release read access
                self.rw_lock.reader_exit()
                
                read_count += 1
                
                # Brief pause before next read attempt
                time.sleep(0.5)
                
            except Exception as e:
                self.log_message.emit(
                    f"Reader {reader_id} error: {str(e)}",
                    "ERROR"
                )
                break
    
    def writer_worker(self, writer_id: int):
        """
        Writer thread worker function.
        
        Continuously attempts to write to the database.
        Follows the synchronization protocol.
        """
        write_count = 0
        
        while self.running:
            # Check if simulation is paused
            with self.pause_condition:
                while self.paused and self.running:
                    self.pause_condition.wait()
            
            if not self.running:
                break
            
            try:
                # Signal waiting to enter
                self.send_thread_message('writer', writer_id, 'enter', 'waiting')
                
                # Request write access
                wait_time = self.rw_lock.writer_enter(writer_id)
                
                if wait_time > 0:
                    self.log_message.emit(
                        f"Writer {writer_id} waited {wait_time:.2f}s to enter",
                        "DEBUG"
                    )
                
                # Signal active writing
                self.send_thread_message('writer', writer_id, 'write', 'active')
                self.writer_active.emit(True)
                
                # Perform write operation
                data = f"Data written by Writer {writer_id} at {time.time():.2f}"
                result = self.database.write(writer_id, data, self.write_delay)
                
                # Signal completion
                self.send_thread_message('writer', writer_id, 'exit', 'completed', result)
                self.writer_active.emit(False)
                
                # Release write access
                self.rw_lock.writer_exit()
                
                write_count += 1
                
                # Brief pause before next write attempt
                time.sleep(0.5)
                
            except Exception as e:
                self.log_message.emit(
                    f"Writer {writer_id} error: {str(e)}",
                    "ERROR"
                )
                break
    
    def stats_worker(self):
        """Worker thread to periodically update statistics."""
        update_interval = 0.1  # Update 10 times per second
        
        while self.running:
            try:
                # Get current statistics
                stats = self.rw_lock.get_stats()
                
                # Add additional stats
                db_stats = self.database.get_status()
                stats.update({
                    'database_accesses': db_stats['access_count'],
                    'database_preview': db_stats['data_preview']
                })
                
                # Check for deadlock
                deadlock_msg = self.rw_lock.try_detect_deadlock()
                if deadlock_msg:
                    self.log_message.emit(deadlock_msg, "WARNING")
                
                # Emit signal for GUI update
                self.status_update.emit(stats)
                
                # Sleep for update interval
                time.sleep(update_interval)
                
            except Exception as e:
                self.log_message.emit(f"Stats worker error: {str(e)}", "ERROR")
                break
    
    def process_messages(self):
        """Process messages from worker threads."""
        while self.running:
            try:
                # Get message with timeout
                message = self.message_queue.get(timeout=0.1)
                
                # Convert to dict for signal emission
                message_dict = {
                    'thread_type': message.thread_type,
                    'thread_id': message.thread_id,
                    'action': message.action,
                    'status': message.status,
                    'data': message.data,
                    'timestamp': message.timestamp
                }
                
                # Emit to GUI
                self.thread_update.emit(message_dict)
                
                # Log significant events
                if message.action in ['read', 'write']:
                    level = "DEBUG" if message.status == 'active' else "INFO"
                    self.log_message.emit(
                        f"{message.thread_type.title()} {message.thread_id} "
                        f"{message.action} {message.status}",
                        level
                    )
                
                # Mark task as done
                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message.emit(f"Message processor error: {str(e)}", "ERROR")
                break
    
    def send_thread_message(self, thread_type: str, thread_id: int,
                           action: str, status: str, data: Optional[str] = None):
        """
        Send a message from a worker thread to the GUI.
        
        This method is thread-safe and should be called from worker threads.
        """
        message = ThreadMessage(thread_type, thread_id, action, status, data)
        
        try:
            self.message_queue.put(message, timeout=0.1)
        except queue.Full:
            # If queue is full, drop the message (shouldn't happen often)
            pass
    
    def update_configuration(self, num_readers: Optional[int] = None,
                            num_writers: Optional[int] = None,
                            read_delay: Optional[float] = None,
                            write_delay: Optional[float] = None,
                            writer_priority: Optional[bool] = None):
        """
        Update simulation configuration at runtime.
        
        Note: Some changes may require restarting simulation.
        """
        if num_readers is not None:
            self.num_readers = num_readers
            self.log_message.emit(f"Readers updated to {num_readers}", "INFO")
        
        if num_writers is not None:
            self.num_writers = num_writers
            self.log_message.emit(f"Writers updated to {num_writers}", "INFO")
        
        if read_delay is not None:
            self.read_delay = read_delay
            self.log_message.emit(f"Read delay updated to {read_delay}s", "INFO")
        
        if write_delay is not None:
            self.write_delay = write_delay
            self.log_message.emit(f"Write delay updated to {write_delay}s", "INFO")
        
        if writer_priority is not None:
            self.writer_priority = writer_priority
            self.rw_lock.set_priority(writer_priority)
            mode = "Writer Priority" if writer_priority else "Reader Priority"
            self.log_message.emit(f"Priority mode changed to {mode}", "INFO")