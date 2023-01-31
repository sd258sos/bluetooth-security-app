#!/usr/bin/python3
#
# Scans for devices and reports details as they are
# Run from the command line with an integer argument which indicates the duration in ms for which scanning
# should be performed.
#
# Illustrates how a path is the unique identifier of a device and that all device properties are not 
# necessarily available in all signals from BlueZ (hence reliance on the path identifier)

# Illustrates how InterfacesAdded reports newly encountered devices and PropertiesChanged reports changes
# to devices that BlueZ already knows about (usually from a previous scan)
#
# Illustrates how InterfacesRemoved reports that BlueZ regards a device as having "gone away" 
# e.g. out of range
#
# Illustrates how the list of devices already known to BlueZ and which will therefore not be reported in InterfacesAdded signals may be obtained

from gi.repository import GLib

import bluetooth_utils
import bluetooth_constants
import dbus
import dbus.mainloop.glib
import sys
sys.path.insert(0, '.')

adapter_interface = None
mainloop = None
timer_id = None

devices = {}
managed_objects_found = 0

def list_devices_found():
    print("Full list of devices",len(devices),"discovered:")
    print("------------------------------")
    for path in devices:
        dev = devices[path]
        print(bluetooth_utils.dbus_to_python(dev['Address']))
   
def interfaces_added(path, interfaces):
    # interfaces is an array of dictionary entries
    if not bluetooth_constants.DEVICE_INTERFACE in interfaces:
        return
    device_properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
    if path not in devices:
        print("NEW path  :", path)
        devices[path] = device_properties
        dev = devices[path]
        if 'Address' in dev:
            print("NEW bdaddr: ", bluetooth_utils.dbus_to_python(dev['Address']))
        if 'Name' in dev:
            print("NEW name  : ", bluetooth_utils.dbus_to_python(dev['Name']))
        if 'RSSI' in dev:
            print("NEW RSSI  : ", bluetooth_utils.dbus_to_python(dev['RSSI']))
        print("------------------------------")

def interfaces_removed(path, interfaces):
    # interfaces is an array of dictionary strings in this signal
    if not bluetooth_constants.DEVICE_INTERFACE in interfaces:
        return
    if path in devices:
        dev = devices[path]
        if 'Address' in dev:
            print("DEL bdaddr: ", bluetooth_utils.dbus_to_python(dev['Address']))
        else:
            print("DEL path  : ", path)
            print("------------------------------")
        del devices[path]


def properties_changed(interface, changed, invalidated, path):
    if interface != bluetooth_constants.DEVICE_INTERFACE:
        return
    if path in devices:
        devices[path] = dict(devices[path].items())
        devices[path].update(changed.items())
    else:
        devices[path] = changed

    dev = devices[path]
    print("CHG path  :", path)
    if 'Address' in dev:
        print("CHG bdaddr: ", bluetooth_utils.dbus_to_python(dev['Address']))
    if 'Name' in dev:
        print("CHG name  : ", bluetooth_utils.dbus_to_python(dev['Name']))
    if 'RSSI' in dev:
        print("CHG RSSI  : ", bluetooth_utils.dbus_to_python(dev['RSSI']))
    print("------------------------------")

def get_known_devices(bus):
    global managed_objects_found
    object_manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, "/"), bluetooth_constants.DBUS_OM_IFACE)
    managed_objects=object_manager.GetManagedObjects()

    for path, ifaces in managed_objects.items():
        for iface_name in ifaces:
            if iface_name == bluetooth_constants.DEVICE_INTERFACE:
                managed_objects_found += 1
                print("EXI path  : ", path)
                device_properties = ifaces[bluetooth_constants.DEVICE_INTERFACE]
                devices[path] = device_properties
                if 'Address' in device_properties:
                    print("EXI bdaddr: ", bluetooth_utils.dbus_to_python(device_properties['Address']))
                if 'Connected' in device_properties:
                    print("EXI cncted: ", bluetooth_utils.dbus_to_python(device_properties['Connected']))           
                print("------------------------------")
            
def discovery_timeout():
    global adapter_interface
    global mainloop
    global timer_id
    GLib.source_remove(timer_id)
    mainloop.quit()
    adapter_interface.StopDiscovery()
    bus = dbus.SystemBus()
    bus.remove_signal_receiver(interfaces_added,"InterfacesAdded")
    bus.remove_signal_receiver(interfaces_added,"InterfacesRemoved")
    bus.remove_signal_receiver(properties_changed,"PropertiesChanged")
    list_devices_found()
    return True

def discover_devices(bus,timeout):
    global adapter_interface
    global mainloop
    global timer_id
    adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME

    # acquire the adapter interface so we can call its methods 
    adapter_object = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_path)
    adapter_interface=dbus.Interface(adapter_object, bluetooth_constants.ADAPTER_INTERFACE)
    
    # register signal handler functions so we can asynchronously report discovered devices
    
    # InterfacesAdded signal is emitted by BlueZ when an advertising packet from a device it doesn't
    # already know about is received
    bus.add_signal_receiver(interfaces_added,
            dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
            signal_name = "InterfacesAdded")

    # InterfacesRemoved signal is emitted by BlueZ when a device "goes away"
    bus.add_signal_receiver(interfaces_removed,
            dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
            signal_name = "InterfacesRemoved")

    # PropertiesChanged signal is emitted by BlueZ when something re: a device already encountered
    # changes e.g. the RSSI value
    bus.add_signal_receiver(properties_changed,
           dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
            signal_name = "PropertiesChanged",
            path_keyword = "path")
    
    mainloop = GLib.MainLoop()
    timer_id = GLib.timeout_add(timeout, discovery_timeout)
    adapter_interface.StartDiscovery(byte_arrays=True)

    mainloop.run()
    
    device_list = devices.values()
    discovered_devices = []
    for device in device_list:
        dev = {}
        discovered_devices.append(dev)

    return discovered_devices

if (len(sys.argv) != 2):
    print("usage: python3 discover_devices.py [scantime (secs)]")
    sys.exit(1)
    
scantime = int(sys.argv[1]) * 1000

# dbus initialisation steps
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

# ask for a list of devices already known to the BlueZ daemon
print("Listing devices already known to BlueZ:")
get_known_devices(bus)
print("Found ",managed_objects_found," managed device objects")
print("Scanning")
discover_devices(bus, scantime)
