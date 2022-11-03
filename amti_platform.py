# Author: William Liu <liwi@ohsu.edu>

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
from datetime import datetime
import numpy as np

# These change when you change excitation V and gain
analog_sens = np.array([6.4717, 6.4442, 1.6602, 16.0339, 16.1206, 33.0285])

# Test the device
dev = nidaqmx.system.Device('Dev1')
dev.self_test_device()
print(dev.product_type)

# Start the task
task = nidaqmx.Task()

# Add channels to the task, use Referenced Single Ended to measure relative to GND
task.ai_channels.add_ai_voltage_chan(
    physical_channel="Dev1/ai1:6",
    min_val=-5,
    max_val=5,
    terminal_config=TerminalConfiguration.RSE)

# Configure the hardware clock for sample timing
task.timing.cfg_samp_clk_timing(rate=50, sample_mode=AcquisitionType.CONTINUOUS)

# Start the task
task.start()

# Set up the loop to collect samples
count = 0
start = datetime.now()
end = start
data = []
while (end - start).total_seconds() < 300:
    buffer = np.array(task.read())
    converted = buffer / analog_sens
    data.append(converted)
    end = datetime.now()

print(np.mean(data, axis=0))

# Stop the task and then clear it
task.stop()
task.close()
