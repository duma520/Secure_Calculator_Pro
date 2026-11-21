nuitka --standalone ^
    --enable-plugin=pyside6 ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=icon.ico ^
    --include-data-files=icon.ico=icon.ico ^
    --follow-imports ^
    --jobs=4 ^
    --clang ^
    --remove-output ^
    --output-dir=build_output ^
    Secure_Calculator_Pro.py

