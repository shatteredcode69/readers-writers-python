# Readers-Writers Synchronization System with PyQt GUI

A complete, interactive simulation system for demonstrating and experimenting with the classic Readers-Writers synchronization problem in Operating Systems. Features a modern, animated GUI with real-time visualization of thread behavior.


## 📋 Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Synchronization Algorithms](#synchronization-algorithms)
- [GUI Components](#gui-components)
- [Thread Management](#thread-management)
- [Educational Value](#educational-value)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🔄 Synchronization Implementations
- **Reader-Priority Algorithm** (Default)
  - Readers have priority over writers
  - Multiple readers can read concurrently
  - Writers wait until no readers are active

- **Writer-Priority Algorithm** (Configurable)
  - Writers have priority over readers
  - Prevents writer starvation
  - New readers wait if writers are waiting

### 🎨 Interactive GUI
- **Real-time Visualization**
  - Animated thread icons with color-coded states
  - Live resource access visualization
  - Concurrent reader indicators
  - Pulsing animations for active/waiting states

- **Comprehensive Controls**
  - Dynamic slider controls for thread counts and delays
  - Real-time priority switching
  - Start/Pause/Stop/Reset functionality
  - Configurable operation delays

- **Live Statistics**
  - Active/waiting readers/writers counters
  - Completed operations tracking
  - Conflict detection and counting
  - Throughput metrics

### 🔧 Technical Features
- **Thread-Safe Design**
  - Qt Signals & Slots for thread-GUI communication
  - Queue-based message passing
  - No GUI updates from worker threads
  - Deadlock detection mechanism

- **Modular Architecture**
  - Clean separation of concerns
  - Reusable synchronization primitives
  - Extensible visualization components

## 🛠 Prerequisites

### Operating Systems
- Ubuntu 20.04+ / Debian 11+ / Arch Linux (latest)
- Python 3.8 or higher

### Python Packages
```bash
PyQt6>=6.4.0
