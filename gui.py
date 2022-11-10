import PySide2
from PySide2 import QtCore
from PySide2.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QVBoxLayout
from PySide2.QtGui import *
import pyqtgraph as pg
from USB6210 import DAQ
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(parent=None)
        self.setMinimumSize(QtCore.QSize(400, 300))
        self.setWindowTitle("Balance Lab")
        self.central_widget = QWidget(parent=self)
        layout = QVBoxLayout()

        self.graph = Plot(self)
        layout.addWidget(self.graph)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)
    
    def closeEvent(self, event):
        """Override closeEvent method to ensure the active task on the DAQ, if there was one, was closed
        safely."""
        if self.graph.task_exists:
            self.graph.dev.close()
            event.accept()
        else:
            event.accept()

class Plot(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        # Define the timer parameters
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.update_plot)

        # Define buttons
        self.start_daq_button = QPushButton("Start", parent=self)
        self.start_daq_button.clicked.connect(self.start_daq)
        self.start_rec_button = QPushButton("Record", parent=self)
        self.start_rec_button.clicked.connect(self.start_recording)
        self.stop_rec_button = QPushButton("Stop", parent=self)
        self.stop_rec_button.clicked.connect(self.stop_recording)

        # Define variables for plotting
        samples_to_show = 250
        self.channel_data = {
            'Fx': [0 for i in range(samples_to_show)],
            'Fy': [0 for i in range(samples_to_show)],
            'Fz': [0 for i in range(samples_to_show)],
            'Mx': [0 for i in range(samples_to_show)],
            'My': [0 for i in range(samples_to_show)],
            'Mz': [0 for i in range(samples_to_show)]
        }
        self.time = [i for i in range(samples_to_show)]
        self.subplots = dict()

        # Build the subplots
        self.plot_widget = self.build_subplots()

        # Initiate variable to store the state of the task
        self.task_exists = False
        
        # Set the layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.start_daq_button)
        self.layout.addWidget(self.start_rec_button)
        self.layout.addWidget(self.stop_rec_button)
        self.setLayout(self.layout)

    def build_subplots(self):
        pg_layout = pg.GraphicsLayoutWidget()
        for idx, ch in enumerate(self.channel_data.keys()):
            plot_item = pg_layout.addPlot(row=idx - idx%2, col=idx%2, title=ch)
            plot_line = plot_item.plot(x=self.time, y=self.channel_data[ch])
            self.subplots[ch] = plot_line

        return pg_layout

    def start_daq(self):
        self.dev = DAQ('Dev1')
        self.dev.create_task('ai1:6')
        self.dev.start()
        self.task_exists = True

    def start_recording(self):
        self.timer.start()

    def stop_recording(self):
        self.timer.stop()
        self.dev.stop()
        self.dev.close()
        self.task_exists = False

    def update_plot(self):
        # Read the voltage from the DAQ
        data = self.dev.read()
        # Update the time array
        self.time = self.time[1:]
        self.time.append(self.time[-1] + 1)
        for idx, ch in enumerate(self.subplots.keys()):
            self.channel_data[ch] = self.channel_data[ch][1:]
            self.channel_data[ch].append(data[idx])
            self.subplots[ch].setData(x=self.time, y=self.channel_data[ch])


app = QApplication()
window = MainWindow()
window.show()
app.exec_()
