# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout
import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')


# Indexes of platform axes
FX = 0
FY = 1
FZ = 2
MX = 3
MY = 4
MZ = 5
EMG_1 = 6
EMG_2 = 7


class GraphDialog(QDialog):
    """Base class for graph windows."""

    def __init__(self, window_title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(window_title)

        # Define the buttons for the dialog box
        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Save Trial", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Repeat Trial", QDialogButtonBox.RejectRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Create the canvas
        self.canvas = MplCanvas()

        # Add the navigation toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button_box)
        self.setLayout(layout)


class BaselineGraphDialog(GraphDialog):
    """A dialog window that shows a baseline trial graph."""

    def __init__(self, data, peaks, valleys, parent=None):
        super().__init__("Baseline APA Viewer", parent)

        self.mediolateral_force_graph = self.canvas.figure.add_subplot(1, 1, 1)
        self.mediolateral_force_graph.plot(data)
        self.mediolateral_force_graph.plot(peaks, data[peaks], "x")
        self.mediolateral_force_graph.plot(valleys, data[valleys], "x")
        self.mediolateral_force_graph.set_title("Mediolateral Force (N)")


class StepGraphDialog(GraphDialog):
    """A dialog window that shows a step trial graph."""

    def __init__(self, data, parent=None) -> None:

        super().__init__("Step Trial Viewer", parent)

        self.mediolateral_force_graph = self.canvas.figure.add_subplot(3, 2, 1)
        self.mediolateral_force_graph.plot([row[FX] for row in data])
        self.mediolateral_force_graph.set_title("Mediolateral Force (N)")

        self.anteroposterior_force_graph = self.canvas.figure.add_subplot(3, 2, 2)
        self.anteroposterior_force_graph.plot([row[FY] for row in data])
        self.anteroposterior_force_graph.set_title("Anteroposterior Force (N)")

        self.vertical_force_graph = self.canvas.figure.add_subplot(3, 2, 3)
        self.vertical_force_graph.plot([row[FZ] for row in data])
        self.vertical_force_graph.set_title("Vertical Force (N)")

        self.emg_tibialis_graph = self.canvas.figure.add_subplot(3, 2, 4)
        self.emg_tibialis_graph.plot([row[EMG_1] for row in data])
        self.emg_tibialis_graph.set_title("EMG Tibialis (V)")

        self.emg_soleus_graph = self.canvas.figure.add_subplot(3, 2, 5)
        self.emg_soleus_graph.plot([row[EMG_2] for row in data])
        self.emg_soleus_graph.set_title("EMG Soleus (V)")


class MplCanvas(FigureCanvas):
    """The canvas where the graph is drawn."""

    def __init__(self, parent=None, width=10, height=10, dpi=200):
        self.figure = Figure(figsize=(width, height), dpi=dpi, layout='tight')
        super().__init__(figure=self.figure)
