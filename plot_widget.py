# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import (QWidget, QVBoxLayout)
from PySide6.QtCore import Slot, QTimer
from pyqtgraph import GraphicsLayoutWidget
import numpy as np
import json
import consts


def calculate_center_of_pressure(fx, fy, fz, mx, my):
    """Calculate the center of pressure (CoP).

    Parameters
    ----------
    fx : float
        the force along the x axis
    fy : float
        the force along the y axis
    fz : float
        the force along the z axis
    mx : float
        the moment about the x axis
    my : float
        the moment about the y axis

    Returns
    -------
    tuple
        (x coordinate of the CoP, y coordinate of the CoP)
    """

    cop_x = (-1) * ((my + (consts.ZOFF * fx)) / fz)
    cop_y = ((mx - (consts.ZOFF * fy)) / fz)

    return cop_x, cop_y


class PlotWidget(QWidget):
    """Custom widget that receives data and plots it using pyqtgraph."""

    def __init__(self, parent=None) -> None:
        """
        Parameters
        ----------
        parent : PySide6.QtWidgets.QWidget, optional
            the parent widget, if None the widget becomes a window
        """

        super().__init__(parent=parent)

        # Initiate the timer that updates the graphs
        self.timer = QTimer(parent=self)
        self.timer.setInterval(33.33)  # ~30Hz, the faster the more resource intensive the app
        self.timer.timeout.connect(self.update_plots)

        # Initiate variables to store incoming data from DataWorker
        self._sample_rate = self._read_settings_file()
        samples_to_show = consts.SECONDS_TO_SHOW * self._sample_rate
        self.cop_xdirection = [0 for i in range(samples_to_show)]
        self.cop_ydirection = [0 for i in range(samples_to_show)]
        self.force_zdirection = [0 for i in range(samples_to_show)]
        self.emg_tibialis = [0 for i in range(samples_to_show)]
        self.emg_soleus = [0 for i in range(samples_to_show)]

        # Initiate the pyqygraph widget
        self.plots = Plots(self, self._sample_rate)

        layout = QVBoxLayout()
        layout.addWidget(self.plots)
        self.setLayout(layout)

    def _read_settings_file(self):
        """Read the settings file to get the sample rate."""
        with open("amti_settings.json", 'r') as file:
            settings = json.load(file)

        sample_rate = settings["sample_rate"]

        return sample_rate

    @Slot(np.ndarray)
    def process_data_from_worker(self, data: np.ndarray) -> None:
        """Slot to receive data and store it in appropriate lists.

        Incoming data is array-like with values
        [Fx, Fy, Fz, Mx, My, Mz, EMG Tibialis, EMG Soleus]. Extract individual
        components of incoming data and add them to their list.

        Parameters
        ----------
        data : np.ndarray
            incoming data
        """

        if data[consts.FZ] > consts.MINIMUM_VERTICAL_FORCE:
            cop_x, cop_y = calculate_center_of_pressure(
                data[consts.FX],
                data[consts.FY],
                data[consts.FZ],
                data[consts.MX],
                data[consts.MY]
            )
        else:
            # This is super kludge, but basically want a threshold below which
            # CoP data won't be displayed. Setting to np.NAN works, but raises
            # an unavoidable warning that has to do with how pyqtgraph uses np,
            # so for now I'll stick with this.
            cop_x = 100
            cop_y = 100

        self.cop_xdirection = self.cop_xdirection[1:]
        self.cop_xdirection.append(cop_x)
        self.cop_ydirection = self.cop_ydirection[1:]
        self.cop_ydirection.append(cop_y)

        self.force_zdirection = self.force_zdirection[1:]
        self.force_zdirection.append(data[consts.FZ])

        self.emg_tibialis = self.emg_tibialis[1:]
        self.emg_tibialis.append(data[consts.EMG_1])
        self.emg_soleus = self.emg_soleus[1:]
        self.emg_soleus.append(data[consts.EMG_2])

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

    def __init__(self, parent, sample_rate) -> None:
        """
        Parameters
        ----------
        parent : PySide6.QtWidgets.QWidget
            the parent widget
        sample_rate : int
            sample rate of the DAQ
        """

        super().__init__(parent=parent)

        # Set cutoff for displaying 1 second of data on the CoP graph
        self._cop_cutoff = (-1) * sample_rate

        # Create the center of pressure graph
        self.cop_plot_item = self.addPlot(row=0, col=0, title="Center of Pressure (m)")
        self.cop_plot_item.setRange(xRange=(-0.254, 0.254), yRange=(-0.254, 0.254))
        self.cop_plot_item.disableAutoRange(axis='xy')
        self.cop_plot_item.invertX(b=True)  # AMTI axis definitions have +X on the left side of the platform
        self.cop_plot_item.hideButtons()  # Hide the auto-scale button
        self.cop_plot_line = self.cop_plot_item.plot(
            x=[0],
            y=[0],
            pen=None,
            symbol='o',
            symbolSize=2,
            symbolPen=(167, 204, 237),
            symbolBrush=(167, 204, 237)
        )

        # Create the vertical force graph
        self.fz_plot_item = self.addPlot(row=1, col=0, title="Vertical Force (N)")
        self.fz_plot_item.setRange(yRange=(consts.FZ_MIN, consts.FZ_MAX))
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

        self.cop_plot_line.setData(x=cop_xdirection[self._cop_cutoff:], y=cop_ydirection[self._cop_cutoff:])
        self.fz_plot_line.setData(y=force_zdirection)
        self.emg_tibialis_plot_line.setData(y=emg_tibialis)
        self.emg_soleus_plot_line.setData(y=emg_soleus)
