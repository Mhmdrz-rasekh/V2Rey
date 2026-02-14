#!/bin/bash
# run.sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# افزودن پوشه bin محلی به متغیر PATH سیستم فقط برای همین پردازش
export PATH="$DIR/bin:$PATH"

# اجرای برنامه پایتون از طریق محیط مجازی
exec ./venv/bin/python main.py
