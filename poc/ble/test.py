import pyshark

captures = pyshark.LiveCapture(interface='/dev/serial/by-id/usb-ZEPHYR_nRF_Sniffer_for_Bluetooth_LE_1C751377F575C06F-if00')
captures.sniff(timeout=30)
print(captures[0])