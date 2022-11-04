# Author: William Liu <liwi@ohsu.edu>

import nidaqmx
from nidaqmx.errors import DaqError
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import numpy as np

class DAQ:
    """This object represents a National Instruments DAQ Device."""

    def __init__(self, dev_name: str) -> None:
        """Initiate the device, perform basic self test."""
        self.dev_name = dev_name
        self.dev = nidaqmx.system.Device(self.dev_name)

        # Perform the self test
        self.dev.self_test_device()

        # Initiate variables to store state
        self.is_running = False
        self.is_task = False

    def create_task(self, channels_str: str):
        # I belive assigning a name to the task will cause an error when trying
        # to create multiple tasks, so I'm assigning it a name to prevent unintended
        # creation of tasks.
        if self.is_task:
            raise ValueError("Task is already running.")

        self.task = nidaqmx.Task(new_task_name="Active Task")
        self.is_task = True

        # Add the channels to the task
        # Use Referenced Single Ended to measure relative to GND
        # The voltage output of the Gen5 amp is +/- 5V, but I don't think these parameters
        # actually change anything about the measurement.
        self.task.ai_channels.add_ai_voltage_chan(
            physical_channel=f"{self.dev_name}/{channels_str}",
            min_val=-5,
            max_val=5,
            terminal_config=TerminalConfiguration.RSE
        )

        # Define sample timing parameters
        self.task.timing.cfg_samp_clk_timing(
            rate=50, 
            sample_mode=AcquisitionType.CONTINUOUS
        )

    def start(self):
        """Start the task, if there is one already defined."""
        if self.is_task:
            if self.is_running:
                raise KeyError("The task has already been started.")
            else:
                self.task.start()
                self.is_running = True
        else:
            raise KeyError("No task has been defined. Use create_task to initiate one.")

    def stop(self):
        """Stop the active task, if there is one already defined."""
        if self.is_task:
            if self.is_running:
                self.task.stop()
                self.is_running = False
            else:
                raise KeyError("Task is already stopped.")
        else:
            raise KeyError("No task has been defined. Use create_task to initiate a task.")

    def close(self):
        """Clear the active task, which is unrecoverable. Task will have to be recreated."""
        if self.is_task:
            if self.is_running:
                self.task.stop()
            self.task.close()
            self.is_task = False
            self.is_running = False
            del self.task
        

    def read(self):
        """Read the data present in the buffer of the DAQ."""
        if not self.is_task:
            raise KeyError("No active task. Use create_task() to create one.")
        if not self.is_running:
            raise KeyError("Task has not been started, use start() to begin the task.")
            
        buffer = self.task.read()
        return buffer
