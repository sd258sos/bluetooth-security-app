#!/usr/bin/python3
# https://www.freedesktop.org/software/systemd/man/org.freedesktop.hostname1.html

import dbus

bus = dbus.SystemBus()
proxy = bus.get_object('org.freedesktop.hostname1','/org/freedesktop/hostname1')
interface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')

all_props = interface.GetAll('org.freedesktop.hostname1')
print(all_props)

print("----------------")
hostname = interface.Get('org.freedesktop.hostname1','Hostname')
print("The host name is ",hostname)

