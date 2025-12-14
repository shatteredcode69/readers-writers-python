"""
Synchronization primitives and algorithms for Readers-Writers problem
Implements both reader-priority and writer-priority solutions
"""
import threading
import time
from typing import Optional
from collections import deque


class ReaderWriterLock:
    """
    Implementation of Readers-Writers lock with configurable priority.
    
    This class provides synchronization for multiple readers and writers
    accessing a shared resource. It prevents race conditions while
    allowing either readers or writers to have priority.
    
    Key Concepts:
    - Readers can read concurrently (no mutual exclusion needed)
    - Writers need exclusive access (mutual exclusion required)
    - Priority determines who gets access first when both are waiting
    """
    
    def __init__(self, writer_priority: bool = False):
        """
        Initialize the Readers-Writers lock.
        
        Args:
            writer_priority: If True, writers have priority over readers.
                            If False, readers have priority (default).
        """
        self.writer_priority = writer_priority
        
        # Counter for active readers
        self.readers_count = 0
        
        # Mutex to protect readers_count
        self.readers_count_mutex = threading.Lock()
        
        # Semaphore for writers (binary semaphore for exclusive write access)
        self.writers_mutex = threading.Semaphore(1)
        
        # Semaphore to control access when writers have priority
        self.read_try = threading.Semaphore(1)
        
        # Condition variable for waiting threads
        self.condition = threading.Condition()
        
        # Queues for waiting threads (for fairness)
        self.reader_queue = deque()
        self.writer_queue = deque()
        
        # Statistics
        self.active_readers = 0
        self.active_writers = 0
        self.waiting_readers = 0
        self.waiting_writers = 0
        self.reads_completed = 0
        self.writes_completed = 0
        self.conflicts = 0
        
        # For deadlock prevention
        self.deadlock_detection_lock = threading.Lock()
        
    def reader_enter(self, reader_id: int):
        """
        Reader attempts to enter critical section.
        
        Reader-priority algorithm:
        1. Wait for writer to finish (read_try semaphore)
        2. Increment readers count (protected by mutex)
        3. If first reader, acquire writers_mutex to block writers
        
        Writer-priority algorithm:
        1. Acquire read_try to prevent new readers
        2. Check if writers are waiting
        3. If no writers, proceed like reader-priority
        """
        start_time = time.time()
        
        if self.writer_priority:
            # Writer-priority implementation
            with self.condition:
                self.waiting_readers += 1
                
            # Acquire read_try to prevent new readers when writers arrive
            self.read_try.acquire()
            
            with self.condition:
                self.waiting_readers -= 1
            
            # Check if writers are waiting
            with self.condition:
                while self.waiting_writers > 0:
                    self.conflicts += 1
                    self.condition.wait()
            
            with self.readers_count_mutex:
                self.readers_count += 1
                if self.readers_count == 1:
                    # First reader blocks writers
                    self.writers_mutex.acquire()
            
            self.read_try.release()
            
        else:
            # Reader-priority implementation (original solution)
            # Prevent writers from acquiring lock while readers are active
            self.read_try.acquire()
            
            with self.readers_count_mutex:
                self.readers_count += 1
                if self.readers_count == 1:
                    # First reader blocks writers
                    self.writers_mutex.acquire()
            
            self.read_try.release()
        
        with self.condition:
            self.active_readers += 1
        
        wait_time = time.time() - start_time
        if wait_time > 0.1:  # If waited more than 100ms, log as conflict
            self.conflicts += 1
            
        return wait_time
    
    def reader_exit(self):
        """Reader leaves critical section."""
        with self.readers_count_mutex:
            self.readers_count -= 1
            if self.readers_count == 0:
                # Last reader releases writers lock
                self.writers_mutex.release()
        
        with self.condition:
            self.active_readers -= 1
            self.reads_completed += 1
            # Notify waiting writers if no more readers
            if self.readers_count == 0:
                self.condition.notify_all()
    
    def writer_enter(self, writer_id: int):
        """
        Writer attempts to enter critical section.
        
        Writer needs exclusive access:
        1. Acquire writers_mutex (blocks other writers)
        2. For writer-priority: also prevent new readers
        """
        start_time = time.time()
        
        if self.writer_priority:
            # Writer-priority implementation
            with self.condition:
                self.waiting_writers += 1
            
            # Prevent new readers from starting
            self.read_try.acquire()
            
            # Acquire exclusive write lock
            self.writers_mutex.acquire()
            
            with self.condition:
                self.waiting_writers -= 1
                self.active_writers += 1
            
            self.read_try.release()
            
        else:
            # Reader-priority implementation
            # Just acquire exclusive write lock
            with self.condition:
                self.waiting_writers += 1
            
            self.writers_mutex.acquire()
            
            with self.condition:
                self.waiting_writers -= 1
                self.active_writers += 1
        
        wait_time = time.time() - start_time
        if wait_time > 0.1:  # If waited more than 100ms, log as conflict
            self.conflicts += 1
            
        return wait_time
    
    def writer_exit(self):
        """Writer leaves critical section."""
        self.writers_mutex.release()
        
        with self.condition:
            self.active_writers -= 1
            self.writes_completed += 1
            # Notify all waiting threads
            self.condition.notify_all()
    
    def get_stats(self) -> dict:
        """Get current synchronization statistics."""
        with self.condition:
            return {
                'active_readers': self.active_readers,
                'active_writers': self.active_writers,
                'waiting_readers': self.waiting_readers,
                'waiting_writers': self.waiting_writers,
                'reads_completed': self.reads_completed,
                'writes_completed': self.writes_completed,
                'conflicts': self.conflicts
            }
    
    def set_priority(self, writer_priority: bool):
        """Change priority mode at runtime."""
        # Note: This is a simplified implementation
        # In production, we'd need to safely transition
        self.writer_priority = writer_priority
        
    def try_detect_deadlock(self) -> Optional[str]:
        """
        Simple deadlock detection.
        Returns error message if deadlock suspected, None otherwise.
        """
        with self.deadlock_detection_lock:
            # Check for potential deadlock conditions
            if (self.active_writers > 0 and self.active_readers > 0):
                return "Deadlock detected: Both readers and writers active"
            
            if (self.waiting_writers > 5 and self.waiting_readers > 5):
                return "Potential starvation: Many threads waiting"
            
            return None


