# Author: William Liu <liwi@ohsu.edu>

from PySide6.QtGui import QFont

# How long (ms) quiet stance lasts before patient is instructed to take a step
QUIET_STANCE_DURATION = 5_000

# Default fonts
DEFAULT_FONT = QFont("Arial", 12)
DEFAULT_FONT_BOLD = QFont("Arial", 14, QFont.Bold)

# Z-offset of the force platform, in meters
ZOFF = -0.040934

# AMTI Gen5 Amplifier ranges, changes based on gain and excitation voltage
FX_MIN = -192.73
FX_MAX = 192.73
FY_MIN = -193.55
FY_MAX = 193.55
FZ_MIN = -1504.76
FZ_MAX = 1504.76
MX_MIN = -155.80
MX_MAX = 155.80
MY_MIN = -154.96
MY_MAX = 154.96
MZ_MIN = -37.77
MZ_MAX = 37.77

# Indexes of platform axes and EMG channels. This is determined by the analog
# input channels on the DAQ that are used, they are in ascending numeric order.
FX = 0
FY = 1
FZ = 2
MX = 3
MY = 4
MZ = 5
EMG_1 = 6  # Physical EMG #7
EMG_2 = 7  # Physical EMG #6
STIM = 8

# How many seconds should be displayed on the graphs before they "roll over"
SECONDS_TO_SHOW = 5

# Minimum vertical force to show CoP graph, in Newtons
MINIMUM_VERTICAL_FORCE = 10
