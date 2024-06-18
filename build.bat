rmdir /S /Q build
rmdir /S /Q dist
del /Q fcbe.zip
pyinstaller --noconsole fcbe.py
cd .\dist\fcbe
tar.exe cavf ..\..\fcbe.zip *
cd ..\..