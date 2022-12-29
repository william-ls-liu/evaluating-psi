# Author: William Liu <liwi@ohsu.edu>

from USB6210 import DAQ
from PySide6.QtCore import QObject, QTimer, Signal, Slot
import numpy as np
import json


class DataWorker(QObject):
    """This is a worker to collect data from the NI DAQ and emit the raw data as a signal."""
    data_signal = Signal(np.ndarray)  # Signal to hold the data from DAQ

    def __init__(self):
        super().__init__()

        # Read the settings file and get the sample rate
        self.sample_rate = self.read_settings_file()

        # Set-up the timer to sample from the DAQ
        self.sampling_timer = QTimer(parent=self)
        self.sampling_timer.setInterval(0)
        self.sampling_timer.timeout.connect(self.get_data_from_daq)

        # Initialize the DAQ
        self.DAQ_device = DAQ('Dev1', rate=self.sample_rate)
        self.DAQ_device.create_tasks('ai1:6', 'ai7:8')

        # Store the state of the task
        self.task_is_running = False

    def read_settings_file(self):
        """Read the settings file to get the sample rate."""
        with open("amti_settings.json", 'r') as file:
            settings = json.load(file)

        sample_rate = settings["sample_rate"]

        return sample_rate

    @Slot()
    def get_data_from_daq(self):
        """Read 1 sample/channel from the DAQ. Calculate the CoP and add that to the array that is emitted."""
        data = self.DAQ_device.read()
        copx = -1 * ((data[4] + (-0.040934 * data[0])) / data[2])
        copy = (data[3] - (-0.040934 * data[1])) / data[2]
        data_to_emit = np.append(data, [copx, copy])
        self.data_signal.emit(data_to_emit)

    @Slot()
    def start_sampling(self):
        """Start the sampling timer and begin acquiring data."""
        if not self.task_is_running:
            self.task_is_running = True
            self.DAQ_device.start()
            self.sampling_timer.start()

    @Slot()
    def stop_sampling(self):
        """Stop the sampling timer."""
        if self.task_is_running:
            self.DAQ_device.stop()
            self.sampling_timer.stop()
            self.task_is_running = False

    @Slot()
    def shutdown(self):
        """This methods handles the termination of the DAQ processes."""
        if self.task_is_running:
            self.stop_sampling()
        self.DAQ_device.close()
