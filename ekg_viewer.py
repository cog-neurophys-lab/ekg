import sys
from matplotlib import axis
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QLabel,
    QFileDialog,
    QWidget,
)
from PySide6.QtCore import QTimer
import pyqtgraph as pg

from pyqtgraph import PlotWidget, mkPen
from olimex.exg import PacketStreamReader
import scipy.signal
import serial
from PySide6.QtWidgets import QHBoxLayout


class ECGApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECG Viewer with PyQtGraph")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize variables
        self.baud_rate = 115200
        self.port = "COM3"
        self.serial_port = None
        self.reader = None
        self.sampling_rate = 256.0
        self.T = 10.0  # seconds to display
        self.subject = "student"
        self.y_data = np.random.rand(round(self.T * self.sampling_rate)) - 0.5
        self.x_data = np.arange(0, len(self.y_data)) / self.sampling_rate
        self.notch_filter_enabled = True

        # Set up the main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Add the plot widget
        self.plot_widget = PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.plot = self.plot_widget.plot(
            self.x_data, self.y_data, pen=mkPen("w", width=2)
        )
        self.plot_widget.setLabel("left", "Amplitude")
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.setYRange(-500, 500)
        self.plot_widget.setXRange(2, 7)

        # Add control buttons and inputs
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)
        button_layout.addWidget(self.stop_button)

        self.layout.addLayout(button_layout)

        self.save_button = QPushButton("Save Figure")
        self.save_button.clicked.connect(self.save_figure)
        self.layout.addWidget(self.save_button)

        self.com_port_input = QLineEdit(self.port)
        self.com_port_input.setPlaceholderText("COM Port")
        self.com_port_input.textChanged.connect(self.update_com_port)
        self.layout.addWidget(self.com_port_input)

        self.subject_input = QLineEdit(self.subject)
        self.subject_input.setPlaceholderText("Subject")
        self.subject_input.textChanged.connect(self.update_subject)
        self.layout.addWidget(self.subject_input)

        # Add sliders for x limits and y limits
        axis_layout = QHBoxLayout()

        self.x_min_slider = QLineEdit("2")
        self.x_min_slider.setPlaceholderText("X Min")
        self.x_min_slider.textChanged.connect(self.update_x_limits)
        axis_layout.addWidget(self.x_min_slider)

        self.x_max_slider = QLineEdit("7")
        self.x_max_slider.setPlaceholderText("X Max")
        self.x_max_slider.textChanged.connect(self.update_x_limits)
        axis_layout.addWidget(self.x_max_slider)

        self.y_min_slider = QLineEdit("-500")
        self.y_min_slider.setPlaceholderText("Y Min")
        self.y_min_slider.textChanged.connect(self.update_y_limits)
        axis_layout.addWidget(self.y_min_slider)

        self.y_max_slider = QLineEdit("500")
        self.y_max_slider.setPlaceholderText("Y Max")
        self.y_max_slider.textChanged.connect(self.update_y_limits)
        axis_layout.addWidget(self.y_max_slider)

        self.layout.addLayout(axis_layout)

        self.notch_filter_checkbox = QCheckBox("50 Hz Notch Filter")
        self.notch_filter_checkbox.setChecked(self.notch_filter_enabled)
        self.notch_filter_checkbox.stateChanged.connect(self.toggle_notch_filter)
        self.layout.addWidget(self.notch_filter_checkbox)

        # Timer for updating the plot
        self.timer = QTimer(self)  # Create a QTimer instance
        self.timer.timeout.connect(
            self.update_plot
        )  # Connect the timer to the update_plot method
        self.timer.start(
            50
        )  # Set the timer interval to 50 ms (adjust as needed for your data rate)

        self.update_subject("Student")

    def update_x_limits(self):
        try:
            x_min = float(self.x_min_slider.text())
            x_max = float(self.x_max_slider.text())
            if x_min < x_max:
                self.plot_widget.setXRange(x_min, x_max)
        except ValueError:
            print("Invalid X range values")

    def update_y_limits(self):
        try:
            y_min = float(self.y_min_slider.text())
            y_max = float(self.y_max_slider.text())
            if y_min < y_max:
                self.plot_widget.setYRange(y_min, y_max)
        except ValueError:
            print("Invalid Y range values")

    def start_acquisition(self):
        try:
            self.serial_port = serial.Serial(self.port, self.baud_rate)
            self.reader = PacketStreamReader(self.serial_port)
            print(f"{datetime.now()}: Started data acquisition")
        except Exception as e:
            print(f"Error starting acquisition: {e}")

    def stop_acquisition(self):
        if self.serial_port:
            self.serial_port.close()
        self.serial_port = None
        self.reader = None
        print(f"{datetime.now()}: Stopped data acquisition")

    def save_figure(self):
        import pyqtgraph.exporters

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Figure",
            f"{self.subject}_ekg_{datetime.now().strftime('%Y%m%d%H%M%S')}.png",
            "PNG Files (*.png);;All Files (*)",
        )
        if filename:
            exporter = pyqtgraph.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(filename)
            print(f"{datetime.now()}: Saved figure as {filename}")

    def update_com_port(self, text):
        self.port = text

    def update_subject(self, text):
        self.subject = text
        self.plot_widget.plotItem.setTitle(f"ECG Viewer - Subject: {self.subject}")

    def toggle_notch_filter(self, state):
        self.notch_filter_enabled = state == 2

    def notch_filter(self, data):
        notch_freq = 50
        f0 = notch_freq / self.sampling_rate
        Q = 30
        w0 = f0 / 0.5
        b, a = scipy.signal.iirnotch(w0, Q)
        return scipy.signal.filtfilt(b, a, data)

    def update_plot(self):
        if self.reader is None or not hasattr(self.reader, "__iter__"):
            return

        try:
            new_data = np.array(next(self.get_new_data_points(self.reader)))
            if len(new_data) == 0:
                return
            new_data -= 512
            self.y_data = np.roll(self.y_data, -len(new_data))
            if self.notch_filter_enabled:
                self.y_data = self.notch_filter(self.y_data)
            self.y_data[-len(new_data) :] = new_data
            self.plot.setData(self.x_data, self.y_data)
        except Exception as e:
            print(f"Error updating plot: {e}")

    def get_new_data_points(self, packet_reader):
        new_data = np.empty((100,))
        while True:
            iIteration = 0
            nDataPoints = 0
            while iIteration < 100:
                iIteration += 1
                channel_values = next(packet_reader, None)
                if channel_values:
                    channel_1, *_ = channel_values
                    new_data[nDataPoints] = channel_1
                    nDataPoints += 1
            yield new_data[:nDataPoints]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ECGApp()
    window.show()
    sys.exit(app.exec_())
