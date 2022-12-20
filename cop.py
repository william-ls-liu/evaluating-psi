# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg
from USB6210 import DAQ
import numpy as np
from sounds import Countdown
from progress_widget import ProgressWidget
from data_viewer import GraphWindow
import csv
from datetime import datetime


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__(parent=None)
        self.setWindowTitle("PSI Data Collection Software")

        # Central widget to serve as contains for other widgets
        self.cw = QtWidgets.QWidget(parent=self)
        layout = QtWidgets.QHBoxLayout()

        # Add the PlotWidget to layout
        self.pw = PlotWidget(self)
        layout.addWidget(self.pw)

        # Add the ProgressWidget to the layout
        self.progress_widget = ProgressWidget(self)
        layout.addWidget(self.progress_widget)

        # Connect the status signal to the progress widget
        self.pw.status_signal.connect(self.progress_widget.update_progress_label)

        # Connect the enable stimulus signal to the plot widget
        self.progress_widget.enable_stimulus_signal.connect(self.pw.set_stimulus_state)
        self.pw.set_stimulus_state(self.progress_widget.enable_stimulus_checkbox.isChecked())

        # Connect the threshold slider signal to set the APA threshold
        self.progress_widget.threshold_slider.valueChanged.connect(self.pw.set_threshold_value)
        self.pw.set_threshold_value(self.progress_widget.threshold_slider.value())  # Set the default value

        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)

    def closeEvent(self, event):
        """Override the closeEvent method to ensure active task on DAQ is closed."""
        if self.pw.task_exists:
            self.pw.stop()

        event.accept()


