from datetime import datetime
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation
import numpy as np
from olimex.exg import PacketStreamReader
import scipy.signal
import serial

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
    while True:
        new_data = []

        iIteration = 0
        while True and iIteration < 50:

            iIteration += 1
            try:
                channel_values = next(packet_reader)
            except StopIteration:
                break

            if channel_values:
                channel_1, *_ = channel_values
                new_data.append(channel_1)

        yield new_data


port = "COM3"
serial = serial.Serial(port, 57600)
reader = PacketStreamReader(serial)


print(next(get_new_data_points(reader)))


sampling_rate = 256
T = 10


# 50 hz notch filter
def notch_filter(data, sampling_rate):
    notch_freq = 50
    f0 = notch_freq / sampling_rate
    Q = 30
    w0 = f0 / 0.5
    b, a = scipy.signal.iirnotch(w0, Q)
    return scipy.signal.filtfilt(b, a, data)


def lowpass_filter(data, sampling_rate):
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
# set minor tick distance to 0.1 seconds
ax.set_xticks(np.arange(0, T, 0.1), minor=True)
# ax.set_yticks(np.arange(-500, 501, 100), minor=True)


# ax.minorticks_on()


title = ax.set_title("ECG:")

next(get_new_data_points(reader))


def update(frame):
    global y_data
    new_data = np.array(next(get_new_data_points(reader)))
    # new_data = np.random.randn(100) * 100 + 500
    if len(new_data) == 0:
        return (line,)
    new_data -= 512

    y_data = np.roll(y_data, -len(new_data))
    y_data = notch_filter(y_data, sampling_rate)
    # y_data = lowpass_filter(y_data, sampling_rate)

    y_data[-len(new_data) :] = new_data
    title.set_text(f"ECG: {datetime.now()}, n={len(new_data)}")
    line.set_ydata(y_data)
    return (line,)


animation = FuncAnimation(figure, update, interval=20, save_count=10)
animation.pause()


# add a button to start and stop the animation
pyplot.subplots_adjust(bottom=0.2)
start_button_axes = pyplot.axes((0.8, 0.05, 0.1, 0.075))
stop_button_axes = pyplot.axes((0.9, 0.05, 0.1, 0.075))
start_button = pyplot.Button(start_button_axes, "Start")
stop_button = pyplot.Button(stop_button_axes, "Stop")

start_button.on_clicked(lambda evemt: animation.resume())
stop_button.on_clicked(lambda evemt: animation.pause())

# button.on_clicked(lambda event: animation.resume())

pyplot.show()
