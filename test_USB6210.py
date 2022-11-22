# Author: William Liu <liwi@ohsu.edu>

import unittest
from USB6210 import DAQ


class TestTask(unittest.TestCase):
    def setUp(self) -> None:
        self.dev_name = 'Dev1'
        self.device = DAQ(self.dev_name)
        self.channels = "ai1:6"

    def test_create_task_success(self):
        # Test creating a task
        self.device.create_tasks(self.channels)
        self.assertTrue(self.device.task.is_task_done())
        self.assertTrue(self.device.are_tasks)
        self.assertEqual(self.device.task.channel_names, [f"{self.dev_name}/ai{i}" for i in range(1, 7)])
        self.device.close()

    def test_create_task_fail(self):
        # Test creating a task when one already exists
        self.device.create_tasks(self.channels)
        with self.assertRaises(ValueError):
            self.device.create_tasks(self.channels)
        self.device.close()

    def test_task_start(self):
        # Test starting a task without creating one first
        with self.assertRaises(KeyError):
            self.device.start()

        # Test creating a task and starting it
        self.device.create_tasks(self.channels)
        self.device.start()
        self.assertFalse(self.device.task.is_task_done())
        self.assertTrue(self.device.are_tasks)
        self.assertTrue(self.device.is_running)

        # Test starting the task when it is already running
        with self.assertRaises(KeyError):
            self.device.start()

        # Test starting a task after stopping it
        self.device.stop()
        self.assertTrue(self.device.task.is_task_done())
        self.assertFalse(self.device.is_running)

        # Test starting a task after closing it
        self.device.start()
        self.assertFalse(self.device.task.is_task_done())
        self.device.close()
        with self.assertRaises(KeyError):
            self.device.start()

        # CLose device just to be safe, so it doesn't interfere with other tests
        self.device.close()

    def test_task_stop(self):
        # Test stopping a task without one being created
        with self.assertRaises(KeyError):
            self.device.stop()

        # Test stopping task after one has been created, but not started
        self.device.create_tasks(self.channels)
        with self.assertRaises(KeyError):
            self.device.stop()

        # Test stopping a task successfully
        self.device.start()
        self.assertTrue(self.device.are_tasks)
        self.assertTrue(self.device.is_running)
        self.assertFalse(self.device.task.is_task_done())
        self.device.stop()
        self.assertFalse(self.device.is_running)
        self.assertTrue(self.device.are_tasks)
        self.assertTrue(self.device.task.is_task_done())

        self.device.close()

    def test_read(self):
        # Test the read functionality
        self.device.create_tasks(self.channels)
        self.device.start()
        buffer = self.device.read()
        self.assertEqual(len(buffer), 6)
        self.device.close()

        # Test reading when a task hasnt been created
        with self.assertRaises(KeyError):
            self.device.read()

        # Test reading when a task has been created, but not started
        self.device.create_tasks(self.channels)
        with self.assertRaises(KeyError):
            self.device.read()
        self.device.close()


if __name__ == '__main__':
    unittest.main()
