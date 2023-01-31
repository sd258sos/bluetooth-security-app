#!/usr/bin/python3
# Advertises, accepts a connection, creates the microbit temperature service, LED service and their characteristics

import bluetooth_constants
import bluetooth_gatt
import bluetooth_utils
import bluetooth_exceptions
import dbus
import dbus.exceptions
import dbus.service
import dbus.mainloop.glib
import sys
import random
from gi.repository import GObject
from gi.repository import GLib
sys.path.insert(0, '.')

bus = None
adapter_path = None
adv_mgr_interface = None
connected = 0

# much of this code was copied or inspired by test\example-advertisement in the BlueZ source
class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/ldsg/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = 'Hello'
        self.include_tx_power = False
        self.data = None
        self.discoverable = True
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.discoverable is not None and self.discoverable == True:
            properties['Discoverable'] = dbus.Boolean(self.discoverable)
        if self.include_tx_power:
            properties['Includes'] = dbus.Array(["tx-power"], signature='s')

        if self.data is not None:
            properties['Data'] = dbus.Dictionary(
                self.data, signature='yv')
        print(properties)
        return {bluetooth_constants.ADVERTISING_MANAGER_INTERFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(bluetooth_constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != bluetooth_constants.ADVERTISEMENT_INTERFACE:
            raise bluetooth_exceptions.InvalidArgsException()
        return self.get_properties()[bluetooth_constants.ADVERTISING_MANAGER_INTERFACE]

    @dbus.service.method(bluetooth_constants.ADVERTISING_MANAGER_INTERFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        print('%s: Released' % self.path)


class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        print("Adding TemperatureService to the Application")
        self.add_service(TemperatureService(bus, '/org/bluez/ldsg', 0))
        self.add_service(LedService(bus, '/org/bluez/ldsg', 1))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(bluetooth_constants.DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            print("GetManagedObjects: service="+service.get_path())
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response

class TemperatureService(bluetooth_gatt.Service):
#   Fake micro:bit temperature service that simulates temperature sensor measurements
#   ref: https://lancaster-university.github.io/microbit-docs/resources/bluetooth/bluetooth_profile.html
#   temperature_period characteristic not implemented to keep things simple

     def __init__(self, bus, path_base, index):
        print("Initialising TemperatureService object")
        bluetooth_gatt.Service.__init__(self, bus, path_base, index, bluetooth_constants.TEMPERATURE_SVC_UUID, True)
        print("Adding TemperatureCharacteristic to the service")
        self.add_characteristic(TemperatureCharacteristic(bus, 0, self))

class TemperatureCharacteristic(bluetooth_gatt.Characteristic):
    temperature = 0
    delta = 0
    notifying = False
    
    def __init__(self, bus, index, service):
        global timer_id
        bluetooth_gatt.Characteristic.__init__(
                self, bus, index,
                bluetooth_constants.TEMPERATURE_CHR_UUID,
                ['read','notify'],
                service)
        self.notifying = False
        self.temperature = random.randint(0, 50)
        print("Initial temperature set to "+str(self.temperature))
        self.delta = 0
        timer_id = GLib.timeout_add(1000, self.simulate_temperature)

    def simulate_temperature(self):
        self.delta = random.randint(-1, 1)
        self.temperature = self.temperature + self.delta
        if (self.temperature > 50):
            self.temperature = 50
        elif (self.temperature < 0):
            self.temperature = 0     
        # print("simulated temperature: "+str(self.temperature)+"C")
        if self.notifying:
            self.notify_temperature()

        GLib.timeout_add(1000, self.simulate_temperature)

    def ReadValue(self, options):
        print('ReadValue in TemperatureCharacteristic called')
        print('Returning '+str(self.temperature))
        value = []
        value.append(dbus.Byte(self.temperature))
        return value
    
    # called by timer expiry
    # simulated temperature will fluctuate between 0 and 50 degrees celsius with randomly selected
    # deltas of at most +/- 5 degrees

    def notify_temperature(self):
        value = []
        value.append(dbus.Byte(self.temperature))
        if self.notifying:
            print("notifying temperature="+str(self.temperature))
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, { 'Value': value }, [])
        return self.notifying

    # note this overrides the same method in bluetooth_gatt.Characteristic where it is exported to 
    # make it visible over DBus
    def StartNotify(self):
        print("starting notifications")
        self.notifying = True

    def StopNotify(self):
        print("stopping notifications")
        self.notifying = False

class LedService(bluetooth_gatt.Service):
#   Fake micro:bit LED service that uses the console as a pretend microbit LED display for text only
#   ref: https://lancaster-university.github.io/microbit-docs/resources/bluetooth/bluetooth_profile.html
#   LED Matrix characteristic not implemented to keep things simple

     def __init__(self, bus, path_base, index):
        print("Initialising LedService object")
        bluetooth_gatt.Service.__init__(self, bus, path_base, index, bluetooth_constants.LED_SVC_UUID, True)
        print("Adding LedTextharacteristic to the service")
        self.add_characteristic(LedTextCharacteristic(bus, 0, self))

class LedTextCharacteristic(bluetooth_gatt.Characteristic):

    text = ""
    
    def __init__(self, bus, index, service):
        bluetooth_gatt.Characteristic.__init__(
                self, bus, index,
                bluetooth_constants.LED_TEXT_CHR_UUID,
                ['write'],
                service)

    def WriteValue(self, value, options):
        ascii_bytes = bluetooth_utils.dbus_to_python(value)
        text = ''.join(chr(i) for i in ascii_bytes)
        print(str(ascii_bytes) + " = " + text)
        

def register_ad_cb():
    print('Advertisement registered OK')

def register_ad_error_cb(error):
    print('Error: Failed to register advertisement: ' + str(error))
    mainloop.quit()

def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()

def set_connected_status(status):
    if (status == 1):
        print("connected")
        connected = 1
        stop_advertising()
    else:
        print("disconnected")
        connected = 0
        start_advertising()

def properties_changed(interface, changed, invalidated, path):
    if (interface == bluetooth_constants.DEVICE_INTERFACE):
        if ("Connected" in changed):
            set_connected_status(changed["Connected"])

def interfaces_added(path, interfaces):
    if bluetooth_constants.DEVICE_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
        if ("Connected" in properties):
            set_connected_status(properties["Connected"])

def stop_advertising():
    global adv
    global adv_mgr_interface
    print("Unregistering advertisement",adv.get_path())
    adv_mgr_interface.UnregisterAdvertisement(adv.get_path())

def start_advertising():
    global adv
    global adv_mgr_interface
    # we're only registering one advertisement object so index (arg2) is hard coded as 0
    print("Registering advertisement",adv.get_path())
    adv_mgr_interface.RegisterAdvertisement(adv.get_path(), {},
                                        reply_handler=register_ad_cb,
                                        error_handler=register_ad_error_cb)

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
# we're assuming the adapter supports advertising
adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME
adv_mgr_interface = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,adapter_path), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)

service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_path),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

bus.add_signal_receiver(properties_changed,
        dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
        signal_name = "PropertiesChanged",
        path_keyword = "path")

bus.add_signal_receiver(interfaces_added,
        dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
        signal_name = "InterfacesAdded")


# we're only registering one advertisement object so index (arg2) is hard coded as 0
adv_mgr_interface = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,adapter_path), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)
adv = Advertisement(bus, 0, 'peripheral')
start_advertising()

app = Application(bus)

mainloop = GLib.MainLoop()

print('Registering GATT application...')

service_manager.RegisterApplication(app.get_path(), {},
                                reply_handler=register_app_cb,
                                error_handler=register_app_error_cb)

mainloop.run()

