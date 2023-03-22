# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QPlainTextEdit, QLabel
from PySide6.QtCore import Signal
import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import consts
matplotlib.use('Qt5Agg')


matplotlib.rcParams.update({'font.size': 6})


class GraphDialog(QDialog):
    """Base class for graph windows."""

    def __init__(self, window_title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(window_title)

        # Define the buttons for the dialog box
        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton("Save Trial", QDialogButtonBox.AcceptRole)
        self.repeat_button = self.button_box.addButton("Repeat Trial", QDialogButtonBox.RejectRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Create the canvas
        self.canvas = MplCanvas()

        # Add the navigation toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)


class BaselineGraphDialog(GraphDialog):
    """A dialog window that shows a baseline trial graph."""

    def __init__(self, data, peaks, valleys, parent=None):
        super().__init__("Baseline APA Viewer", parent)

        # If no peaks were detected, remove option to save the trial
        if len(peaks) == 0 or len(valleys) == 0:
            self.button_box.removeButton(self.save_button)

        self.mediolateral_force_graph = self.canvas.figure.add_subplot(1, 1, 1)
        self.mediolateral_force_graph.plot(data)
        self.mediolateral_force_graph.plot(peaks, data[peaks], "x")
        self.mediolateral_force_graph.plot(valleys, data[valleys], "x")
        self.mediolateral_force_graph.set_title("Mediolateral Force (N)")


class StepGraphDialog(GraphDialog):
    """A dialog window that shows a step trial graph."""

    notes_signal = Signal(str)  # Signal containing collection notes

    def __init__(self, data, parent=None) -> None:

        super().__init__("Step Trial Viewer", parent)

        # Add a text entry box where user can write collection notes
        self.collection_notes_label = QLabel(text="Collection Notes:")
        self.collection_notes_text_edit = QPlainTextEdit(parent=self)
        self.collection_notes_text_edit.setPlaceholderText("Enter notes here.")

        # Update the layout with new widgets
        self.layout.replaceWidget(self.button_box, self.collection_notes_label)
        self.layout.addWidget(self.collection_notes_text_edit)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

        self.mediolateral_force_graph = self.canvas.figure.add_subplot(3, 2, 1)
        self.mediolateral_force_graph.plot([row[consts.FX] for row in data])
        self.mediolateral_force_graph.set_title("Mediolateral Force (N)")

        self.anteroposterior_force_graph = self.canvas.figure.add_subplot(3, 2, 2)
        self.anteroposterior_force_graph.plot([row[consts.FY] for row in data])
        self.anteroposterior_force_graph.set_title("Anteroposterior Force (N)")

        self.vertical_force_graph = self.canvas.figure.add_subplot(3, 2, 3)
        self.vertical_force_graph.plot([row[consts.FZ] for row in data])
        self.vertical_force_graph.set_title("Vertical Force (N)")

        self.emg_tibialis_graph = self.canvas.figure.add_subplot(3, 2, 4)
        self.emg_tibialis_graph.plot([row[consts.EMG_1] for row in data])
        self.emg_tibialis_graph.set_title("EMG Tibialis (V)")

        self.emg_soleus_graph = self.canvas.figure.add_subplot(3, 2, 5)
        self.emg_soleus_graph.plot([row[consts.EMG_2] for row in data])
        self.emg_soleus_graph.set_title("EMG Soleus (V)")

    def accept(self):
        """Re-implement default accept behavior to save collection notes."""
        self.notes_signal.emit(self.collection_notes_text_edit.toPlainText())
        super().accept()


class MplCanvas(FigureCanvas):
    """The canvas where the graph is drawn."""

    def __init__(self, parent=None, width=10, height=10, dpi=200):
        self.figure = Figure(figsize=(width, height), dpi=dpi, layout='tight')
        super().__init__(figure=self.figure)
