#!/usr/bin/env python3

import dbus
import re

class Spotify(object):

    def __init__():

    def find_spotify():
        bus = dbus.SessionBus()
        spotifies = set()
        for name in bus.list_names():
            if re.match(r'.*mpris.*spotify', name):
                spotifies.add(str(name))
                print(name)
        return spotifies[-1]


def main():
    find_spotify()

if __name__ == "__main__":
    main()
