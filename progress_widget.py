# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtWidgets


class ProgressWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.label = QtWidgets.QLabel()
        self.label.setText("Ready to collect")
        self.label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.setFixedWidth(200)

    def update_label(self, txt):
        self.label.setText(txt)
