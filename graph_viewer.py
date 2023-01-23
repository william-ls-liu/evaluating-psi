# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout
import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')


class BaselineGraphDialog(QDialog):
    """This class represents a dialog window that shows a MPL graph."""
    def __init__(self, data, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Baseline APA Viewer")

        # Define the buttons for the dialog box
        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Save Trial", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Repeat Trial", QDialogButtonBox.RejectRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Create the graph
        self.figure = MplCanvas()
        self.figure.cop_graph.plot(data)
        self.figure.cop_graph.set_title("APA")

        # Add the navigation toolbar
        self.toolbar = NavigationToolbar2QT(self.figure, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.figure)
        layout.addWidget(self.button_box)
        self.setLayout(layout)


class MplCanvas(FigureCanvas):
    """The canvas where the graph is drawn."""
    def __init__(self, parent=None, width=10, height=10, dpi=200):
        self.figure = Figure(figsize=(width, height), dpi=dpi, layout='tight')
        self.cop_graph = self.figure.add_subplot(1, 1, 1)
        super().__init__(figure=self.figure)
