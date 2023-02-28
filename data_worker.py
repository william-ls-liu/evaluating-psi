# Author: William Liu <liwi@ohsu.edu>

from USB6210 import DAQ
from PySide6.QtCore import QObject, QTimer, Signal, Slot, Qt
import numpy as np
import json


class DataWorker(QObject):
    """
    This is a worker to collect data from the NI DAQ and emit the raw data as a signal.

    Attributes
    ----------
    data_signal : PySide6.QtCore.Signal(np.ndarray)
        a signal of array-like data to be emitted
    sample_rate : int
        hardware sample rate for the DAQ in Hz
    sampling_timer : PySide6.QtCore.QTimer
        timer to acquire data from DAQ
    DAQ_device : USB6210.DAQ
        instance of National Instruments USB6210 Data Acquisition Device
    task_is_running : bool
        the state of the DAQ task, running (True) or not running (False)

    Methods
    -------
    read_settings_file()
        Read the JSON file of settings.
    get_data_from_daq()
        A Slot connected to timeout of sampling_timer. Read DAQ_device, calculate the center of pressure (CoP),
        add CoP to array of raw data, and emit data_signal.
    start_sampling()
        A Slot. Start sampling_timer and DAQ_device if task is not running
    stop_sampling()
        A Slot. If task is running, stop DAQ_device and sampling_timer
    shutdown()
        A Slot. Ensure graceful termination of sampling_timer and DAQ_device
    """

    data_signal = Signal(np.ndarray)  # Signal to hold the data from DAQ

    def __init__(self):
        super().__init__()

        # Read the settings file and get the sample rate
        self.sample_rate = self.read_settings_file()

        # Set-up the timer to sample from the DAQ
        self.sampling_timer = QTimer(parent=self)
        self.sampling_timer.setTimerType(Qt.PreciseTimer)
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
        """Read 1 sample per channel from the DAQ."""
        data = self.DAQ_device.read()
        self.data_signal.emit(data)

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
    def ttl(self):
        """Trigger the TTL output."""
        self.DAQ_device.ttl()

    @Slot()
    def shutdown(self):
        """This methods handles the termination of the DAQ processes."""
        if self.task_is_running:
            self.stop_sampling()
        self.DAQ_device.close()
