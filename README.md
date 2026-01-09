<div align="center">

# 🌊 Wave Reborn

### Audio Mixer for Linux Streamers

*Elgato Wave Link alternative built for Linux content creators*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PulseAudio](https://img.shields.io/badge/audio-PulseAudio-orange.svg)](https://www.freedesktop.org/wiki/Software/PulseAudio/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

[Features](#-features) • [Quick Start](#-quick-start) • [Usage](#-usage) • [Configuration](#-configuration) • [API](#-api-endpoints)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎛️ **Professional Mixer**
- **Independent Audio Channels** - Route applications to separate channels (Music, Game, Voice, System)
- **Dual-Level Control** - Separate volumes for what you hear vs. what your stream hears
- **Real-time VU Meters** - Visual audio feedback with WebSocket updates (~20 FPS)
- **Application Routing** - Drag-and-drop style routing for any audio application

</td>
<td width="50%">

### 🎨 **Modern Interface**
- **Sleek Web UI** - Professional gradient design inspired by Elgato Wave Link
- **System Tray Integration** - Quick access from your desktop
- **Settings Panel** - Configure everything through beautiful UI
- **Qt5 Desktop App** - Alternative desktop interface available

</td>
</tr>
</table>

### 🔧 **Flexible & Configurable**
- Customizable channel names and count
- Adjustable audio latency (10-100ms)
- Multiple audio device support with auto-detection
- Full REST API + WebSocket support for integrations

---

## 🚀 Quick Start

### Prerequisites

- **Linux** with PulseAudio (most distributions)
- **Python 3.7+**
- **PulseAudio** daemon running

### Installation

```bash
# Clone the repository
git clone https://github.com/Lukuoris/wave-reborn.git
cd wave-reborn

# Run the launcher (auto-installs dependencies)
python start.py
```

That's it! The application will:
1. Create a virtual environment
2. Install all dependencies (FastAPI, Uvicorn, PyQt5)
3. Start the backend server
4. Open your browser to the mixer interface

### Alternative: System Tray Mode (Recommended)

```bash
# Install dependencies first
pip install -r requirements.txt

# Run with system tray integration
./run_tray.sh
# or
python tray_app.py
```

**Tray Menu Features:**
- 🌐 **Open Mixer** - Launch web interface
- ⚙️ **Settings** - Configure audio and network
- 🔄 **Restart Backend** - Apply changes
- ❌ **Quit** - Clean shutdown

---

## 🎛️ Usage

### Web Interface (Recommended)

<div align="center">

**Main Mixer Interface**

1. **Vertical Faders** - Control volume levels
   - **Monitor** (left) - What you hear in headphones
   - **Stream** (right) - What OBS/stream captures
2. **VU Meters** - Real-time audio level visualization
3. **Mute Buttons** - Quickly silence channels
4. **Application Routing** - Route any app to any channel

**Settings Panel**

- 🎧 **Audio Configuration** - Select output device, adjust latency
- 📻 **Channel Management** - Add, remove, rename channels
- 🌐 **Network Settings** - Configure ports and host binding

</div>

### Desktop GUI (Qt5)

```bash
python wavepipe.py
```

Traditional desktop interface with:
- Horizontal sliders for volume control
- Device selection dropdown
- Quick preset toggles
- Native system integration

### Backend Only Mode

```bash
python run_wavepipe.py
```

Runs backend without separate frontend server (access via `http://127.0.0.1:8000/`)

---

## ⚙️ Configuration

### Web-based Configuration (Easy)

1. Click **⚙️ Settings** in the web interface
2. Select your audio device from the dropdown
3. Customize channels, latency, and network settings
4. Click **Save Settings**
5. Restart the application

### Command-line Configuration

```bash
python configure.py
```

Interactive menu for:
- Audio device selection (auto-detected)
- Channel customization
- Latency adjustment
- Port configuration

### Manual Configuration

Edit `wave_config.json` (auto-generated on first run):

```json
{
  "audio": {
    "output_device": "alsa_output.usb-AudioDevice-analog-stereo",
    "channels": ["Music", "Game", "Voice", "System"],
    "latency_ms": 20
  },
  "network": {
    "backend_port": 8000,
    "frontend_port": 8080,
    "backend_host": "127.0.0.1"
  }
}
```

**Find your audio device:**
```bash
pactl list short sinks
```

---

## 📡 API Endpoints

Backend runs on `http://127.0.0.1:8000` by default.

### REST API

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/channels` | GET | - | Get all channels state |
| `/set_volume_stream` | POST | `channel`, `value` | Set stream volume (0-100) |
| `/set_volume_you` | POST | `channel`, `value` | Set monitor volume (0-100) |
| `/mute` | POST | `channel` | Mute channel |
| `/unmute` | POST | `channel` | Unmute channel |
| `/applications` | GET | - | List all audio applications |
| `/route_application` | POST | `app_index`, `channel` | Route app to channel |
| `/config` | GET | - | Get current configuration |
| `/config` | POST | `config` (JSON) | Save configuration |
| `/config/reset` | POST | - | Reset to defaults |
| `/config/devices` | GET | - | List audio devices |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/vu` | Real-time VU meter data stream (~20 FPS) |

**Example WebSocket Usage:**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/vu');
ws.onmessage = (e) => {
  const levels = JSON.parse(e.data);
  // levels = { "Music": 0.75, "Game": 0.4, ... }
};
```

---

## 🎮 Application Routing

### Via Web Interface
1. Navigate to **Application Routing** section
2. Click **Refresh Applications** to scan for audio apps
3. Select target channel from dropdown for each application
4. Routes instantly - no restart required

### Via Command Line
```bash
# List all applications with their sink-input IDs
pactl list sink-inputs

# Route application to a channel
pactl move-sink-input <sink-input-id> <channel>_Apps

# Example: Route Firefox to Music channel
pactl move-sink-input 42 Music_Apps
```

---

## 🐛 Troubleshooting

<details>
<summary><b>No audio devices found</b></summary>

```bash
# Check if PulseAudio is running
systemctl --user status pulseaudio

# Start PulseAudio if not running
systemctl --user start pulseaudio

# Restart PulseAudio if needed
systemctl --user restart pulseaudio

# Verify devices are detected
pactl list short sinks
```
</details>

<details>
<summary><b>pactl command not found</b></summary>

Install PulseAudio utilities:

```bash
# Debian/Ubuntu
sudo apt install pulseaudio-utils

# Fedora
sudo dnf install pulseaudio-utils

# Arch Linux
sudo pacman -S pulseaudio

# openSUSE
sudo zypper install pulseaudio-utils
```
</details>

<details>
<summary><b>Backend won't start - Port already in use</b></summary>

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process or change port
python configure.py
# Then select different port in network settings
```
</details>

<details>
<summary><b>Channels disappear after reboot</b></summary>

Wave Reborn channels are temporary and cleared on restart. This is by design.

**Solutions:**
1. Use system tray mode - starts automatically when you log in
2. Add to startup applications:
   ```bash
   # Add this to your autostart
   /path/to/wave-reborn/run_tray.sh
   ```
</details>

<details>
<summary><b>Audio quality issues / crackling</b></summary>

Adjust latency in settings:

1. Open **⚙️ Settings**
2. Increase **Audio Latency** (try 30-50ms)
3. Save and restart

Higher latency = better stability, lower latency = less delay.
</details>

---


## 📜 License

This project is open source and available under the MIT License.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so.
```

---

## 🙏 Acknowledgments

- Built for the Linux streaming community
- Inspired by Elgato Wave Link
- Optimized for OBS Studio integration
- Thanks to all contributors and users

---

<div align="center">

### 🌟 Star this project if you find it useful!

**Happy Streaming! 🎬✨**

Made with ❤️ by [Lukuoris](https://github.com/Lukuoris)

[Report Bug](https://github.com/Lukuoris/wave-reborn/issues) • [Request Feature](https://github.com/Lukuoris/wave-reborn/issues)

</div>
