#!/usr/bin/python3
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

mainloop = None

def greeting_signal_received(greeting):
	print(greeting)

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
bus.add_signal_receiver(greeting_signal_received,
		dbus_interface = "com.example.greeting",
		signal_name = "GreetingSignal")

mainloop = GLib.MainLoop()
mainloop.run()