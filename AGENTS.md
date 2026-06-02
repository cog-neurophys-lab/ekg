# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A Python GUI for streaming and displaying EKG/EMG data from an [Olimex EKG/EMG Arduino Shield](https://www.olimex.com/Products/Duino/Shields/SHIELD-EKG-EMG/) over USB serial. Intended for teaching/lab use.

There are two GUI implementations:
- `ekg_viewer.py` — the active implementation using **PySide6 + pyqtgraph** (faster rendering, `QTimer`-driven updates at 50 ms)
- `main.py` — an older **matplotlib/TkAgg** implementation (kept for reference)

## Setup and running

This project uses [uv](https://github.com/astral-sh/uv) for dependency management. Python 3.10+ is required (see `.python-version`).

```bash
uv sync                  # install dependencies
uv run python ekg_viewer.py   # run the active GUI
uv run python main.py         # run the legacy matplotlib GUI
```

## Building a Windows executable

```bash
uv run pyinstaller --console --version-file file_version_info.txt --onefile --name ekg ekg_viewer.py --hidden-import matplotlib.backends.backend_pdf
```

The `file_version_info.txt` file carries the Windows version metadata for the `.exe`.

## Architecture

### Data flow

```
Arduino (Olimex Shield) → USB serial → PacketStreamReader → GUI update loop → plot
```

The hardware sends 17-byte packets at 256 Hz (baud rate 115200). `olimex/exg.py::PacketStreamReader` is an iterator that syncs on the `0xa5 0x5a` header, reads each packet, and yields a list of 6 channel values (10-bit ADC, 0–1023). Only channel 1 is used by both GUIs.

Raw values are offset by −512 (centering around zero) before plotting. An optional 50 Hz IIR notch filter (`scipy.signal.iirnotch`) is applied in-place to the rolling buffer before each display update.

### `olimex/` package

Vendored from [olimex-ekg-emg](https://github.com/logston/olimex-ekg-emg), MIT licensed separately (`olimex/LICENSE`):

- `constants.py` — packet format constants (`PACKET_SIZE=17`, `SYNC0/SYNC1` bytes, 6-channel layout)
- `exg.py` — `PacketStreamReader` iterator; returns `None` when the serial buffer has fewer than `PACKET_SIZE−1` bytes (non-blocking)
- `utils.py` — `calculate_values_from_packet_data` converts big-endian uint16 pairs and flips the signal vertically (`val = (val - 1024) * -1`)

### `ekg_viewer.py` — `ECGApp` (PySide6)

- Maintains a rolling `y_data` numpy array of length `T × sampling_rate` (default 10 s × 256 Hz = 2560 samples)
- `QTimer` fires every 50 ms → `update_plot` → `get_new_data_points` drains up to 100 packets per tick via `next(reader, None)`
- New samples are appended via `np.roll` + tail assignment, not by rebuilding the array
- Serial port is opened/closed by Start/Stop buttons; the timer keeps running even when disconnected (safe: guards on `self.reader is None`)
- Save uses `pyqtgraph.exporters.ImageExporter` (PNG only); the matplotlib version saves PDF

### `main.py` — legacy matplotlib/Tk implementation

- Uses `matplotlib.animation.FuncAnimation` at 5 ms interval instead of `QTimer`
- Opens the serial port at module load time (will crash if the port is absent)
- Otherwise functionally equivalent to `ekg_viewer.py`

## Key design constraints

- The `PacketStreamReader.__next__` returns `None` (not raises `StopIteration`) when no data is available — callers must handle `None` channel values.
- Signal values from the hardware are inverted and need the `(val - 1024) * -1` flip in `utils.py`; do not remove this.
- Default COM port is hardcoded to `"COM3"` (Windows). On Linux, the port will be something like `/dev/ttyUSB0` and must be entered in the GUI text field.
