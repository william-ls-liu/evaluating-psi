# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtWidgets, QtCore


class ProgressWidget(QtWidgets.QWidget):
    enable_stimulus_signal = QtCore.Signal(bool)

    def __init__(self, parent):
        super().__init__(parent=parent)

        # Create a label to report on the status of the protocol
        self.progress_label = QtWidgets.QLabel()
        self.progress_label.setText("Ready to collect")
        self.progress_label.setWordWrap(True)

        # Create a checkbox to enable the stimulus
        self.enable_stimulus_checkbox = QtWidgets.QCheckBox(parent=self)
        self.enable_stimulus_checkbox.setText("Enable Stimulus")
        self.enable_stimulus_checkbox.stateChanged.connect(self.enable_stimulus_checkbox_statechanged)

        # Create a label to display the currently set APA threshold
        self.apa_threshold_label = QtWidgets.QLabel(parent=self)
        self.apa_threshold_label.setText("APA Threshold: 5")

        # Create a slider to set the threshold for APA
        self.threshold_slider = QtWidgets.QSlider(parent=self)
        self.threshold_slider.setMinimum(1)
        self.threshold_slider.setMaximum(50)
        self.threshold_slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.threshold_slider.setValue(5)
        self.threshold_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        self.threshold_slider.valueChanged.connect(self.update_apa_label)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.progress_label)
        layout.addWidget(self.enable_stimulus_checkbox)
        layout.addWidget(self.apa_threshold_label)
        layout.addWidget(self.threshold_slider)

        self.setLayout(layout)

        self.setFixedWidth(200)

    def update_progress_label(self, txt):
        """Receives a signal from the MainWindow and updates the label with the provided text."""
        self.progress_label.setText(txt)

    def enable_stimulus_checkbox_statechanged(self):
        """
        Emits a signal containing the state of the enable stimulus checkbox,
        every time the state of the checkbox changes.
        """
        self.enable_stimulus_signal.emit(self.enable_stimulus_checkbox.isChecked())

    def update_apa_label(self, value):
        """Update the """
        self.apa_threshold_label.setText(f"APA Threshold: {value}")
