import unittest
import os
import shutil
import tempfile
from usb_analyzer import USBDevice, get_usb_devices

class TestUSBAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.device_path = os.path.join(self.test_dir, "test_device")
        os.makedirs(self.device_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content):
        with open(os.path.join(self.device_path, filename), "w") as f:
            f.write(content)

    def test_device_info_parsing(self):
        self.create_file("product", "Test Product\n")
        self.create_file("manufacturer", "Test Manufacturer\n")
        self.create_file("speed", "480\n")
        self.create_file("version", "2.00\n")
        self.create_file("bcdUSB", "0200\n")
        self.create_file("bMaxPower", "100mA\n")

        dev = USBDevice(self.device_path, "test_port")
        self.assertEqual(dev.product, "Test Product")
        self.assertEqual(dev.manufacturer, "Test Manufacturer")
        self.assertEqual(dev.speed, "480")
        self.assertEqual(dev.version, "2.00")
        self.assertEqual(dev.bcdUSB, "0200")
        self.assertEqual(dev.bMaxPower, "100mA")
        self.assertEqual(dev.get_max_speed_version_str(), "2.0")

    def test_analysis_ok(self):
        self.create_file("speed", "5000\n")
        self.create_file("bcdUSB", "0300\n") # 3.0
        dev = USBDevice(self.device_path, "test_port")
        # Expect tuple (0, "Optimal")
        status, msg = dev.analyze()
        self.assertEqual(status, 0)
        self.assertEqual(msg, "Optimal")

    def test_analysis_bottleneck(self):
        self.create_file("speed", "480\n")
        self.create_file("bcdUSB", "0300\n") # Supports 3.0, running at 2.0 speed
        dev = USBDevice(self.device_path, "test_port")
        status, msg = dev.analyze()
        self.assertEqual(status, 1)
        self.assertIn("Move to blue USB 3.0 port", msg)

    def test_analysis_mouse_exception(self):
        self.create_file("product", "USB Optical Mouse\n")
        self.create_file("speed", "1.5\n")
        self.create_file("bcdUSB", "0200\n") # Supports 2.0
        dev = USBDevice(self.device_path, "test_port")
        status, msg = dev.analyze()
        self.assertEqual(status, 0)
        self.assertEqual(msg, "OK")

if __name__ == '__main__':
    unittest.main()
