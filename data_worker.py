# Author: William Liu <liwi@ohsu.edu>

from USB6210 import DAQ
from PySide6.QtCore import QObject, QTimer, Signal, Slot


class DataWorker(QObject):
    """This is a worker to collect data from the NI DAQ and emit the raw data as a signal."""
    data_signal = Signal(list)  # Signal to hold the data from DAQ

    def __init__(self):
        super().__init__()

        # Set-up the timer to sample from the DAQ
        self.sampling_timer = QTimer(parent=self)
        self.sampling_timer.setInterval(1000)
        self.sampling_timer.timeout.connect(self.get_data_from_daq)

        # Initialize the DAQ
        self.DAQ_device = DAQ('Dev1', rate=1)
        self.DAQ_device.create_tasks('ai1:6', 'ai7:8')

        # Store the state of the task
        self.task_is_running = False

    @Slot()
    def get_data_from_daq(self):
        """Read 1 sample/channel from the DAQ."""
        self.data_signal.emit(self.DAQ_device.read())

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
