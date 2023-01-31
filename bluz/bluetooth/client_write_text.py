#!/usr/bin/python3
#
# Connects to a specified device and writes a short string to the LED Text characteristic of a BBC microbit.
# Run from the command line with a bluetooth device address argument

import bluetooth_constants
import bluetooth_utils
import dbus
import dbus.mainloop.glib
import sys
import time
from gi.repository import GLib
sys.path.insert(0, '.')

bus = None
device_interface = None
device_path = None
found_ls = False
found_lc  = False
ls_path = None
lc_path  = None
text = None

def write_text(text):
    global lc_path
    char_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,lc_path)
    char_interface = dbus.Interface(char_proxy, bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE)
    try:
        ascii = bluetooth_utils.text_to_ascii_array(text)
        value = char_interface.WriteValue(ascii, {})
    except Exception as e:
        print("Failed to write to LED Text")
        print(e.get_dbus_name())
        print(e.get_dbus_message())
        return bluetooth_constants.RESULT_EXCEPTION
    else:
        print("LED Text written OK")
        return bluetooth_constants.RESULT_OK
    
def service_discovery_completed():
    global found_ls
    global found_lc
    global ls_path
    global lc_path
    global bus
    global text
    
    if found_ls and found_lc:
        print("Required service and characteristic found - device is OK")
        print("LED service path: ",ls_path)
        print("LED characteristic path: ",lc_path)
        write_text(text)
    else:
        print("Required service and characteristic were not found - device is NOK")
        print("LED service found: ",str(found_ls))
        print("LED Text characteristic found: ",str(found_lc))
    bus.remove_signal_receiver(interfaces_added,"InterfacesAdded")
    bus.remove_signal_receiver(properties_changed,"PropertiesChanged")
    mainloop.quit()
    
def properties_changed(interface, changed, invalidated, path):
    global device_path
    if path != device_path:
        return

    if 'ServicesResolved' in changed:
        sr = bluetooth_utils.dbus_to_python(changed['ServicesResolved'])
        print("ServicesResolved  : ", sr)
        if sr == True:
            service_discovery_completed()
        

def interfaces_added(path, interfaces):
    global found_ls
    global found_lc
    global ls_path
    global lc_path
    if bluetooth_constants.GATT_SERVICE_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.GATT_SERVICE_INTERFACE]
        print("--------------------------------------------------------------------------------")
        print("SVC path   :", path)
        if 'UUID' in properties:
            uuid = properties['UUID']
            if uuid == bluetooth_constants.LED_SVC_UUID:
                found_ls = True
                ls_path = path
            print("SVC UUID   : ", bluetooth_utils.dbus_to_python(uuid))
            print("SVC name   : ", bluetooth_utils.get_name_from_uuid(uuid))
        return

    if bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE]
        print("  CHR path   :", path)
        if 'UUID' in properties:
            uuid = properties['UUID']
            if uuid == bluetooth_constants.LED_TEXT_CHR_UUID:
                found_lc = True
                lc_path = path
            print("  CHR UUID   : ", bluetooth_utils.dbus_to_python(uuid))
            print("  CHR name   : ", bluetooth_utils.get_name_from_uuid(uuid))
            flags  = ""
            for flag in properties['Flags']:
                flags = flags + flag + ","
            print("  CHR flags  : ", flags)
        return
    
    if bluetooth_constants.GATT_DESCRIPTOR_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.GATT_DESCRIPTOR_INTERFACE]
        print("    DSC path   :", path)
        if 'UUID' in properties:
            uuid = properties['UUID']
            print("    DSC UUID   : ", bluetooth_utils.dbus_to_python(uuid))
            print("    DSC name   : ", bluetooth_utils.get_name_from_uuid(uuid))
        return

def connect():
    global bus
    global device_interface
    try:
        device_interface.Connect()
    except Exception as e:
        print("Failed to connect")
        print(e.get_dbus_name())
        print(e.get_dbus_message())
        if ("UnknownObject" in e.get_dbus_name()):
            print("Try scanning first to resolve this problem")
        return bluetooth_constants.RESULT_EXCEPTION
    else:
        print("Connected OK")
        return bluetooth_constants.RESULT_OK

if (len(sys.argv) != 3):
    print("usage: client_python3 write_text.py [bdaddr] [text]")
    sys.exit(1)

bdaddr = sys.argv[1]
text = sys.argv[2]
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME
device_path = bluetooth_utils.device_address_to_path(bdaddr, adapter_path)
device_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,device_path)
device_interface = dbus.Interface(device_proxy, bluetooth_constants.DEVICE_INTERFACE)

print("Connecting to " + bdaddr)
connect()
print("Discovering services++")
print("Registering to receive InterfacesAdded signals")
bus.add_signal_receiver(interfaces_added,
        dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
        signal_name = "InterfacesAdded")
print("Registering to receive PropertiesChanged signals")
bus.add_signal_receiver(properties_changed,
        dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
        signal_name = "PropertiesChanged",
        path_keyword = "path")
mainloop = GLib.MainLoop()
mainloop.run()
print("Finished")