class PlotWidget(QtWidgets.QWidget):
    # Signal to report on the status of the protocol
    status_signal = QtCore.Signal(str)

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        # Set-up QTimer to initiate reads from the DAQ
        self.timer = QtCore.QTimer(parent=self)
        # An interval of 0 means the timer will timeout as soon as all events in the queue have been processed
        # This is basically running the timer as fast as possible, and will tie the software timer to the hardware
        # timer on the DAQ, which is very accurate and fast.
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.read_daq)

        # Initiate a timer for the streaming plot
        self.plot_timer = QtCore.QTimer(parent=self)
        self.plot_timer.setInterval(16.66)  # ~60Hz since drawing new graphs is resource-intensive
        self.plot_timer.timeout.connect(self.update_plot)

        # Initiate a timer for the protocol
        self.protocol_timer = QtCore.QTimer(parent=self)
        self.protocol_timer.setInterval(0)
        self.protocol_timer.timeout.connect(self.protocol)

        # Define buttons
        self.start_daq_btn = QtWidgets.QPushButton("Start DAQ", parent=self)
        self.start_daq_btn.clicked.connect(self.start_daq)

        self.start_stream_btn = QtWidgets.QPushButton("Stream Data", parent=self)
        self.start_stream_btn.clicked.connect(self.start_streaming)
        self.start_stream_btn.setEnabled(False)

        self.stop_stream_btn = QtWidgets.QPushButton("Stop", parent=self)
        self.stop_stream_btn.clicked.connect(self.stop)
        self.stop_stream_btn.setEnabled(False)

        self.start_protocol_btn = QtWidgets.QPushButton("Start Protocol", parent=self)
        self.start_protocol_btn.clicked.connect(self.start_protocol)

        self.stop_protocol_btn = QtWidgets.QPushButton("Stop Protocol", parent=self)
        self.stop_protocol_btn.clicked.connect(self.stop_protocol)
        self.stop_protocol_btn.setEnabled(False)

        # Define variables for storing data and plotting
        samples_to_show = 2000
        self.samples = [i for i in range(samples_to_show)]
        self.raw = list()  # A list of np.arrays storing the raw data from every channel read
        self.emg_tib = [0 for i in range(samples_to_show)]
        self.emg_soleus = [0 for i in range(samples_to_show)]
        self.Fz = [0 for i in range(samples_to_show)]
        self.copX = []
        self.copY = []
        self.subplots = dict()

        # Create the subplots
        self.plot_widget = self.build_subplots()

        # Initiate variable to store the state of the task
        self.task_exists = False

        # Initiate variable to store whether stimulus has been triggerd
        self.stim_triggered = False

        # Set the layout for the buttons
        self.btn_layout = QtWidgets.QGridLayout()
        self.btn_layout.addWidget(self.start_daq_btn, 0, 0)
        self.btn_layout.addWidget(self.start_stream_btn, 1, 0)
        self.btn_layout.addWidget(self.stop_stream_btn, 2, 0)
        self.btn_layout.addWidget(self.start_protocol_btn, 0, 1)
        self.btn_layout.addWidget(self.stop_protocol_btn, 1, 1)

        # Set the layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.plot_widget)
        self.layout.addLayout(self.btn_layout)
        self.setLayout(self.layout)

    def build_subplots(self):
        """Create subplots for the EMG and CoP graphs."""
        pg_layout = pg.GraphicsLayoutWidget()

        # Create the CoP plot
        cop_plotItem = pg_layout.addPlot(row=0, col=0, title="Center of Pressure (m)")
        cop_plotItem.setRange(xRange=(-0.254, 0.254), yRange=(-0.254, 0.254))
        cop_plotItem.disableAutoRange(axis='xy')  # Disable automatic adjustment of axes ranges
        cop_plotItem.invertX(b=True)  # AMTI axis definitions mean the +X is actually on the left of the graph
        cop_plotLine = cop_plotItem.plot(x=[0], y=[0], pen=None, symbol='o')
        self.subplots['cop'] = cop_plotLine

        # Create plot for the Fz
        Fz_plotItem = pg_layout.addPlot(row=1, col=0, title="Fz (N)")
        Fz_plotLine = Fz_plotItem.plot(x=self.samples, y=self.Fz)
        self.subplots['Fz'] = Fz_plotLine

        # Create plots for the two EMG channels
        emg_tib_plotItem = pg_layout.addPlot(row=0, col=1, title="EMG: Tibial")
        emg_tib_plotItem.setRange(yRange=(-2.5, 2.5))
        emg_tib_plotItem.disableAutoRange(axis='y')  # Disable just the y axis, so data still scrolls
        emg_tib_plotLine = emg_tib_plotItem.plot(x=self.samples, y=self.emg_tib)
        self.subplots['tib'] = emg_tib_plotLine

        emg_soleus_plotItem = pg_layout.addPlot(row=1, col=1, title="EMG: Soleus")
        emg_soleus_plotItem.setRange(yRange=(-2.5, 2.5))
        emg_soleus_plotItem.disableAutoRange(axis='y')
        emg_soleus_plotLine = emg_soleus_plotItem.plot(x=self.samples, y=self.emg_soleus)
        self.subplots['soleus'] = emg_soleus_plotLine

        return pg_layout

    def start_daq(self):
        """Create the DAQ task."""
        self.dev = DAQ('Dev1')
        self.sample_rate = self.dev.get_sample_rate()
        self.dev.create_tasks('ai1:6', 'ai7:8')
        self.dev.start()
        self.task_exists = True

        # Enable/disable relevant buttons
        self.start_daq_btn.setEnabled(False)
        self.start_stream_btn.setEnabled(True)
        self.stop_stream_btn.setEnabled(True)
        self.start_protocol_btn.setEnabled(False)

    def start_streaming(self):
        """Start streaming the data from the DAQ."""
        self.timer.start()
        self.plot_timer.start()
        self.start_stream_btn.setEnabled(False)
        self.start_protocol_btn.setEnabled(False)

    def stop(self):
        """Stop the stream of data, clear the DAQ task, and remove DAQ device from memory."""
        self.timer.stop()
        self.protocol_timer.stop()
        self.plot_timer.stop()
        self.dev.stop()
        self.dev.close()
        del self.dev
        self.task_exists = False

        # Enable/disable relevant buttons
        self.start_daq_btn.setEnabled(True)
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(False)
        self.start_protocol_btn.setEnabled(True)

    def read_daq(self):
        """Method to read the DAQ and convert data to CoP."""
        data = self.dev.read()
        self.raw.append(data)

        # Calculate the Center of Pressure
        copX = -1 * ((data[4] + (-0.040934 * data[0])) / data[2])
        self.copX.append(copX)
        copY = (data[3] - (-0.040934 * data[1])) / data[2]
        self.copY.append(copY)

        # Add Fz to the plot
        self.Fz = self.Fz[1:]
        self.Fz.append(data[2])

        # Add EMG data for the plot
        self.emg_soleus = self.emg_soleus[1:]
        self.emg_tib = self.emg_tib[1:]
        self.emg_soleus.append(data[6])
        self.emg_tib.append(data[7])

        # Remove data points to conserve memory
        if len(self.copX) > 60000:
            self.copX.pop(0)
            self.copY.pop(0)
            self.raw.pop(0)

    def update_plot(self):
        """
        Update the plot with the most recent data. The plot updates slower than data is read
        because the data acquisiton rate is much higher than would be suitable for drawing graphics
        on the screen.
        """
        self.subplots['cop'].setData(x=[self.copX[-1]], y=[self.copY[-1]])
        self.subplots['Fz'].setData(x=self.samples, y=self.Fz)
        self.subplots['soleus'].setData(x=self.samples, y=self.emg_soleus)
        self.subplots['tib'].setData(x=self.samples, y=self.emg_tib)

    def protocol(self):
        """Read the DAQ and compare CoP values to the threshold for APA."""
        # Read the voltage from the DAQ
        data = self.dev.read()
        self.raw.append(data)

        # Calculate the Center of Pressure
        copX = -1 * ((data[4] + (-0.040934 * data[0])) / data[2])
        self.copX.append(copX)
        copY = (data[3] - (-0.040934 * data[1])) / data[2]
        self.copY.append(copY)

        # Add Fz to the plot
        self.Fz = self.Fz[1:]
        self.Fz.append(data[2])

        # Add EMG data for the plot
        self.emg_soleus = self.emg_soleus[1:]
        self.emg_tib = self.emg_tib[1:]
        self.emg_soleus.append(data[6])
        self.emg_tib.append(data[7])

        if copX > self.cop_upper or copX < self.cop_lower:
            if not self.stim_triggered:
                if self.enable_stimulus:
                    self.dev.ttl()  # Trigger the TTL output
                    self.stim_triggered = True
                    self.status_signal.emit("APA detected. Stimulus was delivered.")
                    self.stop_protocol_btn.setEnabled(True)

    def start_protocol(self):
        """Start the PSI collection protocol. Begin with 10s of quiet stance to capture baseline sway."""
        # Disable all other buttons while protocol is running
        self.start_protocol_btn.setEnabled(False)
        self.start_daq_btn.setEnabled(False)
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(False)

        # Reset all the variables used to store data
        self.copX.clear()
        self.copY.clear()
        self.raw.clear()

        # Ensure the lists to store the data are definitely empty
        if self.raw:
            raise ValueError("The list to store the raw data is not empty.")
        elif self.copX:
            raise ValueError("The list to store the CoP X is not empty.")
        elif self.copY:
            raise ValueError("The list to store the CoP Y is not empty.")

        # Create the sound effect, connect the end of the effect to initiating the protocol
        sound = Countdown(self)
        sound.play()
        sound.playingChanged.connect(self._baseline_helper)

    def _baseline_helper(self):
        """Helper method to initiate the protocol recording after the sound effect has finished."""
        # Emit a signal to update the progress window
        self.status_signal.emit("Collecting baseline")

        baseline_timer = QtCore.QTimer(parent=self)
        baseline_timer.setInterval(10000)  # 10 secs
        baseline_timer.setSingleShot(True)
        baseline_timer.timeout.connect(self.stop)
        baseline_timer.timeout.connect(self.baseline_cop)

        # Start the device, the 10s timer, and the data stream
        self.start_daq()
        baseline_timer.start()
        self.start_streaming()
        self.stop_stream_btn.setEnabled(False)

    def baseline_cop(self):
        """Calculate the baseline CoP sway, then start the protocol data collection."""
        self.status_signal.emit("Baseline Center of Pressure has been collected. Patient can now take a step.")
        origin = np.mean(self.copX)
        stdev = np.std(self.copX)
        sd = self.apa_threshold * stdev

        self.cop_upper = origin + sd
        self.cop_lower = origin - sd

        # Reset all the variables used to store data
        self.copX.clear()
        self.copY.clear()
        self.raw.clear()

        self._protocol_helper()

    def _protocol_helper(self):
        # Start the protocol streaming
        self.start_daq()
        self.start_daq_btn.setEnabled(False)
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(False)
        self.protocol_timer.start()
        self.plot_timer.start()

    def stop_protocol(self):
        """Handle the clean-up required to stop the protocol, provide user with option to save the data to .csv."""
        # Stop the DAQ Task
        self.stop()
        self.start_protocol_btn.setEnabled(True)
        self.stim_triggered = False
        self.stop_protocol_btn.setEnabled(False)

        # Open a save file dialog window
        fname = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Select a location to save the data.",
            filter="*.csv"
        )

        # If user selects Cancel or doesn't enter a filename don't save a file
        if fname[0] != '':
            to_csv = self.create_export_file()
            file = open(fname[0], 'w+', newline='')
            with file:
                write = csv.writer(file)
                write.writerows(to_csv)

        # Open the graph window
        raw_as_array = np.array(self.raw)
        self.gw = GraphWindow(
            {
                'CopX': self.copX,
                'CopY': self.copY,
                'Fz': raw_as_array[:, 2],
                'EMG Soleus': raw_as_array[:, 6],
                'EMG Tibialis': raw_as_array[:, 7]
            }
        )
        self.gw.show()

    def create_export_file(self):
        """This method will format the raw data for export to csv."""
        date_of_export = str(datetime.today())
        raw = self.raw.copy()

        export = [
            ["Date of Export:", date_of_export],
            ['Sample Rate:', self.sample_rate],
            ['Fx (N)', 'Fy (N)', 'Fz (N)', 'Mx (N/m)', 'My (N/m)', 'Mz (N/m)', 'CoP X (m)', 'CoP Y (m)', 'EMG1', 'EMG2']
        ]

        for row in raw:
            copX = (-1) * ((row[4] + (-0.040934 * row[0])) / row[2])
            copY = ((row[3] - (-0.040934 * row[1])) / row[2])
            new_row = [row[0], row[1], row[2], row[3], row[4], row[5], copX, copY, row[6], row[7]]
            export.append(new_row)

        return export

    def set_stimulus_state(self, state):
        """Connected to the checkbox in the progress widget which enables/disables the stimulus."""
        self.enable_stimulus = state

    def set_threshold_value(self, value):
        """
        Connected to the int slider in the progress widget to set the APA threshold.
        APA threshold = value * standard deviation of baseline CoP
        """
        self.apa_threshold = value


app = QtWidgets.QApplication()
window = MainWindow()
window.showMaximized()
window.show()
app.exec()
