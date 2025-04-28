from datetime import datetime
from matplotlib import pyplot
from matplotlib.widgets import TextBox, CheckButtons
from matplotlib.animation import FuncAnimation
import numpy as np
from olimex.exg import PacketStreamReader
import scipy.signal
import serial
from tkinter.filedialog import asksaveasfilename


# set tk backend for matplotlib
pyplot.switch_backend("TkAgg")


def get_new_data_points(packet_reader: PacketStreamReader):
    """
    Return all data points in the buffer waiting to be displayed.

    In between refreshes of the graph, data points will be
    read into a waiting buffer where they are held before
    they are displayed during the next refresh. The packet
    reader is responsible for managing that buffer.
    """
    new_data = np.empty((100,))

    while True:
        iIteration = 0
        nDataPoints = 0
        while True and iIteration < 100:
            iIteration += 1
            channel_values = next(packet_reader)

            if channel_values:
                channel_1, *_ = channel_values
                # new_data.append(channel_1)
                new_data[nDataPoints] = channel_1
                nDataPoints += 1

        yield new_data[:nDataPoints]


baud_rate = 115200
port: str = "COM3"
serial_port: serial.Serial | None = serial.Serial(port, baud_rate)
reader: PacketStreamReader | None = PacketStreamReader(serial_port)

sampling_rate = 256.0
T = 10.0  # seconds to display
subject: str = "student"


# 50 hz notch filter
def notch_filter(data, sampling_rate: float) -> np.ndarray:
    notch_freq = 50
    f0 = notch_freq / sampling_rate
    Q = 30
    w0 = f0 / 0.5
    b, a = scipy.signal.iirnotch(w0, Q)
    return scipy.signal.filtfilt(b, a, data)


def lowpass_filter(data, sampling_rate: float) -> np.ndarray:
    cutoff = 50
    b, a = scipy.signal.butter(4, cutoff / (sampling_rate / 2), "low")
    return scipy.signal.filtfilt(b, a, data)


y_data = np.random.rand(round(T * sampling_rate))
x_data = np.arange(0, len(y_data)) / sampling_rate


figure, ax = pyplot.subplots()

# maximize figure with tk backend
manager = pyplot.get_current_fig_manager()
if manager is not None:
    manager.window.state("zoomed")


(line,) = ax.plot(x_data, y_data, "k-")

ax.set_xlim(2, 7)
ax.set_ylim(-500, 500)
ax.set_xlabel("Time (s)")
ax.grid(True, which="major", color="k", linestyle="-")
ax.grid(True, which="minor", color="k", linestyle="--")
ax.set_xticks(np.arange(0, T, 0.1), minor=True)

timestamp = datetime.now()
title = ax.set_title(f"{subject} - EKG: {timestamp}")

nFrames = 0


def update(frame):
    global y_data
    global reader
    global nFrames
    global timestamp
    # nFrames += 1

    if reader is None:
        return (line,)

    new_data = np.array(next(get_new_data_points(reader)))

    if len(new_data) == 0:
        return (line,)
    new_data -= 512

    y_data = np.roll(y_data, -len(new_data))

    # if check_buttons.get_status()[1]:
    # y_data = lowpass_filter(y_data, sampling_rate)

    if check_buttons.get_status()[0]:
        y_data = notch_filter(y_data, sampling_rate)

    timestamp = datetime.now()
    y_data[-len(new_data) :] = new_data
    title.set_text(f"{subject} - EKG: {timestamp}")
    line.set_ydata(y_data)
    return (line,)


def on_start(event):
    global serial_port
    global reader
    global animation
    print(f"{datetime.now()}: Started data acqusition")
    serial_port = serial.Serial(port, baud_rate)
    reader = PacketStreamReader(serial_port)
    animation.resume()


def on_stop(event):
    global serial_port
    global reader
    global animation
    print(f"{datetime.now()}: Stopped data acquisition")
    animation.pause()
    serial_port = None
    reader = None


animation = FuncAnimation(figure, update, interval=5, save_count=10)
animation.pause()

# add a button to start and stop the animation
pyplot.subplots_adjust(bottom=0.2)
start_button_axes = pyplot.axes((0.8, 0.05, 0.08, 0.075))
stop_button_axes = pyplot.axes((0.9, 0.05, 0.08, 0.075))
start_button = pyplot.Button(start_button_axes, "Start")
stop_button = pyplot.Button(stop_button_axes, "Stop")

start_button.on_clicked(on_start)
stop_button.on_clicked(on_stop)


# add TextBox to define the COM port
def on_comport_submit_callback(text):
    global port
    port = text


port_slider_axes = pyplot.axes((0.1, 0.05, 0.025, 0.025))
port_text_box = TextBox(
    port_slider_axes, "COM Port  ", initial=port, textalignment="center"
)
port_text_box.on_submit(on_comport_submit_callback)


# add TextBox for Subject
def on_subject_submit(text):
    global subject
    subject = text


subject_axes = pyplot.axes((0.25, 0.05, 0.025, 0.025))
subject_text_box = TextBox(
    subject_axes, "Subject", initial=subject, textalignment="center"
)
subject_text_box.on_submit(on_subject_submit)


# add CheckButtons to select filters
filters = ["50 Hz notch"]
check_axes = pyplot.axes((0.15, 0.05, 0.08, 0.025))
check_buttons = CheckButtons(check_axes, filters, [True, False])


# add button to save as pdf
def on_save(event):
    filename = f"{subject}_ekg_" + timestamp.strftime("%Y%m%d%H%M%S") + ".pdf"

    filename = asksaveasfilename(
        title="Pick filename for saving",
        defaultextension=".pdf",
        initialfile=filename,
        filetypes=[
            ("PDF Files", "*.pdf"),
            ("PNG Files", "*.png"),
            ("All Files", "*.*"),
        ],
    )
    if filename is not None or filename != "":
        pyplot.savefig(filename)
        print(f"{datetime.now()}: Saved figure as {filename}")


save_button_axes = pyplot.axes((0.7, 0.05, 0.08, 0.075))
save_button = pyplot.Button(save_button_axes, "Save figure")
save_button.on_clicked(on_save)

print(f"{datetime.now()}: Started EKG")


pyplot.show()
