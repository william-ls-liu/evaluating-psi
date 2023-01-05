# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import (QWidget, QVBoxLayout)
from PySide6.QtCore import Slot, QTimer
from pyqtgraph import GraphicsLayoutWidget
import numpy as np
from collections import namedtuple


amplifier_range_namedtuple = namedtuple(
    "Amplifier Range",
    [
        'Fx_min',
        'Fx_max',
        'Fy_min',
        'Fy_max',
        'Fz_min',
        'Fz_max',
        'Mx_min',
        'Mx_max',
        'My_min',
        'My_max',
        'Mz_min',
        'Mz_max'
    ]
)

AMPLIFIER_RANGE = amplifier_range_namedtuple(
    Fx_min=-192.73,
    Fx_max=192.73,
    Fy_min=-193.55,
    Fy_max=193.55,
    Fz_min=-1504.76,
    Fz_max=1504.76,
    Mx_min=-155.80,
    Mx_max=155.80,
    My_min=-154.96,
    My_max=154.96,
    Mz_min=-37.77,
    Mz_max=37.77
)


class PlotWidget(QWidget):
    """Custom widget that receives data and plots it using pyqtgraph.

    Attributes
    ----------
    plots : GraphicsLayoutWidget
        a pyqtgraph GraphicsLayoutWidget that contains subplots
    timer : PySide6.QtCore.QTimer
        timer object, on timeout it updates the graphs with any new data
    cop_xdirection : list
        stores center of pressure coordinates in the x-direction
    cop_ydirection : list
        stores center of pressure coordinates in the y-direction
    force_zdirection : list
        stores the force values in the z-direction
    emg_tibialis : list
        stores the voltage values from the EMG placed on the tibialis
    emg_soleus : list
        stores the voltage values from the EMG places on the soleus

    Methods
    -------
    process_data_from_worker(data: np.ndarray)
        A Slot. Receives an array of data and stores values in appropriate lists
    update_plots()
        A Slot. Called by the timeout of timer. Calls Plots.update to add new data to graphs.
    start_timer()
        A Slot that starts timer. QTimers cannot be started/stopped from other threads, but using a signal and slot
        is threadsafe.
    stop_timer()
        A Slot that stops timer.
    """

    def __init__(self, parent=None) -> None:
        """
        Parameters
        ----------
        parent : PySide6.QtWidgets.QWidget, optional
            the parent widget, if None the widget becomes a window
        """

        super().__init__(parent=parent)

        # Initiate the pyqygraph widget
        self.plots = Plots(self)

        # Initiate the timer that updates the graphs
        self.timer = QTimer(parent=self)
        self.timer.setInterval(33.33)  # ~30Hz, the faster the more resource intensive the app
        self.timer.timeout.connect(self.update_plots)

        # Initiate variables to store incoming data from DataWorker
        # TODO: Get rid of this magic number and use the sample rate multiplied
        # by however many seconds should be shown
        samples_to_show = 2000
        self.cop_xdirection = [0 for i in range(samples_to_show)]
        self.cop_ydirection = [0 for i in range(samples_to_show)]
        self.force_zdirection = [0 for i in range(samples_to_show)]
        self.emg_tibialis = [0 for i in range(samples_to_show)]
        self.emg_soleus = [0 for i in range(samples_to_show)]

        layout = QVBoxLayout()
        layout.addWidget(self.plots)
        self.setLayout(layout)

    @Slot(np.ndarray)
    def process_data_from_worker(self, data: np.ndarray) -> None:
        """
        Slot to receive data and store it in appropriate lists.

        Incoming data is array-like with values [Fx, Fy, Fz, Mx, My, Mz, EMG Tibialis, EMG Soleus, CoP X, CoP Y].
        Extract individual components of incoming data and add them to their list.

        Parameters
        ----------
        data : np.ndarray
            incoming data
        """

        self.cop_xdirection = self.cop_xdirection[1:]
        self.cop_xdirection.append(data[8])
        self.cop_ydirection = self.cop_ydirection[1:]
        self.cop_ydirection.append(data[9])

        self.force_zdirection = self.force_zdirection[1:]
        self.force_zdirection.append(data[2])

        self.emg_tibialis = self.emg_tibialis[1:]
        self.emg_tibialis.append(data[6])
        self.emg_soleus = self.emg_soleus[1:]
        self.emg_soleus.append(data[7])

    @Slot()
    def update_plots(self) -> None:
        """Update the graphs with new data."""

        self.plots.update(
            self.cop_xdirection,
            self.cop_ydirection,
            self.force_zdirection,
            self.emg_tibialis,
            self.emg_soleus
        )

    @Slot()
    def start_timer(self) -> None:
        """Start the QTimer."""

        self.timer.start()

    @Slot()
    def stop_timer(self) -> None:
        """Stop the QTimer."""

        self.timer.stop()


class Plots(GraphicsLayoutWidget):
    """A class to display a multi-panel pyqtgraph figure."""

    def __init__(self, parent) -> None:
        """
        Parameters
        ----------
        parent : PySide6.QtWidgets.QWidget
            the parent widget
        """

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
        self.fz_plot_item.setRange(yRange=(AMPLIFIER_RANGE.Fz_min, AMPLIFIER_RANGE.Fz_max))
        self.fz_plot_item.disableAutoRange(axis='y')
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

    def update(self, cop_xdirection, cop_ydirection, force_zdirection, emg_tibialis, emg_soleus) -> None:
        """
        Update the graphs with new data.

        Parameters
        ----------
        cop_xdirection : list
            center of pressure data in x-direction (platform coordinates)
        cop_ydirection : list
            center of pressure data in y-direction (platform coordinates)
        force_zdirection : list
            force data in the z-direction (platform coordinates)
        emg_tibialis : list
            emg data from tibialis sensor
        emg_soleus : list
            emg data from soleus sensor
        """

        self.cop_plot_line.setData(x=[cop_xdirection[-1]], y=[cop_ydirection[-1]])
        self.fz_plot_line.setData(y=force_zdirection)
        self.emg_tibialis_plot_line.setData(y=emg_tibialis)
        self.emg_soleus_plot_line.setData(y=emg_soleus)
