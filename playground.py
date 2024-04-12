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
        while True:
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


y_data = np.random.rand(round(T * sampling_rate))
x_data = np.arange(0, len(y_data)) / sampling_rate


figure, ax = pyplot.subplots()

# maximize figure with tk backend
manager = pyplot.get_current_fig_manager()
if manager is not None:
    manager.window.state("zoomed")


(line,) = ax.plot(x_data, y_data, "-")

ax.set_xlim(0, T)
ax.set_ylim(-500, 500)
ax.set_xlabel("Time (s)")
ax.grid(True)
title = ax.set_title("ECG:")

next(get_new_data_points(reader))


def update(frame):
    global y_data
    new_data = np.array(next(get_new_data_points(reader)))
    # if new_data.size == 0:
    #    return (line,)
    new_data -= 512
    y_data = np.roll(y_data, -len(new_data))
    # y_data = notch_filter(y_data, sampling_rate)
    y_data[-len(new_data) :] = new_data
    title.set_text(f"ECG: {datetime.now()}, n={len(new_data)}")
    line.set_ydata(y_data)
    return


animation = FuncAnimation(figure, update, interval=15, save_count=10)
pyplot.show()
