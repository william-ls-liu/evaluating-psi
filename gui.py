# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtCore
from PySide6 import QtWidgets
import pyqtgraph as pg
from USB6210 import DAQ

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__(parent=None)
        self.setMinimumSize(QtCore.QSize(900, 900))
        self.setWindowTitle("Balance Lab")
        self.central_widget = QtWidgets.QWidget(parent=self)
        layout = QtWidgets.QVBoxLayout()

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

class Plot(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        # Define the timer parameters
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.update_plot)

        # Define buttons
        self.start_daq_btn = QtWidgets.QPushButton("Start DAQ", parent=self)
        self.start_daq_btn.clicked.connect(self.start_daq)
        
        self.start_stream_btn = QtWidgets.QPushButton("Stream Data", parent=self)
        self.start_stream_btn.clicked.connect(self.start_streaming)
        self.start_stream_btn.setEnabled(False)

        self.stop_stream_btn = QtWidgets.QPushButton("Stop Streaming", parent=self)
        self.stop_stream_btn.clicked.connect(self.stop_streaming)
        self.stop_stream_btn.setEnabled(False)

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
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.start_daq_btn)
        self.layout.addWidget(self.start_stream_btn)
        self.layout.addWidget(self.stop_stream_btn)
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

        # Enable/disable relevant buttons
        self.start_daq_btn.setEnabled(False)
        self.start_stream_btn.setEnabled(True)
        self.stop_stream_btn.setEnabled(True)

    def start_streaming(self):
        self.timer.start()
        self.start_stream_btn.setEnabled(False)

    def stop_streaming(self):
        self.timer.stop()
        self.dev.stop()
        self.dev.close()
        self.task_exists = False

        # Enable/disable relevant buttons
        self.start_daq_btn.setEnabled(True)
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(False)

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


app = QtWidgets.QApplication()
window = MainWindow()
window.show()
app.exec_()
