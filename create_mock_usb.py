import os
import shutil

MOCK_BASE = "mock_usb/sys/bus/usb/devices"

def create_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def setup_mock_usb():
    if os.path.exists(MOCK_BASE):
        shutil.rmtree(MOCK_BASE)
    os.makedirs(MOCK_BASE)

    # Device 1: USB 2.0 Root Hub (usb1)
    d1 = os.path.join(MOCK_BASE, "usb1")
    os.makedirs(d1)
    create_file(os.path.join(d1, "speed"), "480\n")
    create_file(os.path.join(d1, "version"), " 2.00\n")
    create_file(os.path.join(d1, "product"), "EHCI Host Controller\n")
    create_file(os.path.join(d1, "manufacturer"), "Linux 5.4.0-54-generic ehci_hcd\n")
    create_file(os.path.join(d1, "busnum"), "1\n")
    create_file(os.path.join(d1, "devnum"), "1\n")
    create_file(os.path.join(d1, "bcdUSB"), "0200\n")
    create_file(os.path.join(d1, "bDeviceClass"), "09\n") # Hub
    create_file(os.path.join(d1, "bMaxPower"), "0mA\n")

    # Device 2: USB 3.0 Root Hub (usb2)
    d2 = os.path.join(MOCK_BASE, "usb2")
    os.makedirs(d2)
    create_file(os.path.join(d2, "speed"), "5000\n")
    create_file(os.path.join(d2, "version"), " 3.00\n")
    create_file(os.path.join(d2, "product"), "xHCI Host Controller\n")
    create_file(os.path.join(d2, "manufacturer"), "Linux 5.4.0-54-generic xhci_hcd\n")
    create_file(os.path.join(d2, "busnum"), "2\n")
    create_file(os.path.join(d2, "devnum"), "1\n")
    create_file(os.path.join(d2, "bcdUSB"), "0300\n")
    create_file(os.path.join(d2, "bDeviceClass"), "09\n") # Hub
    create_file(os.path.join(d2, "bMaxPower"), "0mA\n")

    # Connected Device A: Mouse on USB 2.0 Hub (1-1)
    da = os.path.join(MOCK_BASE, "1-1")
    os.makedirs(da)
    create_file(os.path.join(da, "speed"), "1.5\n")
    create_file(os.path.join(da, "version"), " 1.10\n")
    create_file(os.path.join(da, "product"), "USB Optical Mouse\n")
    create_file(os.path.join(da, "manufacturer"), "Logitech\n")
    create_file(os.path.join(da, "busnum"), "1\n")
    create_file(os.path.join(da, "devnum"), "2\n")
    create_file(os.path.join(da, "bcdUSB"), "0200\n") # Supports 2.0 but running at 1.5 is fine for mouse
    create_file(os.path.join(da, "bDeviceClass"), "00\n")
    create_file(os.path.join(da, "bMaxPower"), "100mA\n")


    # Connected Device B: Fast Flash Drive on USB 2.0 Hub (1-2) -> BOTTLENECK
    db = os.path.join(MOCK_BASE, "1-2")
    os.makedirs(db)
    create_file(os.path.join(db, "speed"), "480\n")
    create_file(os.path.join(db, "version"), " 2.10\n")
    create_file(os.path.join(db, "product"), "Ultra Fast Flash Drive\n")
    create_file(os.path.join(db, "manufacturer"), "SanDisk\n")
    create_file(os.path.join(db, "busnum"), "1\n")
    create_file(os.path.join(db, "devnum"), "3\n")
    create_file(os.path.join(db, "bcdUSB"), "0310\n") # Supports USB 3.1!
    create_file(os.path.join(db, "bDeviceClass"), "00\n")
    create_file(os.path.join(db, "bMaxPower"), "400mA\n")

    # Connected Device C: Fast Flash Drive on USB 3.0 Hub (2-1) -> OPTIMAL
    dc = os.path.join(MOCK_BASE, "2-1")
    os.makedirs(dc)
    create_file(os.path.join(dc, "speed"), "5000\n")
    create_file(os.path.join(dc, "version"), " 3.00\n")
    create_file(os.path.join(dc, "product"), "External SSD\n")
    create_file(os.path.join(dc, "manufacturer"), "Samsung\n")
    create_file(os.path.join(dc, "busnum"), "2\n")
    create_file(os.path.join(dc, "devnum"), "2\n")
    create_file(os.path.join(dc, "bcdUSB"), "0300\n") # Supports USB 3.0
    create_file(os.path.join(dc, "bDeviceClass"), "00\n")
    create_file(os.path.join(dc, "bMaxPower"), "896mA\n")

    print(f"Mock USB environment created at {MOCK_BASE}")

if __name__ == "__main__":
    setup_mock_usb()
