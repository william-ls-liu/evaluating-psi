# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QMessageBox, QComboBox, QGridLayout, QCheckBox,
                               QFileDialog, QLineEdit)
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot, Signal, Qt, QTimer
from graph_viewer import BaselineGraphDialog, StepGraphDialog
import numpy as np
from scipy.signal import find_peaks
import csv
from datetime import datetime

# How long (ms) quiet stance lasts before patient is instructed to take a step
QUIET_STANCE_DURATION = 5_000

# Default fonts
DEFAULT_FONT = QFont("Arial", 12)
DEFAULT_FONT_BOLD = QFont("Arial", 14, QFont.Bold)

# Z-offset of the force platform, in meters
ZOFF = -0.040934

# Indexes of platform axes
FX = 0
FY = 1
FZ = 2
MX = 3
MY = 4
MZ = 5
EMG_1 = 6
EMG_2 = 7
STIM = 8


def get_mediolateral_force(data: list) -> list:
    """Extract the force along the x axis (mediolateral) and return it.

    Parameters
    ----------
    data : list
        list of raw data for all channels

    Returns
    -------
    list
        list of force data along the x axis
    """

    return [row[FX] for row in data]


def calculate_force_delta(force: list) -> np.ndarray:
    """Calculate the change in force relative to quiet stance.

    The relative change of force is found by subtracting the mean of the force
    during quiet stance from the force values.

    Parameters
    ----------
    force : list
        a list of time-series force data along a single axis

    Returns
    -------
    np.ndarray
        an array of time-series force data, corrected for quiet stance
    """

    quiet_stance = force[:QUIET_STANCE_DURATION]
    force_during_quiet_stance = np.mean(quiet_stance)

    return np.array([f - force_during_quiet_stance for f in force])


def calculate_center_of_pressure(fx, fy, fz, mx, my) -> tuple:
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

    cop_x = (-1) * ((my + (ZOFF * fx)) / fz)
    cop_y = ((mx - (ZOFF * fy)) / fz)

    return cop_x, cop_y


def create_csv_export(
        step_data: list,
        quiet_stance_data: list,
        notes: str,
        stim_status: bool,
        threshold: float,
        threshold_percent: int,
        patient_id: str,
        patient_foot_measurement: str,
        trial_type: str
) -> list:

    """Save data from a step trial as a .csv file.

    Parameters
    ----------
    step_data : list
        data recorded during a step trial
    quiet_stance_data : list
        data recorded during the quiet stance that precedes a step trial
    notes : str
        a str of user-entered notes
    stim_status : bool
        a bool to indicate whether stimulation was enabled during the trial
    threshold : float
        the threshold used to determine an APA
    threshold_percent : int
        the percent used to calculate threshold
    patient_id : str
        patient identifier
    patient_foot_measurement
        patient's foot size
    trial_type : str
        a string that specifies the type of trial that was collected
    """

    datetime_of_export = str(datetime.now())
    export = [
        ["Date/Time of Export:", datetime_of_export],
        ["Patient ID:", patient_id],
        ["Foot Measurement:", patient_foot_measurement],
        ["Trial Type:", trial_type],
        ["APA Threshold:", threshold],
        ["Threshold Percentage:", threshold_percent],
        ["Stimulus Enabled:", stim_status],
        ["Collection Notes:", notes],
        [
            'Fx (N)', 'Fy (N)', 'Fz (N)',
            'Mx (N/m)', 'My (N/m)', 'Mz (N/m)',
            'EMG_Tib (V)', 'EMG_Sol (V)',
            'CoPx (m)', 'CoPy (m)',
            'Stim'
        ]
    ]

    full_trial_data = [*quiet_stance_data, *step_data]

    for row in full_trial_data:
        CoPx, CoPy = calculate_center_of_pressure(row[FX], row[FY], row[FZ], row[MX], row[MY])
        new_row = [row[FX], row[FY], row[FZ], row[MX], row[MY], row[MZ], row[EMG_1], row[EMG_2], CoPx, CoPy, row[STIM]]
        export.append(new_row)

    return export


