import os
import sys
import argparse
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

"""
USB Inspector
-------------
A Python-based GUI tool to analyze connected USB devices, their speeds, power usage,
and versions. It provides suggestions for optimizing device connections (e.g., detecting
if a USB 3.0 device is plugged into a slower port).

Platform Support:
    - Linux: Fully supported (relies on /sys/bus/usb/devices).
    - Other OS: Supported via mock mode (requires generating mock data).

Dependencies:
    - Python 3
    - tkinter (python3-tk)
"""

# Default path for Linux USB devices
REAL_USB_PATH = "/sys/bus/usb/devices"
# Fallback to mock path if real path doesn't exist (for development/demo)
MOCK_USB_PATH = "mock_usb/sys/bus/usb/devices"

# Design Constants
COLOR_BG = "#FFFFFF"
COLOR_FG = "#333333"
COLOR_HEADER_BG = "#F5F5F7" # Light grey header
COLOR_ACCENT = "#007AFF"   # Apple Blue
COLOR_WARNING = "#FF9500"  # Apple Orange
COLOR_DANGER = "#FF3B30"   # Apple Red
COLOR_SUCCESS = "#34C759"  # Apple Green
COLOR_SUBTLE = "#8E8E93"   # Grey for secondary text

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
        Returns a tuple (status_code, message).
        status_code: 0=OK, 1=Warning
        """
        speed_val = self.get_speed_mbps()

        try:
            bcd_val = int(self.bcdUSB, 16)
        except ValueError:
            return (0, "OK")

        # Check for USB 3.0+ device (bcdUSB >= 0x0300) on USB 2.0 speed (480) or lower
        if bcd_val >= 0x0300:
            if speed_val <= 480:
                return (1, "Running slow. Move to blue USB 3.0 port.")

        # Check for USB 2.0 device (bcdUSB >= 0x0200) on USB 1.1 speed (12 or 1.5)
        if bcd_val >= 0x0200:
            if speed_val <= 12:
                prod_lower = self.product.lower()
                if "hub" in prod_lower or "mouse" in prod_lower or "keyboard" in prod_lower:
                     return (0, "OK")
                return (1, "Running slow. Try another port.")

        return (0, "Optimal")

def get_usb_devices(usb_path):
    devices = []
    if not os.path.exists(usb_path):
        return devices

    for entry in os.listdir(usb_path):
        full_path = os.path.join(usb_path, entry)
        if os.path.isdir(full_path):
            if os.path.exists(os.path.join(full_path, "speed")):
                devices.append(USBDevice(full_path, entry))

    devices.sort(key=lambda x: (x.bus_num_int(), x.dev_num_int()))
    return devices

class USBMonitorApp:
    def __init__(self, root, usb_path):
        self.root = root
        self.usb_path = usb_path
        self.root.title("USB Inspector")
        self.root.geometry("1100x600")
        self.root.configure(bg=COLOR_BG)

        self._configure_styles()
        self._build_ui()
        self.refresh_data()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # General App Styling
        style.configure(".",
            background=COLOR_BG,
            foreground=COLOR_FG,
            font=("Helvetica", 10)
        )

        # Treeview (The List)
        style.configure("Treeview",
            background=COLOR_BG,
            foreground=COLOR_FG,
            rowheight=40,
            fieldbackground=COLOR_BG,
            borderwidth=0,
            font=("Helvetica", 11)
        )
        style.configure("Treeview.Heading",
            background=COLOR_HEADER_BG,
            foreground=COLOR_SUBTLE,
            font=("Helvetica", 9, "bold"),
            borderwidth=0,
            relief="flat"
        )
        style.map("Treeview",
            background=[('selected', COLOR_ACCENT)],
            foreground=[('selected', 'white')]
        )

        # Remove borders/focus lines
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def _build_ui(self):
        # -- Header Section --
        header_frame = tk.Frame(self.root, bg=COLOR_BG)
        header_frame.pack(fill=tk.X, padx=30, pady=(30, 20))

        title_lbl = tk.Label(header_frame,
            text="USB Inspector",
            font=("Helvetica", 24, "bold"),
            bg=COLOR_BG, fg=COLOR_FG
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(header_frame,
            text="Real-time analysis of connected peripherals and performance.",
            font=("Helvetica", 13),
            bg=COLOR_BG, fg=COLOR_SUBTLE
        )
        subtitle_lbl.pack(anchor="w", pady=(5, 0))

        # -- Main Content Section --
        container = tk.Frame(self.root, bg=COLOR_BG)
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

        # Table Frame with shadow/border effect (simulated with a container)
        table_frame = tk.Frame(container, bg="white", bd=1, relief="solid") # subtle border
        # Actually standard tkinter border is ugly. Let's rely on clean flat look.

        # Treeview
        columns = ("Icon", "Port", "Device", "Speed", "Power", "Ver", "Suggestion")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("Icon", text="")
        self.tree.heading("Port", text="PORT")
        self.tree.heading("Device", text="DEVICE")
        self.tree.heading("Speed", text="SPEED")
        self.tree.heading("Power", text="POWER")
        self.tree.heading("Ver", text="VERSION")
        self.tree.heading("Suggestion", text="STATUS")

        self.tree.column("Icon", width=40, anchor="center")
        self.tree.column("Port", width=60, anchor="w")
        self.tree.column("Device", width=300, anchor="w")
        self.tree.column("Speed", width=100, anchor="w")
        self.tree.column("Power", width=100, anchor="w")
        self.tree.column("Ver", width=80, anchor="center")
        self.tree.column("Suggestion", width=300, anchor="w")

        # Scrollbar (Modern style? Tkinter scrollbars are hard to style perfectly, will stick to default but integrated well)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # -- Footer Section --
        footer_frame = tk.Frame(self.root, bg=COLOR_BG)
        footer_frame.pack(fill=tk.X, padx=30, pady=20)

        self.status_lbl = tk.Label(footer_frame, text="Scanning...", bg=COLOR_BG, fg=COLOR_SUBTLE, font=("Helvetica", 10))
        self.status_lbl.pack(side=tk.LEFT)

        # "Action" Button
        refresh_btn = tk.Button(footer_frame,
            text="Refresh Analysis",
            command=self.refresh_data,
            bg=COLOR_ACCENT, fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            padx=20, pady=8,
            activebackground="#0062CC", activeforeground="white",
            borderwidth=0
        )
        refresh_btn.pack(side=tk.RIGHT)

    def refresh_data(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        devices = get_usb_devices(self.usb_path)

        if not devices and not os.path.exists(self.usb_path):
             self.tree.insert("", "end", values=("⚠️", "", f"Path not found: {self.usb_path}", "-", "-", "-", "Check System"))
             self.status_lbl.config(text="Error: System path unavailable")
             return

        count = 0
        issues = 0

        for dev in devices:
            count += 1
            status_code, suggestion_text = dev.analyze()
            ver_str = dev.get_max_speed_version_str()
            full_name = f"{dev.manufacturer} {dev.product}".strip()

            # Formatting Speed
            speed_val = dev.get_speed_mbps()
            if speed_val >= 5000:
                speed_display = f"{speed_val/1000:.0f} Gbps"
            else:
                speed_display = f"{speed_val:.0f} Mbps"

            # Formatting Power
            power_display = dev.bMaxPower

            # Icons and Status
            if status_code == 1:
                icon = "⚠️"
                issues += 1
                # We can tag this row to color the text if we want, but clean design prefers subtle indicators
                # The icon is strong. The suggestion text explains it.
            else:
                icon = "⚡" # or a plug icon, or generic dot
                # Check for Hub
                if "hub" in full_name.lower():
                    icon = "⚇" # Hub symbol approximately

            values = (
                icon,
                dev.port_name,
                full_name,
                speed_display,
                power_display,
                f"USB {ver_str}",
                suggestion_text
            )

            item = self.tree.insert("", "end", values=values)
            if status_code == 1:
                self.tree.item(item, tags=("warning",))

        # Tag configuration for subtle highlighting
        self.tree.tag_configure("warning", foreground=COLOR_WARNING)
        # Note: foreground changes text color.

        self.status_lbl.config(text=f"{count} devices connected. {issues} optimization(s) found.")


def run_cli(usb_path):
    devices = get_usb_devices(usb_path)
    print(f"{'Port':<8} | {'Device':<40} | {'Speed':<10} | {'Power':<8} | {'Cur Ver':<7} | {'Suggestion'}")
    print("-" * 130)
    for dev in devices:
        status_code, suggestion = dev.analyze()
        ver_str = dev.get_max_speed_version_str()
        full_name = f"{dev.manufacturer} {dev.product}".strip()

        prefix = "  "
        if status_code == 1:
            prefix = "! "

        print(f"{prefix}{dev.port_name:<6} | {full_name[:40]:<40} | {dev.speed:<10} | {dev.bMaxPower:<8} | {dev.version:<7} | {suggestion}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="USB Inspector")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    args = parser.parse_args()

    # Determine which path to use
    path_to_use = REAL_USB_PATH
    if not os.path.exists(REAL_USB_PATH) and os.path.exists(MOCK_USB_PATH):
        if args.cli:
            print(f"Real USB path not found. Using mock path: {MOCK_USB_PATH}")
        path_to_use = MOCK_USB_PATH
    elif not os.path.exists(REAL_USB_PATH):
         # Just to allow GUI to open and show error
         pass

    if args.cli:
        run_cli(path_to_use)
    else:
        root = tk.Tk()
        # Set icon if possible, but skip for now
        app = USBMonitorApp(root, path_to_use)
        root.mainloop()
