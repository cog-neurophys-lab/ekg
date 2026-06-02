# Elektrokardiogram (EKG) Stream Viewer

This is a simple Python-based GUI to stream data from the [Olimex EKG/EMG Arduino
Shield](https://www.olimex.com/Products/Duino/Shields/SHIELD-EKG-EMG/open-source-hardware)
via a USB serial connection. 

![](screenshot.png)

The EKG Stream Viewer is free and open source, licensed under the MIT license. It uses code from Paul Logston's [olimex-ekg-emg](https://github.com/logston/olimex-ekg-emg) (see [LICENSE](olimex/LICENSE)).

Dependencies are listed in [`pyproject.toml`](pyproject.toml) and include the standard scientific stack of NumPy, SciPy and Matplotlib.


## Get started

Download a [(currently only Windows) release](https://github.com/cog-neurophys-lab/ekg/releases) and start the executable after connecting the Arduino (with the Olimex EKG Shield) via USB to your PC.

## Create binary for deployment

```
uv sync --group dev
uv run pyinstaller --console --version-file file_version_info.txt --onefile --name ekg ekg_viewer.py --hidden-import matplotlib.backends.backend_pdf
```