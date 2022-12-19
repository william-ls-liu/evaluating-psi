# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtCore, QtWidgets, QtGui


class MainWindow(QtWidgets.QMainWindow):
    """This class represents the main window of the GUI."""
    def __init__(self) -> None:
        super().__init__(parent=None)

        # Set the title
        self.setWindowTitle("PSI Data Collection Software")

        # A MainWindow needs a central widget to serve as a container for all other widgets
        self.central_widget = QtWidgets.QWidget(parent=self)

        # Add a toolbar
        self.toolbar = ControlBar(self)

        # Create a layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)


class ControlBar(QtWidgets.QWidget):
    """This is the toolbar that holds the buttons that control the software."""
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.stop_button = QtWidgets.QPushButton(parent=self, icon=QtGui.QIcon("icons/16/142.png"))
        # self.stop_button.setFixedSize(20, 20)
        self.start_button = QtWidgets.QPushButton(parent=self, icon=QtGui.QIcon("icons/16/131.png"))
        # self.start_button.setFixedSize(20, 20)
        self.record_button = QtWidgets.QPushButton(parent=self, icon=QtGui.QIcon("icons/16/151.png"))

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.stop_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.record_button)
        # layout.addStretch(1)

        self.setLayout(layout)


app = QtWidgets.QApplication()
window = MainWindow()
window.showMaximized()
app.exec()
