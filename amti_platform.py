# Author: William Liu <liwi@ohsu.edu>

import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, TerminalConfiguration
from datetime import datetime
import numpy as np

# Start the task
task = nidaqmx.Task()

# Add channels to the task, use Referenced Single Ended to measure relative to GND
task.ai_channels.add_ai_voltage_chan(
    physical_channel="Dev1/ai1",
    min_val=-5,
    max_val=5,
    terminal_config=TerminalConfiguration.RSE)

# Configure the hardware clock for sample timing
task.timing.cfg_samp_clk_timing(rate=1, sample_mode=AcquisitionType.CONTINUOUS)

# Set up the loop to collect samples
count = 0
start = datetime.now()
end = start
while (end - start).total_seconds() < 10:
    buffer = task.read()
    print(buffer)
    end = datetime.now()

task.close()
