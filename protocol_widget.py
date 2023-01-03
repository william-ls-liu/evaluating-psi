# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot, Signal
from baseline_graph_viewer import GraphDialog
import numpy as np


class ProtocolWidget(QWidget):
    """This widget provides buttons to control the data collection and labels to show the progress.

    Attributes
    ----------
    start_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `start_baseline_button` is clicked
    cancel_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `cancel_baseline_button` is clicked
    collect_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `collect_baseline_button` is clicked
    finish_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when  `finish_baseline_button` is clicked
    """

    start_baseline_signal = Signal()
    cancel_baseline_signal = Signal()
    collect_baseline_signal = Signal()
    finish_baseline_signal = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Create a heading for the Widget
        self.progress_label = QLabel(parent=self)
        self.progress_label.setText("PSI Protocol Collection Status")
        self.progress_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.progress_label.setWordWrap(True)

        # Create a label to keep track of the number of baseline trials
        self.baseline_trial_counter = QLabel(parent=self)
        self.baseline_trial_counter.setText("Number of baseline trials collected: 0")
        self.baseline_trial_counter.setFont(QFont("Arial", 14))
        self.baseline_trial_counter.setWordWrap(True)

        # Label for tracking the APA threshold
        self.threshold_label = QLabel(parent=self)
        self.threshold_label.setText("No baseline threshold set")
        self.threshold_label.setFont(QFont("Arial", 14))
        self.threshold_label.setWordWrap(True)

        # Create buttons for collecting baseline APA
        self.start_baseline_button = QPushButton(parent=self, text="Start baseline collection")
        self.start_baseline_button.setEnabled(False)
        self.start_baseline_button.clicked.connect(self.start_baseline_button_clicked)

        self.cancel_baseline_button = QPushButton(parent=self, text="Cancel baseline collection")
        self.cancel_baseline_button.setEnabled(False)
        self.cancel_baseline_button.clicked.connect(self.cancel_baseline_button_clicked)

        self.collect_baseline_button = QPushButton(parent=self, text="Collect baseline step")
        self.collect_baseline_button.setEnabled(False)
        self.collect_baseline_button.clicked.connect(self.collect_baseline_button_clicked)

        self.finish_baseline_button = QPushButton(parent=self, text="Finish baseline collection")
        self.finish_baseline_button.setEnabled(False)
        self.finish_baseline_button.clicked.connect(self.finish_baseline_button_clicked)

        # Create buttons for starting/stopping the protocol
        self.start_trial_button = QPushButton(parent=self, text="Start Trial")
        self.start_trial_button.setEnabled(False)

        self.stop_trial_button = QPushButton(parent=self, text="Stop Trial")
        self.stop_trial_button.setEnabled(False)

        # Button for setting APA threshold
        self.set_APA_threshold_button = QPushButton(parent=self, text="Set APA Threshold")
        self.set_APA_threshold_button.setEnabled(False)
        self.set_APA_threshold_button.clicked.connect(self.set_APA_threshold)

        # Initiate variable to store the baseline data
        self.baseline_data = dict()
        self.temporary_data_storage = list()

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(self.progress_label)
        layout.addWidget(self.set_APA_threshold_button)
        layout.addWidget(self.start_baseline_button)
        layout.addWidget(self.cancel_baseline_button)
        layout.addWidget(self.collect_baseline_button)
        layout.addWidget(self.finish_baseline_button)
        layout.addWidget(self.baseline_trial_counter)
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.start_trial_button)
        layout.addWidget(self.stop_trial_button)

        self.setLayout(layout)
        self.setFixedWidth(300)

    @Slot()
    def start_baseline_button_clicked(self):
        self.start_baseline_signal.emit()
        self.cancel_baseline_button.setEnabled(True)

    @Slot()
    def cancel_baseline_button_clicked(self):
        """Cancels a baseline recording if user accepts.

        Opens a pop-up message box allowing user to confirm the cancellation or continue
        with the current recording.
        """

        message_box = QMessageBox.warning(
            self,
            "Warning!",
            "Are you sure you want to cancel the baseline collection?\n"
            "You will lose all previously collect baseline trials.",
            buttons=QMessageBox.No | QMessageBox.Yes,
            defaultButton=QMessageBox.No
        )

        if message_box == QMessageBox.Yes:
            # Emit the cancel button signal
            self.cancel_baseline_signal.emit()

            # If the cancel button is pressed during a collection then emit the same signal
            # that the finish button does to disconnect the DataWorker from this widget
            if self.finish_baseline_button.isEnabled():
                self.finish_baseline_signal.emit()
                self.finish_baseline_button.setEnabled(False)

            # Delete all the previously collected trials and any temporary data that has been stored
            self.baseline_data.clear()
            self.temporary_data_storage.clear()

            # Disable/enable relevant buttons
            self.start_baseline_button.setEnabled(True)
            self.cancel_baseline_button.setEnabled(False)
            self.collect_baseline_button.setEnabled(False)
            self.set_APA_threshold_button.setEnabled(False)

            # Reset the counter
            self.baseline_trial_counter.setText("Number of baseline trials collected: 0")
            self.threshold_label.setText("No baseline threshold set")

    @Slot()
    def collect_baseline_button_clicked(self):
        self.collect_baseline_signal.emit()
        self.finish_baseline_button.setEnabled(True)
        self.collect_baseline_button.setEnabled(False)

    @Slot()
    def finish_baseline_button_clicked(self):
        self.finish_baseline_signal.emit()
        self.collect_baseline_button.setEnabled(True)
        self.finish_baseline_button.setEnabled(False)

        # Open the Graph Dialog
        self.show_baseline_graph()

    def show_baseline_graph(self):
        """Display the lateral CoP data from the most recent trial.

        Open a dialog window with a graph of the lateral CoP position vs. time. User can choose to save the trial or
        discard it, depending on how the graph looks.
        """
        
        copx = self.calculate_APA(self.temporary_data_storage)
        graph_dialog = GraphDialog(data=copx, parent=self)
        graph_dialog.open()
        graph_dialog.finished.connect(self.handle_baseline_trial)

    def calculate_APA(self, data):
        """Calculate the relative motion of the lateral CoP and return it.

        The relative motion is the distance the lateral CoP has moved from the starting position. Starting position is
        defined as the mean CoP during 5 seconds of quiet stance.

        Parameters
        ----------
        data : list of np.ndarray
            data from the most recent baseline recording

        Returns
        -------
        list
            a time-series of the relative lateral CoP deviations
        """

        # Get the lateral CoP data
        copx = [row[8] for row in data]
        # TODO: get rid of this 5000 magic number, read the settings file and get sample rate, then multiply by 5
        quiet_stance = copx[:5000]  # Get first 5s of trial
        x_origin = np.mean(quiet_stance)

        return [row[8] - x_origin for row in data]

    @Slot(int)
    def handle_baseline_trial(self, result):
        """This method will save or discard the most recent baseline trial, depending on what the user selects.

        Parameters
        ----------
        result : int
            result code emitted when `GraphDialog` window is closed, 1 indicates user wants to save the trial
        """
        if result == 1:
            number_of_baseline_trials = len(self.baseline_data)
            # Save a copy of the temporary storage list, since clear() on that list will affect references as well
            self.baseline_data[f"trial {number_of_baseline_trials + 1}"] = self.temporary_data_storage.copy()
            # Update the counter to display number of trials collected
            self.baseline_trial_counter.setText(f"Number of baseline trials collected: {number_of_baseline_trials + 1}")
            # Enable button to set the APA threshold based on collected baseline trials
            self.set_APA_threshold_button.setEnabled(True)

        self.temporary_data_storage.clear()

    @Slot(bool)
    def toggle_collect_baseline_button(self, check_state):
        self.start_baseline_button.setEnabled(check_state)
        self.collect_baseline_button.setEnabled(False)
        self.finish_baseline_button.setEnabled(False)
        self.start_trial_button.setEnabled(False)
        self.stop_trial_button.setEnabled(False)

    @Slot(np.ndarray)
    def receive_data(self, data: np.ndarray):
        self.temporary_data_storage.append(data)

    @Slot()
    def ready_to_start_baseline(self):
        self.collect_baseline_button.setEnabled(True)
        self.start_baseline_button.setEnabled(False)

    @Slot()
    def set_APA_threshold(self):
        """This method will calculate the APA threshold based on the collected baseline trials.

        For every trial find the maximum, relative, lateral deviation of the CoP. Find the mean
        across all trials to get the average lateral CoP deviation during a step.
        """

        maximum_lateral_deviation = list()

        for trial in self.baseline_data.keys():

            trial_data = self.baseline_data[trial].copy()
            copx = self.calculate_APA(trial_data)
            maximum_lateral_deviation.append(max(copx, key=abs))

        self.threshold_label.setText(f"APA Threshold: {np.mean(maximum_lateral_deviation)}")
