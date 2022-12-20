# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from plot_widget import PlotWidget
from data_worker import DataWorker


class MainWindow(QMainWindow):
    """This class represents the main window of the GUI."""
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

        # Connect the signals between the control bar and the worker
        self.control_bar.start_button_signal.connect(self.data_worker.start_sampling)
        self.control_bar.stop_button_signal.connect(self.data_worker.stop_sampling)
        self.data_worker.data_signal.connect(self.display_data)

        # Create a layout
        layout = QVBoxLayout()
        layout.addWidget(self.control_bar)
        layout.addWidget(self.plot_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def closeEvent(self, event):
        """Override of the default close method. Ensure the thread is shut down and the DAQ task is stopped."""
        # Need to implement a method to shutdown the active DAQ task if one exists. This method will be in the
        # data worker class.
        self.data_worker_thread.exit()

    def display_data(self, data):
        print(data)


class ControlBar(QWidget):
    """This is the toolbar that holds the buttons that control the software."""
    stop_button_signal = Signal(bool)
    start_button_signal = Signal(bool)
    record_button_signal = Signal(bool)

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
        self.stop_button_signal.emit(True)

    def start_button_clicked(self):
        """Emit the start signal when the button is clicked."""
        print("start clicked")
        self.start_button_signal.emit(True)

    def record_button_clicked(self):
        """Emit the record signal when the button is clicked."""
        self.record_button_signal.emit(True)


app = QApplication()
window = MainWindow()
window.showMaximized()
app.exec()
