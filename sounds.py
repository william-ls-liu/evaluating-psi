# Author: William Liu <liwi@ohsu.edu>

from PySide6 import QtMultimedia, QtCore


class Countdown(QtMultimedia.QSoundEffect):
    """This is a simple start tone with 3 initial beeps followed by the GO signal."""
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setSource(QtCore.QUrl.fromLocalFile("start_countdown.wav"))
        self.setVolume(1)


class StartTone(QtMultimedia.QSoundEffect):
    """A single start tone."""
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setSource(QtCore.QUrl.fromLocalFile("start_tone.wav"))
        self.setVolume(1)

