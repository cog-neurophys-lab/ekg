# ekg



## Create binary for deployment

```
python -m venv .env
.env\Scripts\activate.bat
python -m pip install requirements.txt
python -m pip install pyinstaller
pyinstaller --console --version-file file_version_info.txt --onefile --name ekg main.py
```