# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')


class GraphDialog(QDialog):
    """This class represents a dialog window that shows a MPL graph."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Baseline APA Viewer")

        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Save Trial", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Repeat Trial", QDialogButtonBox.RejectRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        dummy = QLabel("This is a test!")
        layout.addWidget(dummy)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
