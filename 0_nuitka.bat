cls
rmdir /s /q *.build
rmdir /s /q *.dist

nuitka --standalone --enable-plugin=pyqt5 --windows-console-mode=disable --include-package-data=pypinyin --windows-icon-from-ico=icon.ico --jobs=4 --output-dir=build_output Secure_Calculator_Pro.py