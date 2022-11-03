# Author: William Liu <liwi@ohsu.edu>

import unittest
from USB6210 import DAQ

class TestTask(unittest.TestCase):
    def setUp(self) -> None:
        self.dev_name = 'Dev1'
        self.device = DAQ(self.dev_name)
        self.channels = channels = "ai0:7"

    def test_create_task_success(self):
        self.device.create_task(self.channels)
        self.assertEqual(self.device.is_task, True)
        self.assertEqual(self.device.task.channel_names, [f"{self.dev_name}/ai{i}" for i in range(8)])
        self.device.close()

    def test_task_start(self):
        # Test starting a task without creating one first
        with self.assertRaises(KeyError):
            self.device.start()

        # Test creating a task and starting it
        self.device.create_task(self.channels)
        self.device.start()
        self.assertEqual(self.device.task.is_task_done(), False)
        self.assertEqual(self.device.is_task, True)
        self.assertEqual(self.device.is_running, True)

        # Test starting the task when it is already running
        with self.assertRaises(KeyError):
            self.device.start()
        
        # Test starting a task after stopping it
        self.device.stop()
        self.assertEqual(self.device.task.is_task_done(), True)
        self.assertEqual(self.device.is_running, False)

        # Test starting a task after closing it
        self.device.start()
        self.assertEqual(self.device.task.is_task_done(), False)
        self.device.close()
        with self.assertRaises(KeyError):
            self.device.start()


if __name__ == '__main__':
    unittest.main()
