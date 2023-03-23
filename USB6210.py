# Author: William Liu <liwi@ohsu.edu>

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import numpy as np
import json


class DAQ:
    """This object represents a National Instruments DAQ Device."""

    def __init__(self, dev_name: str, rate: int = 1000) -> None:
        """
        Initiate the device, perform basic self test.

        :param dev_name: A str representing the name of the DAQ device,
                         can be found in the NI Device Monitor software.
        :param rate: The sample rate for data acquisition, default is 100Hz
        """
        self.dev_name = dev_name
        self.dev = nidaqmx.system.Device(self.dev_name)

        # Read the analog sensitivities
        self._analog_sensitivities = self._read_settings()

        # Reset the device
        self.dev.reset_device()

        # Perform the self test
        self.dev.self_test_device()

        # Initiate variables to store state
        self.is_running = False
        self.are_tasks = False

        # Set the sample rate
        self.rate = rate

    def _read_settings(self):
        """Read the settings file to get the analog sensitivities."""
        with open("amti_settings.json", 'r') as file:
            settings = json.load(file)

        analog_sensitivities = np.array(settings['analog_sensitivities'], dtype=np.float64)
        analog_sensitivities = analog_sensitivities * 1e-3  # Convert units from mV/N to V/N
        # Add [1, 1] to the end of the analog sensitivities array as EMG values are not scaled
        analog_sensitivities = np.append(analog_sensitivities, [1, 1])

        return analog_sensitivities

    def create_tasks(self, fp_channels: list, emg_channels: list):
        # I belive assigning a name to the task will cause an error when trying
        # to create multiple tasks, so I'm assigning it a name to prevent unintended
        # creation of tasks.
        if self.are_tasks:
            raise ValueError("Task is already running.")

        self.task = nidaqmx.Task(new_task_name="Reader")
        self.counter = nidaqmx.Task(new_task_name="Counter")
        self.are_tasks = True

        # Add the channels to the task
        # Use Referenced Single Ended to measure relative to GND
        # The voltage output of the Gen5 amp is +/- 5V, but I don't think these parameters
        # actually change anything about the measurement.
        for channel in fp_channels:
            self.task.ai_channels.add_ai_voltage_chan(
                physical_channel=f"{self.dev_name}/ai{str(channel)}",
                min_val=-5,
                max_val=5,
                terminal_config=TerminalConfiguration.RSE
            )

        # Add the EMG channels
        for channel in emg_channels:
            self.task.ai_channels.add_ai_voltage_chan(
                physical_channel=f"{self.dev_name}/ai{str(channel)}",
                min_val=-2.5,
                max_val=2.5,
                terminal_config=TerminalConfiguration.RSE
            )

        # Define sample timing parameters
        self.task.timing.cfg_samp_clk_timing(
            rate=self.rate,
            sample_mode=AcquisitionType.CONTINUOUS
        )

        # Set up the counter task for generating TTL pulse
        self.counter.co_channels.add_co_pulse_chan_time(
            counter=f"{self.dev_name}/ctr0",
            low_time=0.00005,
            high_time=0.00005
        )
        self.counter.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE, samps_per_chan=1)

    def start(self):
        """Start the task, if there is one already defined."""
        if self.are_tasks:
            if self.is_running:
                raise KeyError("The task has already been started.")
            else:
                self.task.start()
                self.is_running = True
        else:
            raise KeyError("No task has been defined. Use create_task to initiate one.")

    def stop(self):
        """Stop the active task, if there is one already defined."""
        if self.are_tasks:
            if self.is_running:
                self.task.stop()
                self.counter.stop()
                self.is_running = False
            else:
                raise KeyError("Task is already stopped.")
        else:
            raise KeyError("No task has been defined. Use create_task to initiate a task.")

    def close(self):
        """Clear the active task, which is unrecoverable. Task will have to be recreated."""
        if self.are_tasks:
            if self.is_running:
                self.task.stop()
                self.counter.stop()
            self.task.close()
            self.counter.close()
            self.are_tasks = False
            self.is_running = False
            del self.task

    def read(self):
        """Read the data present in the buffer of the DAQ and convert the voltage value to Newtons."""
        if not self.are_tasks:
            raise KeyError("No active task. Use create_task() to create one.")
        if not self.is_running:
            raise KeyError("Task has not been started, use start() to begin the task.")

        return np.array(self.task.read()) / self._analog_sensitivities

    def ttl(self):
        """Generate the TTL pulse at the counter terminal."""
        self.counter.start()
        self.counter.wait_until_done()
        self.counter.stop()

    def get_sample_rate(self):
        """Getter for the sample rate."""
        return self.rate
