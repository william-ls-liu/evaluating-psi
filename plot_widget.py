# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import (QWidget, QVBoxLayout)
from PySide6.QtCore import Slot
from pyqtgraph import GraphicsLayoutWidget


class PlotWidget(QWidget):
    """This widget reads data from the DAQ and holds the graphs to display that data."""
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        self.plots = Plots(self)

        layout = QVBoxLayout()
        layout.addWidget(self.plots)
        self.setLayout(layout)

    @Slot(list)
    def update_plots(self, data):
        """Receives data from the MainWindow and updates the plots."""
        copx = data[0]
        copy = data[1]
        fz = data[2]
        emg_tibialis = data[3]
        emg_soleus = data[4]
        self.plots.update(copx, copy, fz, emg_tibialis, emg_soleus)


class Plots(GraphicsLayoutWidget):
    """This widget represents the different graphs."""
    def __init__(self, parent):
        super().__init__(parent=parent)

        # Create the center of pressure graph
        self.cop_plot_item = self.addPlot(row=0, col=0, title="Center of Pressure (m)")
        self.cop_plot_item.setRange(xRange=(-0.254, 0.254), yRange=(-0.254, 0.254))
        self.cop_plot_item.disableAutoRange(axis='xy')
        self.cop_plot_item.invertX(b=True)  # AMTI axis definitions have +X on the left side of the platform
        self.cop_plot_item.hideButtons()  # Hide the auto-scale button
        self.cop_plot_line = self.cop_plot_item.plot(x=[0], y=[0], pen=None, symbol='o')

        # Create the vertical force graph
        self.fz_plot_item = self.addPlot(row=1, col=0, title="Vertical Force (N)")
        self.fz_plot_item.hideAxis('bottom')
        self.fz_plot_line = self.fz_plot_item.plot(x=[0], y=[0])

        # Create the EMG plots
        self.emg_tibialis_plot_item = self.addPlot(row=0, col=1, title="EMG: Tibialis")
        self.emg_tibialis_plot_item.setRange(yRange=(-2.5, 2.5))
        self.emg_tibialis_plot_item.disableAutoRange(axis='y')
        self.emg_tibialis_plot_item.hideAxis('bottom')
        self.emg_tibialis_plot_line = self.emg_tibialis_plot_item.plot(x=[0], y=[0])

        self.emg_soleus_plot_item = self.addPlot(row=1, col=1, title="EMG: Soleus")
        self.emg_soleus_plot_item.setRange(yRange=(-2.5, 2.5))
        self.emg_soleus_plot_item.disableAutoRange(axis='y')
        self.emg_soleus_plot_item.hideAxis('bottom')
        self.emg_soleus_plot_line = self.emg_soleus_plot_item.plot(x=[0], y=[0])

    def update(self, copx, copy, fz, emg_tibialis, emg_soleus):
        """Update the graphs."""
        self.cop_plot_line.setData(x=[copx[-1]], y=[copy[-1]])
        self.fz_plot_line.setData(y=fz)
        self.emg_tibialis_plot_line.setData(y=emg_tibialis)
        self.emg_soleus_plot_line.setData(y=emg_soleus)
