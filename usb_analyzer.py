import os
import sys
import argparse
import tkinter as tk
from tkinter import ttk

# Default path for Linux USB devices
REAL_USB_PATH = "/sys/bus/usb/devices"
# Fallback to mock path if real path doesn't exist (for development/demo)
MOCK_USB_PATH = "mock_usb/sys/bus/usb/devices"

class USBDevice:
    def __init__(self, path, name):
        self.path = path
        self.port_name = name
        self.product = self._read_file("product", "Unknown Product")
        self.manufacturer = self._read_file("manufacturer", "Unknown Manufacturer")
        self.speed = self._read_file("speed", "0")
        self.version = self._read_file("version", "0.0")
        self.bcdUSB = self._read_file("bcdUSB", "0000")
        self.busnum = self._read_file("busnum", "?")
        self.devnum = self._read_file("devnum", "?")
        self.bMaxPower = self._read_file("bMaxPower", "0mA")

    def _read_file(self, filename, default):
        try:
            with open(os.path.join(self.path, filename), "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return default

    def get_max_speed_version_str(self):
        # bcdUSB is often in hex format like 0200, 0300, 0310
        try:
            val = int(self.bcdUSB, 16)
            major = (val >> 8) & 0xFF
            minor = (val >> 4) & 0xF
            sub = val & 0xF
            if sub == 0:
                return f"{major}.{minor}"
            else:
                return f"{major}.{minor}{sub}"
        except ValueError:
            return "Unknown"

    def get_speed_mbps(self):
        try:
            return float(self.speed)
        except ValueError:
            return 0.0

    def bus_num_int(self):
        try: return int(self.busnum)
        except: return 999

    def dev_num_int(self):
        try: return int(self.devnum)
        except: return 999

    def analyze(self):
        """
        Returns a suggestion string or "OK" if everything seems fine.
        """
        speed_val = self.get_speed_mbps()

        # High Speed (USB 2.0) is 480 Mbps
        # SuperSpeed (USB 3.0) is 5000 Mbps

        # Parse bcdUSB to see what the device claims to support
        try:
            bcd_val = int(self.bcdUSB, 16)
        except ValueError:
            return "OK"

        # Check for USB 3.0+ device (bcdUSB >= 0x0300) on USB 2.0 speed (480) or lower
        if bcd_val >= 0x0300:
            if speed_val <= 480:
                return "Device supports USB 3.0+ but is running at slower speeds. Try a blue USB 3.0 port."

        # Check for USB 2.0 device (bcdUSB >= 0x0200) on USB 1.1 speed (12 or 1.5)
        if bcd_val >= 0x0200:
            if speed_val <= 12:
                # Exclude Hubs, Mice, Keyboards from this warning as they often run slow intentionally
                prod_lower = self.product.lower()
                if "hub" in prod_lower or "mouse" in prod_lower or "keyboard" in prod_lower:
                     return "OK"
                return "Device supports USB 2.0 but is running at low speed. Try another port."

        return "OK"

def get_usb_devices(usb_path):
    devices = []
    if not os.path.exists(usb_path):
        return devices

    # Filter for directories that look like USB devices (numbers, dashes, usb*)
    for entry in os.listdir(usb_path):
        full_path = os.path.join(usb_path, entry)
        if os.path.isdir(full_path):
            # Verify it has essential USB files
            if os.path.exists(os.path.join(full_path, "speed")):
                devices.append(USBDevice(full_path, entry))

    # Sort by bus and devnum
    devices.sort(key=lambda x: (x.bus_num_int(), x.dev_num_int()))
    return devices

class USBMonitorApp:
    def __init__(self, root, usb_path):
        self.root = root
        self.usb_path = usb_path
        self.root.title("USB Port Analyzer")
        self.root.geometry("1100x400")

        self.tree = ttk.Treeview(root, columns=("Port", "Device", "Speed (Mbps)", "Power", "USB Ver", "Supported", "Suggestion"), show="headings")
        self.tree.heading("Port", text="Port ID")
        self.tree.heading("Device", text="Device")
        self.tree.heading("Speed (Mbps)", text="Speed (Mbps)")
        self.tree.heading("Power", text="Power")
        self.tree.heading("USB Ver", text="Current Ver")
        self.tree.heading("Supported", text="Supported Ver")
        self.tree.heading("Suggestion", text="Suggestion")

        self.tree.column("Port", width=80)
        self.tree.column("Device", width=250)
        self.tree.column("Speed (Mbps)", width=100)
        self.tree.column("Power", width=80)
        self.tree.column("USB Ver", width=80)
        self.tree.column("Supported", width=100)
        self.tree.column("Suggestion", width=400)

        self.tree.pack(fill=tk.BOTH, expand=True)

        refresh_btn = tk.Button(root, text="Refresh", command=self.refresh_data)
        refresh_btn.pack(pady=5)

        self.refresh_data()

    def refresh_data(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        devices = get_usb_devices(self.usb_path)

        if not devices and not os.path.exists(self.usb_path):
             self.tree.insert("", "end", values=("Error", f"Path not found: {self.usb_path}", "", "", "", "", ""))
             return

        for dev in devices:
            suggestion = dev.analyze()
            ver_str = dev.get_max_speed_version_str()
            full_name = f"{dev.manufacturer} {dev.product}".strip()

            values = (
                dev.port_name,
                full_name,
                dev.speed,
                dev.bMaxPower,
                dev.version,
                ver_str,
                suggestion
            )
            item_id = self.tree.insert("", "end", values=values)
            if suggestion != "OK":
                self.tree.item(item_id, tags=("warning",))

        self.tree.tag_configure("warning", foreground="red")

def run_cli(usb_path):
    devices = get_usb_devices(usb_path)
    print(f"{'Port':<8} | {'Device':<40} | {'Speed':<8} | {'Power':<8} | {'Cur Ver':<7} | {'Sup Ver':<7} | {'Suggestion'}")
    print("-" * 130)
    for dev in devices:
        suggestion = dev.analyze()
        ver_str = dev.get_max_speed_version_str()
        full_name = f"{dev.manufacturer} {dev.product}".strip()
        print(f"{dev.port_name:<8} | {full_name[:40]:<40} | {dev.speed:<8} | {dev.bMaxPower:<8} | {dev.version:<7} | {ver_str:<7} | {suggestion}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="USB Port Analyzer")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    args = parser.parse_args()

    # Determine which path to use
    path_to_use = REAL_USB_PATH
    if not os.path.exists(REAL_USB_PATH) and os.path.exists(MOCK_USB_PATH):
        if args.cli:
            print(f"Real USB path not found. Using mock path: {MOCK_USB_PATH}")
        path_to_use = MOCK_USB_PATH
    elif not os.path.exists(REAL_USB_PATH):
         print("Warning: Neither real nor mock USB path found.")

    if args.cli:
        run_cli(path_to_use)
    else:
        root = tk.Tk()
        app = USBMonitorApp(root, path_to_use)
        root.mainloop()