class FairReaderWriterLock:
    """
    Fair Readers-Writers lock (no starvation).
    
    This implementation ensures fairness by using queues,
    preventing starvation of either readers or writers.
    """
    
    def __init__(self):
        """Initialize fair lock."""
        self.readers_count = 0
        self.writer_active = False
        
        self.mutex = threading.Lock()
        self.readers_condition = threading.Condition(self.mutex)
        self.writers_condition = threading.Condition(self.mutex)
        
        self.waiting_readers = 0
        self.waiting_writers = 0
        
    def reader_enter(self, reader_id: int):
        """Reader enters with fairness."""
        with self.mutex:
            self.waiting_readers += 1
            while self.writer_active or self.waiting_writers > 0:
                self.readers_condition.wait()
            self.waiting_readers -= 1
            self.readers_count += 1
        return 0  # Simplified wait time
    
    def reader_exit(self):
        """Reader exits."""
        with self.mutex:
            self.readers_count -= 1
            if self.readers_count == 0:
                self.writers_condition.notify()
    
    def writer_enter(self, writer_id: int):
        """Writer enters with fairness."""
        with self.mutex:
            self.waiting_writers += 1
            while self.writer_active or self.readers_count > 0:
                self.writers_condition.wait()
            self.waiting_writers -= 1
            self.writer_active = True
        return 0  # Simplified wait time
    
    def writer_exit(self):
        """Writer exits."""
        with self.mutex:
            self.writer_active = False
            if self.waiting_readers > 0:
                self.readers_condition.notify_all()
            else:
                self.writers_condition.notify()


class DatabaseSimulator:
    """
    Simulates a shared database with read/write operations.
    
    This class represents the shared resource that readers and writers
    access. It provides simulated read and write operations with
    configurable delays.
    """
    
    def __init__(self, initial_data: str = "Initial Database Content"):
        """Initialize database with initial content."""
        self.data = initial_data
        self.access_count = 0
        self.data_mutex = threading.Lock()
        
    def read(self, reader_id: int, delay: float = 1.0) -> str:
        """
        Simulate a read operation.
        
        Multiple readers can read concurrently (no mutual exclusion needed).
        The delay simulates the time taken to read data.
        
        Args:
            reader_id: ID of the reading thread
            delay: Time to simulate reading (seconds)
            
        Returns:
            Current database content
        """
        # Simulate reading time
        time.sleep(delay)
        
        with self.data_mutex:
            self.access_count += 1
            return f"[Reader {reader_id}] Read: {self.data[:50]}..." \
                   f" (Access #{self.access_count})"
    
    def write(self, writer_id: int, new_data: str, delay: float = 2.0) -> str:
        """
        Simulate a write operation.
        
        Only one writer can write at a time (exclusive access required).
        The delay simulates the time taken to write data.
        
        Args:
            writer_id: ID of the writing thread
            new_data: Data to write
            delay: Time to simulate writing (seconds)
            
        Returns:
            Confirmation message
        """
        # Simulate writing time
        time.sleep(delay)
        
        with self.data_mutex:
            self.data = new_data
            self.access_count += 1
            return f"[Writer {writer_id}] Wrote: {new_data[:50]}..." \
                   f" (Access #{self.access_count})"
    
    def get_status(self) -> dict:
        """Get current database status."""
        with self.data_mutex:
            return {
                'data_preview': self.data[:50] + "..." if len(self.data) > 50 else self.data,
                'access_count': self.access_count,
                'data_length': len(self.data)
            }