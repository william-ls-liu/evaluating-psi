# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QMessageBox, QComboBox, QGridLayout, QCheckBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot, Signal, Qt
from baseline_graph_viewer import GraphDialog
import numpy as np

# How long (ms) quiet stance lasts before patient is instructed to take a step
QUIET_STANCE_DURATION = 5000

# Default fonts
DEFAULT_FONT = QFont("Arial", 12)
DEFAULT_FONT_BOLD = QFont("Arial", 14, QFont.Bold)


def calculate_force_delta(force: list):
    """Calculate the change in force relative to quiet stance.

    The relative change is force is found by subtracting the mean of the force
    during quiet stance from the force values.

    Parameters
    ----------
    force : list
        a list of time-series force data along a single axis

    Returns
    -------
    list
        a list of time-series force data, corrected for quiet stance
    """

    quiet_stance = force[:QUIET_STANCE_DURATION]
    force_during_quiet_stance = np.mean(quiet_stance)

    return [f - force_during_quiet_stance for f in force]


class ProtocolWidget(QWidget):
    """Sidebar with buttons that control data collection and display progress.

    Attributes
    ----------
    start_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `start_baseline_button` is clicked
    stop_baseline_signal : PySide6.QtCore.Signal
        a signal that is emitted when `stop_baseline_button` is clicked
    connect_signal : PySide6.QtCore.Signal
        a signal that connects this widget to the data stream from the DAQ
    disconnect_signal : PySide6.QtCore.Signal
        a signal that disconnects this widget from the data stream
    """

    start_baseline_signal = Signal()
    stop_baseline_signal = Signal()
    connect_signal = Signal()
    disconnect_signal = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Create a heading for the Widget
        self.progress_label = QLabel(parent=self)
        self.progress_label.setText("Protocol Status")
        self.progress_label.setFont(DEFAULT_FONT_BOLD)
        self.progress_label.setWordWrap(True)

        # Create buttons for starting/stopping the protocol
        self.start_trial_button = QPushButton(parent=self, text="Start Trial")
        self.start_trial_button.setEnabled(False)

        self.stop_trial_button = QPushButton(parent=self, text="Stop Trial")
        self.stop_trial_button.setEnabled(False)

        # Create button to enable/disable stimulus
        self.enable_stimulus_button = QCheckBox(text="Enable stimulus", parent=self)
        self.enable_stimulus_button.setFont(DEFAULT_FONT)

        # Initiate variable to store the baseline data
        self.baseline_data = dict()
        self.temporary_data_storage = list()

        # Create the parent layout
        layout = QGridLayout()

        # Create layout for the baseline buttons
        baseline_layout = QGridLayout()

        # Create a layout for the threshold buttons
        threshold_layout = QGridLayout()

        # Populate the layout
        layout.addWidget(self.progress_label, 0, 0, Qt.AlignTop | Qt.AlignHCenter)
        layout.addLayout(baseline_layout, 1, 0)
        layout.addLayout(threshold_layout, 2, 0)
        layout.addWidget(self.enable_stimulus_button, 3, 0)
        layout.addWidget(self.start_trial_button, 4, 0)
        layout.addWidget(self.stop_trial_button, 5, 0)

        # Populate the baseline and threshold layouts
        self._create_baseline_layout(baseline_layout)
        self._create_threshold_layout(threshold_layout)

        self.setLayout(layout)
        self.setFixedWidth(300)

    def _create_baseline_layout(self, layout: QGridLayout) -> None:
        """Create buttons for baseline collection, add them to a layout.

        Parameters
        ----------
        layout : PySide6.QtWidgets.QGridLayout
            an empty grid layout
        """

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
        self.baseline_trial_counter_label.setFont(DEFAULT_FONT)
        self.baseline_trial_counter_label.setWordWrap(True)
        self._update_baseline_trial_counter_label()

        layout.addWidget(self.start_baseline_button, 0, 0)
        layout.addWidget(self.stop_baseline_button, 0, 1)
        layout.addWidget(self.collect_baseline_button, 1, 0, 1, 2)
        layout.addWidget(self.finish_baseline_button, 2, 0, 1, 2)
        layout.addWidget(self.baseline_trial_counter_label, 3, 0, 1, -1, Qt.AlignTop)

    def _create_threshold_layout(self, layout: QGridLayout) -> None:
        """Create buttons for setting/displaying APA threshold.

        Parameters
        ----------
        layout : PySide6.QtWidgets.QGridLayout
            an empty grid layout
        """

        # ComboBox for specifying % threshold
        self.threshold_percentage_entry = QComboBox(parent=self)
        self.threshold_percentage_entry.addItems([str(i*5) for i in range(1, 21)])
        self.threshold_percentage_entry.currentTextChanged.connect(self.update_threshold_percentage)
        self.threshold_percentage = int(self.threshold_percentage_entry.currentText())  # Initialize a default value

        # Label for the ComboBox
        self.threshold_percentage_label = QLabel(parent=self)
        self.threshold_percentage_label.setFont(DEFAULT_FONT)
        self.threshold_percentage_label.setWordWrap(True)
        self.threshold_percentage_label.setText(
            "Select a % for the threshold:"
        )

        # Label for tracking the APA threshold
        self.threshold = None
        self.threshold_label = QLabel(parent=self)
        self.threshold_label.setFont(DEFAULT_FONT)
        self.threshold_label.setWordWrap(True)
        self._update_APA_threshold_label()

        layout.addWidget(self.threshold_percentage_entry, 0, 3)
        layout.addWidget(self.threshold_percentage_label, 0, 0, 1, 3)
        layout.addWidget(self.threshold_label, 1, 0, 1, -1, Qt.AlignTop)

    def _update_baseline_trial_counter_label(self) -> None:
        self.baseline_trial_counter_label.setText(
            f"Number of baseline trials collected: {self.baseline_trial_counter}"
        )

    def _update_APA_threshold_label(self) -> None:
        if self.threshold is None:
            self.threshold_label.setText("No baseline threshold set")
        else:
            self.threshold_label.setText(f"APA Threshold: {round(self.threshold, 4)}")

    @Slot(bool)
    def toggle_start_baseline_button(self, check_state) -> None:
        self.start_baseline_button.setEnabled(check_state)

    @Slot()
    def start_baseline_button_clicked(self):
        """Open blocking message when the user starts baseline APA collection.

        Window prompts user to Hardware Zero the force platform. User can also
        cancel the baseline collection.
        """

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
            self.threshold = None  # Clear any previously set APA threshold
            self._update_APA_threshold_label()
        elif ret == QMessageBox.Save:
            if self.threshold is None:
                self.update_threshold_percentage(self.threshold_percentage_entry.currentText())
            self.start_trial_button.setEnabled(True)

        if ret in {QMessageBox.Discard, QMessageBox.Save, QMessageBox.Yes}:
            self.start_baseline_button.setEnabled(True)
            self.stop_baseline_button.setEnabled(False)
            self.collect_baseline_button.setEnabled(False)
            self.stop_baseline_signal.emit()

    @Slot()
    def collect_baseline_button_clicked(self):
        self.connect_signal.emit()
        self.finish_baseline_button.setEnabled(True)
        self.collect_baseline_button.setEnabled(False)
        self.stop_baseline_button.setEnabled(False)

    @Slot()
    def finish_baseline_button_clicked(self):
        self.disconnect_signal.emit()
        self.collect_baseline_button.setEnabled(True)
        self.finish_baseline_button.setEnabled(False)
        self.stop_baseline_button.setEnabled(True)

        # Open the Graph Dialog
        self._show_baseline_graph()

    def _show_baseline_graph(self):
        """Display the lateral CoP data from the most recent trial.

        Open a dialog window with a graph of the lateral CoP position vs. time.
        User can choose to save the trial or discard it, depending on how the
        graph looks.
        """

        mediolateral_force = [row[0] for row in self.temporary_data_storage]
        corrected_mediolateral_force = calculate_force_delta(mediolateral_force)
        graph_dialog = GraphDialog(data=corrected_mediolateral_force, parent=self)
        graph_dialog.open()
        graph_dialog.finished.connect(self.handle_baseline_trial)

    @Slot(int)
    def handle_baseline_trial(self, result: int):
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

        self.temporary_data_storage.clear()

    @Slot(np.ndarray)
    def receive_data(self, data: np.ndarray) -> None:
        """Receives data from the `DataWorker` and stores it in a `list`.

        Parameters
        ----------
        data : np.ndarray
            array sent from `DataWorker`
        """

        self.temporary_data_storage.append(data)

    @Slot(str)
    def update_threshold_percentage(self, percentage: str) -> None:
        """Calculate the APA threshold based on the collected baseline trials.

        For every trial find the maximum mediolateral Force. Find the
        mean across all trials to get the average mediolateral Force during a
        step. Multiply this by the user-defined `threshold_percentage` to get
        the threshold for an anticipatory postural adjustment (APA).

        Parameters
        ----------
        percentage : str
            a string representing the threshold percentage
        """

        self.threshold_percentage = int(percentage)

        if self.baseline_trial_counter != 0:
            maximum_mediolateral_force = list()

            for trial in self.baseline_data.keys():

                trial_data = self.baseline_data[trial].copy()
                mediolateral_force = [row[0] for row in trial_data]
                corrected_mediolateral_force = calculate_force_delta(mediolateral_force)
                maximum_mediolateral_force.append(max(corrected_mediolateral_force, key=abs))

            mean_maximum_mediolateral_force = np.mean(maximum_mediolateral_force)
            self.threshold = self.threshold_percentage * mean_maximum_mediolateral_force / 100
            self._update_APA_threshold_label()
