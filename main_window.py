# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from plot_widget import PlotWidget


class MainWindow(QMainWindow):
    """This class represents the main window of the GUI."""
    def __init__(self) -> None:
        super().__init__(parent=None)

        # Set the title
        self.setWindowTitle("PSI Data Collection Software")

        # A MainWindow needs a central widget to serve as a container for all other widgets
        self.central_widget = QWidget(parent=self)

        # Add a toolbar
        self.control_bar = ControlBar(self)

        # Add plot widget
        self.plot_widget = PlotWidget(self)

        # Create a layout
        layout = QVBoxLayout()
        layout.addWidget(self.control_bar)
        layout.addWidget(self.plot_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)


class ControlBar(QWidget):
    """This is the toolbar that holds the buttons that control the software."""
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.stop_button = QPushButton(parent=self, icon=QIcon("icons/16/142.png"))
        # self.stop_button.setFixedSize(20, 20)
        self.start_button = QPushButton(parent=self, icon=QIcon("icons/16/131.png"))
        # self.start_button.setFixedSize(20, 20)
        self.record_button = QPushButton(parent=self, icon=QIcon("icons/16/151.png"))

        layout = QHBoxLayout()
        layout.addWidget(self.stop_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.record_button)
        # layout.addStretch(1)

        self.setLayout(layout)


app = QApplication()
window = MainWindow()
window.showMaximized()
app.exec()
