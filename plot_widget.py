# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import (QWidget, QVBoxLayout)
from pyqtgraph import GraphicsLayoutWidget


class PlotWidget(QWidget):
    """This widget reads data from the DAQ and holds the graphs to display that data."""
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        self.plots = Plots(self)

        layout = QVBoxLayout()
        layout.addWidget(self.plots)
        self.setLayout(layout)


class Plots(GraphicsLayoutWidget):
    """This widget represents the different graphs."""
    def __init__(self, parent):
        super().__init__(parent=parent)

        # Create the center of pressure graph
        self.cop_plot_item = self.addPlot(row=0, col=0, title="Center of Pressure (m)")
        self.cop_plot_item.setRange(xRange=(-0.254, 0.254), yRange=(-0.254, 0.254))
        self.cop_plot_item.disableAutoRange(axis='xy')
        self.cop_plot_item.invertX(b=True)  # AMTI axis definitions have +X on the left side of the platform
        self.cop_plot_line = self.cop_plot_item.plot(x=[0], y=[0], pen=None, symbol='o')

        # Create the vertical force graph
        self.fz_plot_item = self.addPlot(row=0, col=1, title="Vertical Force (N)")
        self.fz_plot_line = self.fz_plot_item.plot(x=[1, 2], y=[10, -30])
