# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox, QComboBox, QGridLayout
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot, Signal
from baseline_graph_viewer import GraphDialog
import numpy as np


class ProtocolWidget(QWidget):
    """Sidebar with buttons that control data collection and display progress.

    Attributes
    ----------
    start_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `start_baseline_button` is clicked
    stop_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `stop_baseline_button` is clicked
    collect_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `collect_baseline_button` is clicked
    finish_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when  `finish_baseline_button` is clicked
    """

    start_baseline_signal = Signal()
    stop_baseline_signal = Signal()
    collect_baseline_signal = Signal()
    finish_baseline_signal = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Create a heading for the Widget
        self.progress_label = QLabel(parent=self)
        self.progress_label.setText("PSI Protocol Collection Status")
        self.progress_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.progress_label.setWordWrap(True)

        # Label for tracking the APA threshold
        self.threshold_label = QLabel(parent=self)
        self.threshold_label.setText("No baseline threshold set")
        self.threshold_label.setFont(QFont("Arial", 14))
        self.threshold_label.setWordWrap(True)

        # ComboBox for specifying % threshold
        self.threshold_percentage_entry = QComboBox(parent=self)
        self.threshold_percentage_entry.addItems(['5', '10', '15', '20', '25', '30'])
        self.threshold_percentage_entry.currentTextChanged.connect(self.update_threshold_percentage)
        self.threshold_percentage = int(self.threshold_percentage_entry.currentText())

        # Button for setting APA threshold
        self.set_APA_threshold_button = QPushButton(parent=self, text="Set APA Threshold")
        self.set_APA_threshold_button.setEnabled(False)
        self.set_APA_threshold_button.clicked.connect(self.set_APA_threshold)

        # Create buttons for starting/stopping the protocol
        self.start_trial_button = QPushButton(parent=self, text="Start Trial")
        self.start_trial_button.setEnabled(False)

        self.stop_trial_button = QPushButton(parent=self, text="Stop Trial")
        self.stop_trial_button.setEnabled(False)

        # Initiate variable to store the baseline data
        self.baseline_data = dict()
        self.temporary_data_storage = list()

        # Create the parent layout
        layout = QVBoxLayout()

        # Create layout for the baseline buttons
        baseline_layout = QGridLayout()

        # Populate the layout
        layout.addWidget(self.progress_label)
        layout.addLayout(baseline_layout)
        layout.addWidget(self.threshold_percentage_entry)
        layout.addWidget(self.set_APA_threshold_button)
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.start_trial_button)
        layout.addWidget(self.stop_trial_button)

        # Populate the baseline layout
        self._create_baseline_layout(baseline_layout)

        self.setLayout(layout)
        self.setFixedWidth(300)

    def _create_baseline_layout(self, layout):
        """Create buttons for baseline collection, add them to a layout."""

        self.start_baseline_button = QPushButton(self, text="Start baseline collection")
        self.start_baseline_button.setEnabled(False)
        self.start_baseline_button.clicked.connect(self.start_baseline_button_clicked)

        self.stop_baseline_button = QPushButton(self, text="Stop baseline collection")
        self.stop_baseline_button.setEnabled(False)
        self.stop_baseline_button.clicked.connect(self.stop_baseline_button_clicked)

        self.collect_baseline_button = QPushButton(self, text="Collect a step")
        self.collect_baseline_button.setEnabled(False)
        self.collect_baseline_button.clicked.connect(self.collect_baseline_button_clicked)

        self.finish_baseline_button = QPushButton(parent=self, text="Finish baseline collection")
        self.finish_baseline_button.setEnabled(False)
        self.finish_baseline_button.clicked.connect(self.finish_baseline_button_clicked)

        # Create a label to keep track of the number of baseline trials
        self.baseline_trial_counter = 0
        self.baseline_trial_counter_label = QLabel(parent=self)
        self.baseline_trial_counter_label.setFont(QFont("Arial", 14))
        self.baseline_trial_counter_label.setWordWrap(True)
        self._update_baseline_trial_counter_label()

        layout.addWidget(self.start_baseline_button, 0, 0)
        layout.addWidget(self.stop_baseline_button, 0, 1)
        layout.addWidget(self.collect_baseline_button, 1, 0, 1, 2)
        layout.addWidget(self.finish_baseline_button, 2, 0, 1, 2)
        layout.addWidget(self.baseline_trial_counter_label, 3, 0, 1, 2)

    def _update_baseline_trial_counter_label(self):
        self.baseline_trial_counter_label.setText(
            f"Number of baseline trials collected: {self.baseline_trial_counter}"
        )

    @Slot()
    def start_baseline_button_clicked(self):
        """Open a blocking message when the user wants to start collecting the baseline APA."""
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Attention!")
        message_box.setText(
            "Instruct patient to step off the platform,\n"
            "then hit the Auto-Zero button on the amplifier.\n"
            "When you have done this click OK.")
        message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        button = message_box.exec()

        if button == QMessageBox.Ok:
            self.start_baseline_signal.emit()
            self.stop_baseline_button.setEnabled(True)
            self.collect_baseline_button.setEnabled(True)
            self.start_baseline_button.setEnabled(False)

    @Slot()
    def stop_baseline_button_clicked(self):
        """Opens dialog for user to stop baseline collection, if they choose.

        Pop-up message box will allow user to save any previously collected
        baseline trials. If no baseline data has been collected user is given
        the choice to stop baseline collection or continue.
        """

        message_box = QMessageBox()
        message_box.setWindowTitle("Stop baseline collection?")
        message_box.setIcon(QMessageBox.Information)

        if self.baseline_data:
            message_box.setText(
                f"Number of pending baseline trials: {self.baseline_trial_counter}"
            )
            message_box.setInformativeText("Do you want to save these trials?")
            message_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            message_box.setDefaultButton(QMessageBox.Save)
        else:
            message_box.setText("You have not collected any baseline trials")
            message_box.setInformativeText("Do you want to stop baseline collection?")
            message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            message_box.setDefaultButton(QMessageBox.Yes)

        ret = message_box.exec()

        if ret == QMessageBox.Discard:
            self.baseline_data.clear()
            self.baseline_trial_counter = 0
            self._update_baseline_trial_counter_label()
            self.set_APA_threshold_button.setEnabled(False)

        if ret in {QMessageBox.Discard, QMessageBox.Save, QMessageBox.Yes}:
            self.start_baseline_button.setEnabled(True)
            self.stop_baseline_button.setEnabled(False)
            self.collect_baseline_button.setEnabled(False)
            self.stop_baseline_signal.emit()

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

        Open a dialog window with a graph of the lateral CoP position vs. time.
        User can choose to save the trial or discard it, depending on how the
        graph looks.
        """

        cop_xdirection = self.calculate_APA(self.temporary_data_storage)
        graph_dialog = GraphDialog(data=cop_xdirection, parent=self)
        graph_dialog.open()
        graph_dialog.finished.connect(self.handle_baseline_trial)

    def calculate_APA(self, data):
        """Calculate the relative motion of the lateral CoP and return it.

        The relative motion is the distance the lateral CoP has moved from the
        starting position. Starting position is defined as the mean CoP during 5
        seconds of quiet stance.

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
        cop_xdirection = [row[8] for row in data]
        # TODO: get rid of this 5000 magic number, read the settings file and get sample rate, then multiply by 5
        quiet_stance = cop_xdirection[:5000]  # Get first 5s of trial
        x_origin = np.mean(quiet_stance)

        return [row[8] - x_origin for row in data]

    @Slot(int)
    def handle_baseline_trial(self, result):
        """Save/discard the most recent baseline trial, based on user selection.

        Parameters
        ----------
        result : int
            result code emitted when `GraphDialog` window is closed, 1 indicates
            user wants to save the trial
        """

        if result == 1:

            self.baseline_trial_counter = len(self.baseline_data) + 1
            # Save a copy of the temporary storage list, since clear() on that list will affect references as well
            self.baseline_data[f"trial {self.baseline_trial_counter}"] = self.temporary_data_storage.copy()
            self._update_baseline_trial_counter_label()
            # Enable button to set the APA threshold based on collected baseline trials
            self.set_APA_threshold_button.setEnabled(True)

        self.temporary_data_storage.clear()

    @Slot(bool)
    def toggle_collect_baseline_button(self, check_state) -> None:
        self.start_baseline_button.setEnabled(check_state)
        self.collect_baseline_button.setEnabled(False)
        self.finish_baseline_button.setEnabled(False)
        self.start_trial_button.setEnabled(False)
        self.stop_trial_button.setEnabled(False)

    @Slot(np.ndarray)
    def receive_data(self, data: np.ndarray) -> None:
        """Receives data from the `DataWorker` and stores it in a `list`.

        Parameters
        ----------
        data : np.ndarray
            array sent from `DataWorker`
        """

        self.temporary_data_storage.append(data)

    @Slot()
    def set_APA_threshold(self) -> None:
        """Calculate the APA threshold based on the collected baseline trials.

        For every trial find the maximum lateral deviation of the CoP. Find the
        mean across all trials to get the average lateral CoP deviation during a
        step. Multiply this by the user-defined `threshold_percentage` to get
        the threshold for an anticipatory postural adjustment (APA).
        """

        maximum_lateral_deviation = list()

        for trial in self.baseline_data.keys():

            trial_data = self.baseline_data[trial].copy()
            cop_mediolateral = self.calculate_APA(trial_data)
            maximum_lateral_deviation.append(max(cop_mediolateral, key=abs))

        mean_maximum_lateral_deviation = np.mean(maximum_lateral_deviation)
        apa_threshold = self.threshold_percentage * mean_maximum_lateral_deviation / 100

        self.threshold_label.setText(f"APA Threshold: {round(apa_threshold, 4)}")

    @Slot(str)
    def update_threshold_percentage(self, percentage: str) -> None:
        self.threshold_percentage = int(percentage)
