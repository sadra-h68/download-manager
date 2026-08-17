#!/bin/bash

# دانلود منیجر - Download Manager Installer
# نصب برنامه دانلود منیجر در دبیان/اوبونتو

echo "🔧 دانلود منیجر را نصب می‌کنیم..."

# بررسی وجود Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 نصب نیست. لطفا با دستور زیر نصب کنید:"
    echo "sudo apt install python3 python3-pip"
    exit 1
fi

# بررسی وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip نصب نیست. نصب می‌شود..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# نصب وابستگی‌ها
echo "📦 نصب وابستگی‌ها..."
pip3 install -r requirements.txt

# ایجاد shortcut در دسکتاپ
DESKTOP_FILE="$HOME/.local/share/applications/download-manager.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Download Manager
Comment=دانلود منیجر
Exec=python3 $(pwd)/main.py
Icon=document-save
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

echo "✅ نصب موفقیت‌آمیز بود!"
echo ""
echo "🚀 راه‌های اجرای برنامه:"
echo "   1. اجرای مستقیم: python3 main.py"
echo "   2. از طریق launcher: python3 launcher.py"
echo "   3. جستجو در منوی دسکتاپ: 'Download Manager'"
