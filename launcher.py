#!/usr/bin/env python3
"""
دانلود منیجر - Download Manager
یک برنامه دانلود کننده سریع و قابل اعتماد برای لینوکس و دبیان
"""

import sys
import os
from pathlib import Path

# اضافه کردن پوشه فعلی به مسیر Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
