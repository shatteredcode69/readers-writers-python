#!/usr/bin/env python3
"""
Readers-Writers Synchronization System
Main Entry Point
"""
import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern look
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()