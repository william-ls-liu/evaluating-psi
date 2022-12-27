# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from plot_widget import PlotWidget
from data_worker import DataWorker
from protocol_widget import ProtocolWidget


class MainWindow(QMainWindow):
    """This class represents the main window of the GUI."""

    shutdown_signal = Signal()  # Signal to be emitted when the window is closed

    def __init__(self) -> None:
        super().__init__(parent=None)

        # Set the title
        self.setWindowTitle("PSI Data Collection Software")

        # A MainWindow needs a central widget to serve as a container for all other widgets
        self.central_widget = QWidget(parent=self)

        # Add the control buttons
        self.control_bar = ControlBar(self)

        # Add plot widget
        self.plot_widget = PlotWidget(self)

        # Create the DAQ worker
        self.data_worker = DataWorker()
        self.data_worker_thread = QThread()
        self.data_worker.moveToThread(self.data_worker_thread)
        self.data_worker_thread.start()
        self.data_worker_ready_for_shutdown = False  # Important for handling termination of the worker thread

        # Connect the start button to the worker and the plot timer
        self.control_bar.start_button_signal.connect(self.data_worker.start_sampling)
        self.control_bar.start_button_signal.connect(self.plot_widget.start_timer)

        # Connect the stop button to the worker and the plot timer
        self.control_bar.stop_button_signal.connect(self.data_worker.stop_sampling)
        self.control_bar.stop_button_signal.connect(self.plot_widget.stop_timer)

        # Connect the data from the worker to the plot widget
        self.data_worker.data_signal.connect(self.plot_widget.process_data_from_worker)

        # Connect the closeEvent signal to the worker to ensure safe termination of timers/threads
        self.shutdown_signal.connect(self.data_worker.shutdown)

        # Create the protocol widget
        self.protocol_widget = ProtocolWidget(self)

        # Create the layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.control_bar)
        left_layout.addWidget(self.plot_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout = QHBoxLayout()
        layout.addLayout(left_layout)
        layout.addWidget(self.protocol_widget)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def closeEvent(self, event):
        """Override of the default close method. Ensure the thread is shut down and the DAQ task is stopped."""
        # First, stop the QTimer that is active in the worker thread, and wait for it to actually stop
        timer_active = self.data_worker.sampling_timer.isActive()
        if timer_active:
            self.shutdown_signal.emit()
            while timer_active is True:  # This loops until the QTimer has fully stopped running
                timer_active = self.data_worker.sampling_timer.isActive()

        # Second, stop the QThread if necessary
        thread_finished = self.data_worker_thread.isFinished()
        if thread_finished is False:
            self.data_worker_thread.quit()
            while thread_finished is False:  # Wait until the QThread has fully stopped running
                thread_finished = self.data_worker_thread.isFinished()

        event.accept()

    @Slot(bool)
    def get_shutdown_status(self, status):
        self.ready_for_shutdown = status
        self.close()


class ControlBar(QWidget):
    """This is the toolbar that holds the buttons that control the software."""
    stop_button_signal = Signal()
    start_button_signal = Signal()
    record_button_signal = Signal()

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.stop_button = QPushButton(parent=self, icon=QIcon("icons/16/142.png"))
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.start_button = QPushButton(parent=self, icon=QIcon("icons/16/131.png"))
        self.start_button.clicked.connect(self.start_button_clicked)
        self.record_button = QPushButton(parent=self, icon=QIcon("icons/16/151.png"))
        self.record_button.clicked.connect(self.record_button_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.stop_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.record_button)

        self.setLayout(layout)

    def stop_button_clicked(self):
        """Emit the stop signal when the button is clicked."""
        self.stop_button_signal.emit()

    def start_button_clicked(self):
        """Emit the start signal when the button is clicked."""
        self.start_button_signal.emit()

    def record_button_clicked(self):
        """Emit the record signal when the button is clicked."""
        self.record_button_signal.emit()


app = QApplication()
window = MainWindow()
window.showMaximized()
app.exec()
