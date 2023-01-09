# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QVBoxLayout, QWidget
from scipy.signal import decimate
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvasQTAgg):
    """The canvas onto which the graphs are drawn."""
    def __init__(self, parent=None, width=10, height=10, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.cop_graph = self.fig.add_subplot(221)
        self.fz_graph = self.fig.add_subplot(222)
        self.emg_tibialis_graph = self.fig.add_subplot(223)
        self.emg_soleus_graph = self.fig.add_subplot(224)
        super().__init__(figure=self.fig)


class GraphWindow(QWidget):
    """This is the window that will display the graphs from the data collection."""
    def __init__(self, data_to_plot):
        super().__init__()
        self.setWindowTitle("Data Viewer")

        # Create the graph canvas
        graphs = MplCanvas()

        # Create the Center of Pressure graph
        copX = decimate(data_to_plot['CopX'], q=10)
        copY = decimate(data_to_plot['CopY'], q=10)
        graphs.cop_graph.plot(copX, copY)
        graphs.cop_graph.set_title("Center of Pressure")
        graphs.cop_graph.set_xlim([-0.254, 0.254])
        graphs.cop_graph.set_ylim([-0.254, 0.254])
        graphs.cop_graph.invert_xaxis()
        graphs.cop_graph.set_ylabel("CoP Anterioposterior (meters)")
        graphs.cop_graph.set_xlabel("CoP Mediolateral (meters)")

        # Create the Z Force graph
        fz = decimate(data_to_plot['Fz'], q=10)
        graphs.fz_graph.plot(fz)
        graphs.fz_graph.set_title("Z-force")
        graphs.fz_graph.set_xlabel("Samples")
        graphs.fz_graph.set_ylabel("Force (Newtons)")

        # Create the EMG graphs
        emg_soleus = decimate(data_to_plot['EMG Soleus'], q=10)
        emg_tibialis = decimate(data_to_plot['EMG Tibialis'], q=10)
        graphs.emg_soleus_graph.plot(emg_soleus)
        graphs.emg_soleus_graph.set_title("EMG Soleus")
        graphs.emg_tibialis_graph.plot(emg_tibialis)
        graphs.emg_tibialis_graph.set_title("EMG Tibialis")

        toolbar = NavigationToolbar2QT(graphs, self)

        layout = QVBoxLayout()
        layout.addWidget(graphs)
        layout.addWidget(toolbar)

        self.setLayout(layout)
