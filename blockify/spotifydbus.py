"""spotifydbus

Usage:
    spotifydbus (toggle | next | prev | get [title|artist|length] | info)
"""
import logging
import re

import dbus
from docopt import docopt


log = logging.getLogger("dbus")


class SpotifyDBus(object):
    "Wrapper for Spotify's DBus interface."

    def __init__(self, bus=None):
        self.obj_path = "/org/mpris/MediaPlayer2"
        self.prop_path = "org.freedesktop.DBus.Properties"
        self.player_path = "org.mpris.MediaPlayer2.Player"
        self.spotify_path = None

        if not bus:
            bus = dbus.SessionBus()
        self.session_bus = bus

        for name in bus.list_names():
            if re.match(r".*mpris.*spotify", name):
                self.spotify_path = str(name)

        if self.spotify_path:
            self.proxy = self.session_bus.get_object(self.spotify_path,
                                                     self.obj_path)
            self.properties = dbus.Interface(self.proxy, self.prop_path)
            self.player = dbus.Interface(self.proxy, self.player_path)
        else:
            self.proxy = None
            log.error("Is Spotify running?")


    def is_running(self):
        "TODO: Make this not redundant"
        if self.spotify_path is None:
            return False
        return True


    def get_property(self, key):
        "Gets the value from any available property."
        if self.properties:
            return self.properties.Get(self.player_path, key)


    def set_property(self, key, value):
        "Sets the value for any available property."
        if self.properties:
            return self.properties.Set(self.player_path, key, value)


    def toggle_pause(self):
        "Calls PlayPause method."
        if self.player:
            can_pause = self.get_property("CanPause")
            can_play = self.get_property("CanPlay")
            if can_pause and can_play:
                self.player.PlayPause()
            else:
                log.warn("Cannot Play/Pause")


    def next(self):
        "Tries to skip to next song."
        if self.player:
            can_next = self.get_property("CanGoNext")
            if can_next:
                self.player.Next()
            else:
                log.warn("Cannot Go Next")


    def prev(self):
        "Tries to go back to last song."
        if self.player:
            can_prev = self.get_property("CanGoPrevious")
            if can_prev:
                self.player.Previous()
            else:
                log.warn("Cannot Go Previous.")


    def seek(self, seconds):
        "Calls (nonworking?) seek method."
        if self.player:
            can_seek = self.get_property("CanSeek")
            if can_seek:
                self.player.Seek(seconds)
            else:
                log.warn("Cannot Seek.")


    def get_song_length(self):
        "Gets the length of current song from metadata (in seconds)."
        metadata = self.get_property("Metadata")
        if metadata:
            return int(metadata["mpris:length"] / 1000000)


    def get_song_title(self):
        "Gets title of current song from metadata"
        metadata = self.get_property("Metadata")
        if metadata:
            return str(metadata["xesam:title"])


    def get_song_artist(self):
        "Gets the artist of current song from metadata"
        metadata = self.get_property("Metadata")
        if metadata:
            return str(metadata["xesam:artist"][0])


    def print_info(self):
        "Print all the DBus info we can get our hands on."
        try:
            interfaces = self.properties.GetAll(self.player_path)
            metadata = self.get_property("Metadata")

            i_keys = list(map(str, interfaces.keys()))
            i_keys.remove("Metadata")
            i_keys.sort()

            for i in i_keys:
                if len(i) < 7:
                    print i, "\t\t= ", self.get_property(i)
                else:
                    print i, "\t= ", self.get_property(i)

            print ""

            d_keys = list(metadata.keys())
            d_keys.sort()

            for k in d_keys:
                d = k.split(":")[1]

                if d == "artist":
                    print d, "\t\t= ", metadata[k][0]
                # elif d == "length":
                elif len(d) < 7:
                    print d, "\t\t= ", metadata[k]
                else:
                    print d, "\t= ", metadata[k]
        except AttributeError as e:
            log.error("Could not get properties: {}".format(e))


if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")
    s = SpotifyDBus()
    if args["toggle"]:
        s.toggle_pause()
    elif args["next"]:
        s.next()
    elif args["prev"]:
        s.prev()
    elif args["info"]:
        s.print_info()
    elif args["get"]:
        if args["title"]:
            print s.get_song_title()
        elif args["artist"]:
            print s.get_song_artist()
        elif args["length"]:
            length = s.get_song_length()
            lentup = divmod(s.get_song_length(), 60)
            print "{}m{}s ({})".format(lentup[0], lentup[1], length)
        else:
            print s.get_song_artist(), "-", s.get_song_title()
