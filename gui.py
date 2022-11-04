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
        self.button = QPushButton("Press me!")
        layout = QVBoxLayout()
        layout.addWidget(self.button)

        self.graph = Plot(self)
        layout.addWidget(self.graph)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

class Plot(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        # Define the timer parameters
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot)

        # Define buttons
        self.start_daq_button = QPushButton("Start", parent=self)
        self.start_daq_button.clicked.connect(self.start_daq)
        self.start_rec_button = QPushButton("Record", parent=self)
        self.start_rec_button.clicked.connect(self.start_recording)
        self.stop_rec_button = QPushButton("Stop", parent=self)
        self.stop_rec_button.clicked.connect(self.stop_recording)

        # Define variables for plotting
        self.x = [i for i in range(1000)]
        self.y = [0 for i in range(1000)]
        self.pw = pg.PlotWidget(parent=self)
        self.data_line = self.pw.plot(self.x, self.y)

        # Set the layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.pw)
        self.layout.addWidget(self.start_daq_button)
        self.layout.addWidget(self.start_rec_button)
        self.layout.addWidget(self.stop_rec_button)
        self.setLayout(self.layout)

    def start_daq(self):
        self.dev = DAQ('Dev1')
        self.dev.create_task('ai0')
        self.dev.start()

    def start_recording(self):
        self.timer.start()

    def stop_recording(self):
        self.timer.stop()
        self.dev.stop()
        self.dev.close()

    def update_plot(self):
        self.y = self.y[1:]
        self.y.append(self.dev.read())
        self.x = self.x[1:]
        self.x.append(self.x[-1] + 1)
        self.data_line.setData(self.x, self.y)


app = QApplication()
window = MainWindow()
window.show()
app.exec_()