class ProtocolWidget(QWidget):
    """Sidebar with buttons that control data collection and display progress.

    Attributes
    ----------
    disable_record_button_signal : PySide6.QtCore.Signal
        a signal to disable the recording button
    enable_record_button_signal : PySide6.QtCore.Signal
        a signal to enable the recording button
    connect_signal : PySide6.QtCore.Signal
        a signal that connects this widget to the data stream from the DAQ
    disconnect_signal : PySide6.QtCore.Signal
        a signal that disconnects this widget from the data stream
    """

    disable_record_button_signal = Signal()
    enable_record_button_signal = Signal()
    connect_signal = Signal(str)
    disconnect_signal = Signal(str)
    stimulus_signal = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Create a heading for the Widget
        self.progress_label = QLabel(parent=self)
        self.progress_label.setText("Protocol Status")
        self.progress_label.setFont(DEFAULT_FONT_BOLD)
        self.progress_label.setWordWrap(True)

        # Initiate variable to store the baseline data
        self.baseline_data = dict()
        self.incoming_data_storage = list()
        self.quiet_stance_data = list()

        # Initiate variables to store whether an APA has been detected
        self.APA_detected = False

        # Initiate variables to store patient demographics
        self.patient_id = None
        self.patient_foot_measurement = None
        self.demographics_saved = False

        # Create the parent layout
        layout = QGridLayout()

        # Create layout for entering patient info
        patient_info_layout = QGridLayout()

        # Create layout for the baseline buttons
        baseline_layout = QGridLayout()

        # Create a layout for the threshold buttons
        threshold_layout = QGridLayout()

        # Create a layout for the trial buttons
        trial_layout = QGridLayout()

        # Populate the layout
        layout.addWidget(self.progress_label, 0, 0, Qt.AlignTop | Qt.AlignHCenter)
        layout.addLayout(patient_info_layout, 1, 0, Qt.AlignTop)
        layout.addLayout(baseline_layout, 2, 0)
        layout.addLayout(threshold_layout, 3, 0)
        layout.addLayout(trial_layout, 4, 0)

        # Populate the baseline and threshold layouts
        self._create_patient_info_layout(patient_info_layout)
        self._create_baseline_layout(baseline_layout)
        self._create_threshold_layout(threshold_layout)
        self._create_trial_layout(trial_layout)

        self.setLayout(layout)
        self.setFixedWidth(300)

    def _create_patient_info_layout(self, layout: QGridLayout) -> None:
        """Create the layout for entering patient info

        Parameters
        ----------
        layout : PySide6.QtWidgets.QGridLayout
            an empty grid layout
        """

        self.patient_id_entry = QLineEdit(parent=self)
        self.patient_id_entry.setPlaceholderText("Enter ID here")
        patient_id_label = QLabel("Patient ID", parent=self)
        patient_id_label.setFont(DEFAULT_FONT)

        self.foot_size_entry = QLineEdit(parent=self)
        self.foot_size_entry.setPlaceholderText("Enter foot measurement here")
        foot_size_label = QLabel("Foot Measurement", parent=self)
        foot_size_label.setFont(DEFAULT_FONT)

        self.store_demographics_button = QPushButton(parent=self, text="Store Patient Info")
        self.store_demographics_button.setCheckable(True)
        self.store_demographics_button.setChecked(True)
        self.store_demographics_button.clicked.connect(self.demographics_button_clicked)

        layout.addWidget(patient_id_label, 0, 0)
        layout.addWidget(self.patient_id_entry, 0, 1)
        layout.addWidget(foot_size_label)
        layout.addWidget(self.foot_size_entry, 1, 1)
        layout.addWidget(self.store_demographics_button, 2, 0, 1, 2)

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

        self.finish_baseline_button = QPushButton(parent=self, text="Finish step")
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
        self.threshold_percentage_entry.currentTextChanged.connect(self._set_APA_threshold)
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

    def _create_trial_layout(self, layout: QGridLayout) -> None:
        """Add widgets to the trial layout.

        Parameters
        ----------
        layout : PySide6.QtWidgets.QGridLayout
            an empty grid layout
        """

        # Create combobox to select type of trial
        self.trial_select_combobox = QComboBox(parent=self)
        self.trial_select_combobox.addItems(["Standing Trial", "Step Trial"])
        self.trial_select_combobox.currentTextChanged.connect(self._set_trial_type)

        # Create button to enable/disable stimulus
        self.enable_stimulus_button = QCheckBox(text="Enable stimulus", parent=self)
        self.enable_stimulus_button.setFont(DEFAULT_FONT)
        self.enable_stimulus_button.stateChanged.connect(self.enable_stimulus)
        self.stimulus_enabled = self.enable_stimulus_button.isChecked()

        # Initialize the trial type, must happen after enable_stimulus_button has been created
        self._set_trial_type(self.trial_select_combobox.currentText())  # Initialize the trial type

        # Create buttons for starting/stopping the protocol
        self.start_trial_button = QPushButton(parent=self, text="Start Trial")
        self.start_trial_button.setEnabled(False)
        self.start_trial_button.clicked.connect(self.start_trial_button_clicked)

        self.stop_trial_button = QPushButton(parent=self, text="Stop Trial")
        self.stop_trial_button.setEnabled(False)
        self.stop_trial_button.clicked.connect(self.stop_trial_button_clicked)

        # Create label to track number of collected trials
        self.trial_counter = 0
        self.trial_counter_label = QLabel(parent=self)
        self.trial_counter_label.setFont(DEFAULT_FONT)
        self._update_trial_counter_label()

        # Add widgets to the layout
        layout.addWidget(self.trial_select_combobox, 0, 0)
        layout.addWidget(self.enable_stimulus_button, 1, 0)
        layout.addWidget(self.start_trial_button, 2, 0)
        layout.addWidget(self.stop_trial_button, 3, 0)
        layout.addWidget(self.trial_counter_label, 4, 0)

    def _update_baseline_trial_counter_label(self) -> None:
        self.baseline_trial_counter_label.setText(
            f"Number of baseline trials collected: {self.baseline_trial_counter}"
        )

    def _update_APA_threshold_label(self) -> None:
        if self.threshold is None:
            self.threshold_label.setText("No baseline threshold set")
        else:
            self.threshold_label.setText(f"APA Threshold: {round(self.threshold, 4)}")

    def _update_trial_counter_label(self) -> None:
        self.trial_counter_label.setText(
            f"Number of trials collected: {self.trial_counter}"
        )

    @Slot(bool)
    def demographics_button_clicked(self, check_state: bool) -> None:
        """Handle when user clicks `store_demographics_button`.

        If user has not entered both a Patient ID and the Foot Measurement then
        show a pop-up warning message telling them to do so. They will not be
        able to collect any data (including baseline data) until they do so.

        Parameters
        ----------
        check_state : bool
            the check state of the `store_demographics_button`
        """

        # Get entry from the text boxes, remove whitespace at beginning and end
        self.patient_id = self.patient_id_entry.text().strip()
        self.patient_foot_measurement = self.foot_size_entry.text().strip()

        if check_state:
            self.store_demographics_button.setText("Store Patient Info")
        else:
            if self.patient_id == "" or self.patient_foot_measurement == "":
                message_box = QMessageBox(self)
                message_box.setWindowTitle("Warning!")
                message_box.setText(
                    "You must enter a value for both the Patient ID and the Foot Measurement."
                )
                message_box.setIcon(QMessageBox.Warning)
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec()
                self.store_demographics_button.setChecked(True)

            else:
                self.store_demographics_button.setText("Edit Patient Info")

        # Disable/enable the text entrys as appropriate
        self.patient_id_entry.setEnabled(self.store_demographics_button.isChecked())
        self.foot_size_entry.setEnabled(self.store_demographics_button.isChecked())

        # Update the state variable to keep track of whether demographics info is saved
        self.demographics_saved = not self.store_demographics_button.isChecked()

    @Slot(bool)
    def toggle_baseline_buttons(self, check_state: bool) -> None:
        self.start_baseline_button.setEnabled(check_state)
        self.stop_baseline_button.setEnabled(check_state)

    @Slot()
    def start_baseline_button_clicked(self):
        """Open blocking message when the user starts baseline APA collection.

        Window prompts user to Hardware Zero the force platform. User can also
        cancel the baseline collection.
        """

        if self.demographics_saved:
            message_box = QMessageBox(self)
            message_box.setWindowTitle("Attention!")
            message_box.setText(
                "Instruct patient to step off the platform,\n"
                "then hit the Auto-Zero button on the amplifier.\n"
                "When you have done this click OK.")
            message_box.setIcon(QMessageBox.Information)
            message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

            button = message_box.exec()

            if button == QMessageBox.Ok:
                self.disable_record_button_signal.emit()
                self.stop_baseline_button.setEnabled(True)
                self.collect_baseline_button.setEnabled(True)
                self.start_baseline_button.setEnabled(False)
                self.start_trial_button.setEnabled(False)

        else:
            message_box = QMessageBox(self)
            message_box.setWindowTitle("Warning!")
            message_box.setText(
                "Patient ID and Foot Measurement have not been saved.\n"
                "Before proceeding you must enter a Patient ID and Foot Measurement."
            )
            message_box.setIcon(QMessageBox.Warning)
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec()

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
            self.start_trial_button.setEnabled(False)
        elif ret == QMessageBox.Save:
            if self.threshold is None:
                self._set_APA_threshold(self.threshold_percentage_entry.currentText())
            self.start_trial_button.setEnabled(True)

        if ret in {QMessageBox.Discard, QMessageBox.Save, QMessageBox.Yes}:
            self.start_baseline_button.setEnabled(True)
            self.stop_baseline_button.setEnabled(False)
            self.collect_baseline_button.setEnabled(False)
            self.enable_record_button_signal.emit()

    @Slot()
    def collect_baseline_button_clicked(self):
        self.collect_baseline_button.setEnabled(False)
        self.stop_baseline_button.setEnabled(False)
        self._collect_quiet_stance("baseline")

    @Slot()
    def finish_baseline_button_clicked(self):
        self.disconnect_signal.emit("baseline")
        self.collect_baseline_button.setEnabled(True)
        self.finish_baseline_button.setEnabled(False)
        self.stop_baseline_button.setEnabled(True)

        # Open the Graph Dialog
        self._show_baseline_graph()

    def _show_baseline_graph(self):
        """Display the mediolateral force data from the most recent trial.

        Open a dialog window with a graph of the lateral CoP position vs. time.
        User can choose to save the trial or discard it, depending on how the
        graph looks.
        """

        mediolateral_force = get_mediolateral_force(self.incoming_data_storage)
        corrected_mediolateral_force = calculate_force_delta(mediolateral_force)
        peaks, _ = find_peaks(corrected_mediolateral_force, height=10, prominence=10)
        valleys, _ = find_peaks(-corrected_mediolateral_force, height=10, prominence=10)
        graph_dialog = BaselineGraphDialog(corrected_mediolateral_force, peaks, valleys, parent=self)
        graph_dialog.open()
        graph_dialog.finished.connect(
            lambda result: self.handle_baseline_trial(result, corrected_mediolateral_force, peaks, valleys)
        )

    @Slot(int)
    def handle_baseline_trial(
        self,
        result: int,
        corrected_mediolateral_force: np.ndarray,
        peaks: np.ndarray,
        valleys: np.ndarray
    ):

        """Save/discard the most recent baseline trial, based on user selection.

        Parameters
        ----------
        result : int
            result code emitted when `GraphDialog` window is closed, 1 indicates
            user wants to save the trial
        corrected_mediolateral_force : np.ndarray
            array of corrected mediolateral force data
        peaks : np.ndarray
            array containing indexes of peaks in mediolateral force data
        valleys : np.ndarray
            array containing indexes of valleys in mediolateral force data
        """

        if result == 1:
            self.baseline_trial_counter += 1
            # During a step there is usually a M/L force in the direction of the
            # swing leg followed by a M/L force in the direction of the stance
            # leg. To keep the code functional for a left or right step, look
            # for whichever occurs first, a peak or a valley, then take that as
            # the APA.
            if peaks[0] < valleys[0]:
                max_force_during_apa = corrected_mediolateral_force[peaks[0]]
            else:
                max_force_during_apa = corrected_mediolateral_force[valleys[0]]

            self.baseline_data[f"trial {self.baseline_trial_counter}"] = max_force_during_apa
            self._update_baseline_trial_counter_label()
            self._set_APA_threshold(self.threshold_percentage_entry.currentText())

        self.incoming_data_storage.clear()

    @Slot()
    def start_trial_button_clicked(self) -> None:
        self.start_trial_button.setEnabled(False)
        self.start_baseline_button.setEnabled(False)
        self.trial_select_combobox.setEnabled(False)
        self.enable_stimulus_button.setEnabled(False)
        self.disable_record_button_signal.emit()
        if self.trial_type == "Step Trial":
            self._collect_quiet_stance("quiet stance")
        elif self.trial_type == "Standing Trial":
            self._collect_quiet_stance("standing quiet stance")
        else:
            raise NameError(f"{self.trial_type} was not found.")

    @Slot()
    def stop_trial_button_clicked(self) -> None:
        if self.trial_type == "Step Trial":
            self.disconnect_signal.emit("step")
        elif self.trial_type == "Standing Trial":
            self.disconnect_signal.emit("standing")
        self.enable_record_button_signal.emit()
        self.start_trial_button.setEnabled(True)
        self.stop_trial_button.setEnabled(False)
        self.start_baseline_button.setEnabled(True)
        self.trial_select_combobox.setEnabled(True)
        self.enable_stimulus_button.setEnabled(True)
        self.APA_detected = False

        # Open the GraphDialog
        self._show_step_graph()

    def _show_step_graph(self):
        """Open a window with graphs of the data collected during a step trial.

        User has the choice to save the trial or discard it, based on how the
        data looks.
        """

        graph_dialog = StepGraphDialog(self.incoming_data_storage, parent=self)
        graph_dialog.finished.connect(self.handle_step_trial)
        graph_dialog.notes_signal.connect(self.receive_collection_notes)
        graph_dialog.open()

    @Slot(int)
    def handle_step_trial(self, result: int):
        """Save or discard a step trial."""

        if result == 1:

            fname = QFileDialog.getSaveFileName(
                parent=self,
                caption="Select a location to save the trial.",
                filter="*.csv"
            )

            if fname[0] != '':

                to_csv = create_csv_export(
                    self.incoming_data_storage,
                    self.quiet_stance_data,
                    self.collection_notes,
                    self.stimulus_enabled,
                    self.threshold,
                    self.threshold_percentage,
                    self.patient_id,
                    self.patient_foot_measurement,
                    self.trial_type
                )
                file = open(fname[0], 'w+', newline='')
                with file:
                    write = csv.writer(file)
                    write.writerows(to_csv)

                self.trial_counter += 1
                self._update_trial_counter_label()
                del self.collection_notes

        self.incoming_data_storage.clear()
        self.quiet_stance_data.clear()

    @Slot(str)
    def receive_collection_notes(self, notes: str) -> None:
        """Slot that receives notes entered in the step graph dialog.

        Parameters
        ----------
        notes : str
            a str of user-entered notes
        """

        self.collection_notes = notes

    @Slot(int)
    def enable_stimulus(self) -> None:
        self.stimulus_enabled = self.enable_stimulus_button.isChecked()

    @Slot(np.ndarray)
    def receive_data(self, data: np.ndarray) -> None:
        """Receives data from the `DataWorker` and stores it in a `list`.

        Parameters
        ----------
        data : np.ndarray
            array sent from `DataWorker`
        """

        self.incoming_data_storage.append(np.append(data, 0))

    @Slot(np.ndarray)
    def receive_step_data(self, data: np.ndarray) -> None:
        """Receives data from the `DataWorker` and compares to APA threshold.

        Parameters
        ----------
        data : np.ndarray
            array of raw data read from the DAQ
        """

        stim = 0
        if self.APA_detected is False:
            if abs(data[FX] - self._quiet_stance_force) > abs(self.threshold):
                if self.stimulus_enabled:
                    self.stimulus_signal.emit()
                    stim = 1
                self.APA_detected = True

        self.incoming_data_storage.append(np.append(data, stim))

    @Slot(np.ndarray)
    def receive_standing_trial_data(self, data: np.ndarray) -> None:
        """Receives data from the `DataWorker` for a standing trial.

        Every 10,000 samples (10 seconds) a stimulus is delivered.

        Parameters
        ----------
        data : np.ndarray
            array of raw data read from the DAQ
        """

        if len(self.incoming_data_storage) % 10_000 == 0:
            self.stimulus_signal.emit()
            self.incoming_data_storage.append(np.append(data, 1))
        else:
            self.incoming_data_storage.append(np.append(data, 0))

    @Slot(str)
    def _set_APA_threshold(self, percentage: str) -> None:
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
                maximum_mediolateral_force.append(self.baseline_data[trial])

            mean_maximum_mediolateral_force = np.mean(maximum_mediolateral_force)
            self.threshold = self.threshold_percentage * mean_maximum_mediolateral_force / 100
            self._update_APA_threshold_label()

    @Slot(str)
    def _set_trial_type(self, type: str) -> None:
        """Set what type of trial, Standing Trial | Step Trial, to use.

        Parameters
        ----------
        type : str
            the type of trial to use
        """

        self.trial_type = type

        if type == "Standing Trial":
            self.enable_stimulus_button.setChecked(True)
            self.enable_stimulus_button.setEnabled(False)
        elif type == "Step Trial":
            self.enable_stimulus_button.setChecked(False)
            self.enable_stimulus_button.setEnabled(True)

    def _collect_quiet_stance(self, stage: str) -> None:
        """Collect data for `QUIET_STANCE_DURATION` amount of time.

        Parameters
        ----------
        stage : str
            a string representing the current stage of the protocol
        """

        quiet_stance_timer = QTimer(parent=self)
        quiet_stance_timer.setTimerType(Qt.PreciseTimer)
        quiet_stance_timer.setInterval(QUIET_STANCE_DURATION)
        quiet_stance_timer.setSingleShot(True)

        if stage == "baseline":
            quiet_stance_timer.timeout.connect(lambda: self.finish_baseline_button.setEnabled(True))
        elif stage == "quiet stance":
            quiet_stance_timer.timeout.connect(self.calculate_quiet_stance)
            quiet_stance_timer.timeout.connect(lambda: self.disconnect_signal.emit(stage))
        elif stage == "standing quiet stance":
            quiet_stance_timer.timeout.connect(self.standing_trial)
            quiet_stance_timer.timeout.connect(lambda: self.disconnect_signal.emit(stage))

        quiet_stance_timer.start()
        self.connect_signal.emit(stage)

    @Slot()
    def calculate_quiet_stance(self) -> None:
        """Calculate the mean mediolateral force during quiet stance."""

        self._quiet_stance_force = np.mean(get_mediolateral_force(self.incoming_data_storage))
        self.quiet_stance_data = self.incoming_data_storage.copy()
        self.incoming_data_storage.clear()
        wait_timer = QTimer(parent=self)
        wait_timer.setSingleShot(True)
        wait_timer.setInterval(500)
        wait_timer.timeout.connect(lambda: self.connect_signal.emit("step"))
        wait_timer.timeout.connect(lambda: self.stop_trial_button.setEnabled(True))
        wait_timer.start()

    @Slot()
    def standing_trial(self) -> None:
        """Runs the protocol for a standing trial.

        A standing trial consists of 10 successive stimuli, with 10 seconds
        between each stimulus. This method creates a timer that will stop the
        data collection after 10 stimuli have been deliverd to the patient.
        """

        self.quiet_stance_data = self.incoming_data_storage.copy()
        self.incoming_data_storage.clear()

        standing_timer = QTimer(parent=self)
        standing_timer.setSingleShot(True)
        standing_timer.setInterval(95_000)
        standing_timer.setTimerType(Qt.PreciseTimer)
        standing_timer.timeout.connect(self.stop_trial_button.click)

        wait_timer = QTimer(parent=self)
        wait_timer.setSingleShot(True)
        wait_timer.setInterval(500)
        wait_timer.timeout.connect(lambda: self.connect_signal.emit("standing"))
        wait_timer.timeout.connect(lambda: self.stop_trial_button.setEnabled(True))
        wait_timer.timeout.connect(standing_timer.start)
        wait_timer.start()
