# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg
from USB6210 import DAQ

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__(parent=None)
        self.setWindowTitle("PSI Data Collection Software")

        # Central widget to serve as contains for other widgets
        self.cw = QtWidgets.QWidget(parent=self)
        layout = QtWidgets.QVBoxLayout()

        # Add the PlotWidget to layout
        self.pw = PlotWidget(self)
        layout.addWidget(self.pw)

        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)

    def closeEvent(self, event):
        """Override the closeEvent method to ensure active task on DAQ is closed."""
        if self.pw.task_exists:
            self.pw.dev.close()

        event.accept()

class PlotWidget(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        # Set-up QTimer to initiate reads from the DAQ
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.update_plot)

        # Define buttons
        self.start_daq_btn = QtWidgets.QPushButton("Start DAQ", parent=self)
        self.start_daq_btn.clicked.connect(self.start_daq)
        
        self.start_stream_btn = QtWidgets.QPushButton("Stream Data", parent=self)
        self.start_stream_btn.clicked.connect(self.start_streaming)
        self.start_stream_btn.setEnabled(False)

        self.stop_stream_btn = QtWidgets.QPushButton("Stop", parent=self)
        self.stop_stream_btn.clicked.connect(self.stop)
        self.stop_stream_btn.setEnabled(False)

        # Define variables for storing data and plotting
        samples_to_show = 250
        self.time = [i for i in range(samples_to_show)]
        self.raw = list()  # A list of np.arrays storing the raw data from every channel read
        self.emg_tib = [0 for i in range(samples_to_show)]
        self.emg_soleus = [0 for i in range(samples_to_show)]
        self.copX = []
        self.copY = []
        self.subplots = dict()

        # Create the subplots
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
        """Create subplots for the EMG and CoP graphs."""
        pg_layout = pg.GraphicsLayoutWidget()

        # Create the CoP plot
        cop_plotItem = pg_layout.addPlot(row=0, col=0, title="Center of Pressure")
        cop_plotItem.setRange(xRange=(-0.254, 0.254), yRange=(-0.254, 0.254))
        cop_plotItem.disableAutoRange(axis='xy')  # Disable automatic adjustment of axes ranges
        cop_plotItem.invertX(b=True)  # AMTI axis definitions mean the +X is actually on the left of the graph
        cop_plotLine = cop_plotItem.plot(x=[0], y=[0], pen=None, symbol='o')
        self.subplots['cop'] = cop_plotLine

        # Create plots for the two EMG channels
        emg_tib_plotItem = pg_layout.addPlot(row=0, col=1, title="EMG: Tibial")
        emg_tib_plotItem.setRange(yRange=(-2.5, 2.5))
        emg_tib_plotItem.disableAutoRange(axis='y')  # Disable just the y axis, so data still scrolls
        emg_tib_plotLine = emg_tib_plotItem.plot(x=self.time, y=self.emg_tib)
        self.subplots['tib'] = emg_tib_plotLine

        emg_soleus_plotItem = pg_layout.addPlot(row=1, col=1, title="EMG: Soleus")
        emg_soleus_plotItem.setRange(yRange=(-2.5, 2.5))
        emg_soleus_plotItem.disableAutoRange(axis='y')
        emg_soleus_plotLine = emg_soleus_plotItem.plot(x=self.time, y=self.emg_soleus)
        self.subplots['soleus'] = emg_soleus_plotLine

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

    def stop(self):
        """Stop the stream of data, clear the DAQ task, and remove DAQ device from memory."""
        self.timer.stop()
        self.dev.stop()
        self.dev.close()
        del self.dev
        self.task_exists = False

        # Enable/disable relevant buttons
        self.start_daq_btn.setEnabled(True)
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(False)

    def update_plot(self):
        # Read the voltage from the DAQ
        data = self.dev.read()
        self.raw.append(data)

        # Calculate the Center of Pressure
        copX = -1 * ((data[4] + (-0.040934 * data[0])) / data[2])
        self.copX.append(copX)
        copY = (data[3] - (-0.040934 * data[1])) / data[2]
        self.copY.append(copY)

        # Update the plot
        self.subplots['cop'].setData(x=[self.copX[-1]], y=[self.copY[-1]])


app = QtWidgets.QApplication()
window = MainWindow()
window.show()
app.exec_()
