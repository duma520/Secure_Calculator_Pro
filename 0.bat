cls
rmdir /s /q build
rmdir /s /q dist

pyinstaller --windowed --icon=icon.ico --add-data "icon.ico;." Secure_Calculator_Pro.py