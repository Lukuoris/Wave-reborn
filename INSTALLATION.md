# Wave Reborn - Installation Guide

## 🚀 Easy Installation (Recommended)

Wave Reborn now features a **one-command installation** that takes care of everything!

### Step 1: Clone and Run

```bash
git clone https://github.com/Lukuoris/wave-reborn.git
cd wave-reborn
python start.py
```

### Step 2: Follow the Prompts

On first run, you'll see:

```
Создаём виртуальное окружение...
Устанавливаем зависимости...

╔═══════════════════════════════════════════════════════╗
║  Wave Reborn - First Time Setup                      ║
╚═══════════════════════════════════════════════════════╝

Would you like to install Wave Reborn to your application menu?
This will add it to your launcher for easy access.

  [Y] Yes, install to menu (recommended)
  [N] No, skip for now
  [?] You can always run ./install.sh later

Your choice [Y/n]:
```

### Step 3: Enjoy!

Just press **Enter** or type **Y**, and Wave Reborn will:
- ✅ Install to your application menu
- ✅ Add the application icon
- ✅ Make it available in all desktop environments
- ✅ Start the mixer automatically

## 📋 What Gets Installed?

### System Menu Integration
- **Location**: `~/.local/share/applications/wave-reborn.desktop`
- **Icon**: `~/.local/share/icons/wave-reborn.png`
- **Accessible from**: GNOME Activities, KDE Menu, XFCE Menu, etc.

### Autostart (Optional)
Configure autostart from the web interface:
- Settings → Application Settings → Autostart on Login
- **Location**: `~/.config/autostart/wave-reborn.desktop`

## 🎯 Manual Installation Options

### Option 1: Install to System Menu Only

```bash
./install.sh
```

This only installs the `.desktop` file and icon. Run the app via:
- Application menu
- System tray mode: `./run_tray.sh`

### Option 2: Run Without Installation

```bash
# System tray mode
./run_tray.sh

# Or Qt desktop GUI
python wavepipe.py

# Or backend only
python run_wavepipe.py
```

## 🗑️ Uninstallation

Remove Wave Reborn from your system menu:

```bash
./uninstall.sh
```

This removes:
- Application launcher entry
- Application icon
- Autostart configuration (if enabled)

**Note**: This does not remove:
- The project directory
- Virtual environment
- Configuration files

## 🔧 Troubleshooting

### Installation Script Not Executable

If `install.sh` doesn't run:
```bash
chmod +x install.sh
./install.sh
```

### Desktop File Not Showing

Try updating the desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

Or log out and log back in.

### Python Not Found

Make sure Python 3.7+ is installed:
```bash
python3 --version
# or
python --version
```

## 📝 File Structure

After installation, Wave Reborn will have:

```
~/.local/share/applications/
└── wave-reborn.desktop          # Application menu entry

~/.local/share/icons/
└── wave-reborn.png              # Application icon

~/.config/autostart/             # Only if autostart enabled
└── wave-reborn.desktop          # Autostart entry

/path/to/wave-reborn/            # Project directory
├── venv/                        # Virtual environment
├── wave_config.json             # User configuration
└── ...                          # Project files
```

## 🎉 Quick Tips

1. **First Time Setup**: Just run `python start.py` and follow the prompts!
2. **Enable Autostart**: Use the web interface Settings panel
3. **Quick Launch**: Use your system's application launcher (Super key, Activities, etc.)
4. **Manual Install**: Run `./install.sh` if you skipped first-time setup
5. **Clean Uninstall**: Run `./uninstall.sh` to remove from system menu

---

**Need help?** Open an issue on [GitHub](https://github.com/Lukuoris/wave-reborn/issues)
