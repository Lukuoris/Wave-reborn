#!/usr/bin/env python3
import os
import sys
import subprocess
import webbrowser
import time

# Папка проекта (где лежит backend.py и index.html)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Import configuration
sys.path.insert(0, PROJECT_DIR)
import config

# Порты из конфигурации
BACKEND_PORT = config.get_backend_port()
FRONTEND_PORT = config.get_frontend_port()
BACKEND_HOST = config.get_backend_host()

# Colors for terminal output
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def is_installed_in_menu():
    """Check if application is installed in the menu"""
    desktop_file = os.path.expanduser("~/.local/share/applications/wave-reborn.desktop")
    return os.path.exists(desktop_file)

def offer_installation():
    """Offer to install the application to the system menu"""
    if is_installed_in_menu():
        return

    print(f"\n{BLUE}╔═══════════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║  Wave Reborn - First Time Setup                      ║{NC}")
    print(f"{BLUE}╚═══════════════════════════════════════════════════════╝{NC}\n")

    print(f"{YELLOW}Would you like to install Wave Reborn to your application menu?{NC}")
    print("This will add it to your launcher for easy access.\n")
    print("  [Y] Yes, install to menu (recommended)")
    print("  [N] No, skip for now")
    print("  [?] You can always run ./install.sh later\n")

    try:
        choice = input(f"{GREEN}Your choice [Y/n]:{NC} ").strip().lower()

        if choice in ['', 'y', 'yes', 'д', 'да']:
            print(f"\n{BLUE}Installing Wave Reborn to application menu...{NC}\n")
            install_script = os.path.join(PROJECT_DIR, "install.sh")

            if os.path.exists(install_script):
                result = subprocess.run([install_script], cwd=PROJECT_DIR)
                if result.returncode == 0:
                    print(f"\n{GREEN}✓ Installation complete!{NC}")
                    print(f"{GREEN}✓ Wave Reborn is now available in your application menu{NC}\n")
                else:
                    print(f"\n{YELLOW}Installation failed. You can try running ./install.sh manually.{NC}\n")
            else:
                print(f"\n{YELLOW}install.sh not found. Skipping installation.{NC}\n")
        else:
            print(f"\n{YELLOW}Skipping installation. You can install later with: ./install.sh{NC}\n")
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{YELLOW}Skipping installation.{NC}\n")

# 1️⃣ Создаём виртуальное окружение, если его нет
VENV_DIR = os.path.join(PROJECT_DIR, "venv")
is_first_run = not os.path.exists(VENV_DIR)

if is_first_run:
    print("Создаём виртуальное окружение...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR])

# 2️⃣ Активируем виртуальное окружение
if os.name == "nt":
    activate_script = os.path.join(VENV_DIR, "Scripts", "activate")
else:
    activate_script = os.path.join(VENV_DIR, "bin", "activate")
    
activate_cmd = f"source {activate_script}"
# используем env переменные для subprocess ниже

# 3️⃣ Устанавливаем зависимости
print("Устанавливаем зависимости...")
subprocess.run([os.path.join(VENV_DIR, "bin", "pip"), "install", "--upgrade", "pip"])
subprocess.run([os.path.join(VENV_DIR, "bin", "pip"), "install", "fastapi", "uvicorn[standard]"])

# 3.5️⃣ Предлагаем установить в меню приложений (только при первом запуске)
if is_first_run:
    offer_installation()

# 4️⃣ Запускаем backend (который обслуживает и фронтенд)
print("Запускаем backend сервер...")

backend_cmd = [
    os.path.join(VENV_DIR, "bin", "uvicorn"),
    "backend:app",
    "--reload",
    f"--host={BACKEND_HOST}",
    f"--port={BACKEND_PORT}"
]

# запускаем backend в отдельном процессе
backend_proc = subprocess.Popen(backend_cmd, cwd=PROJECT_DIR)

# небольшой таймаут, чтобы backend успел стартовать
time.sleep(2)

# 5️⃣ Открываем браузер с фронтендом (backend обслуживает статические файлы)
webbrowser.open(f"http://127.0.0.1:{BACKEND_PORT}/")

# 6️⃣ Держим скрипт живым, пока работает backend
try:
    backend_proc.wait()
except KeyboardInterrupt:
    print("Закрываем сервер...")
    backend_proc.terminate()
