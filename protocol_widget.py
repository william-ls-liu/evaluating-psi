# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot, Signal
import numpy as np


class ProtocolWidget(QWidget):
    """This widget holds methods related to PSI protocol."""

    collect_baseline_button_signal = Signal()

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        # Create a heading for the Widget
        self.progress_label = QLabel()
        self.progress_label.setText("PSI Protocol Collection Status")
        self.progress_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.progress_label.setWordWrap(True)

        # Create buttons for collecting baseline APA
        self.collect_baseline_button = QPushButton(parent=self, text="Collect baseline step")
        self.collect_baseline_button.setEnabled(False)
        self.collect_baseline_button.clicked.connect(self.collect_baseline_button_clicked)

        self.finish_baseline_button = QPushButton(parent=self, text="Finish baseline collection")
        self.finish_baseline_button.setEnabled(False)

        # Create buttons for starting/stopping the protocol
        self.start_trial_button = QPushButton(parent=self, text="Start Trial")
        self.start_trial_button.setEnabled(False)

        self.stop_trial_button = QPushButton(parent=self, text="Stop Trial")
        self.stop_trial_button.setEnabled(False)

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(self.progress_label)
        layout.addWidget(self.collect_baseline_button)
        layout.addWidget(self.finish_baseline_button)
        layout.addWidget(self.start_trial_button)
        layout.addWidget(self.stop_trial_button)

        self.setLayout(layout)
        self.setFixedWidth(300)

    def collect_baseline_button_clicked(self):
        self.collect_baseline_button_signal.emit()

    @Slot(bool)
    def toggle_collect_baseline_button(self, check_state):
        self.collect_baseline_button.setEnabled(check_state)

    @Slot(np.ndarray)
    def receive_data(self, data: np.ndarray):
        pass

    def enable_finish_baseline_button(self):
        self.finish_baseline_button.setEnabled(True)

    def disable_finish_baseline_button(self):
        self.finish_baseline_button.setEnabled(False)

    def enable_start_trial_button(self):
        self.start_trial_button.setEnabled(True)

    def disable_start_trial_button(self):
        self.start_trial_button.setEnabled(False)

    def enable_stop_trial_button(self):
        self.stop_trial_button.setEnabled(True)

    def disable_stop_trial_button(self):
        self.stop_trial_button.setEnabled(False)
