#!/usr/bin/env python2
"""blockifydbus

Usage:
    blockifydbus (toggle | next | prev | stop | play | pause) [-v...] [options]
    blockifydbus get [title | artist | length | status | all] [-v...] [options]
    blockifydbus (openuri <uri> | seek <secs> | setpos <pos>) [-v...] [options]

Options:
    -l, --log=<path>  Enables logging to the logfile/-path specified.
    -q, --quiet       Don't print anything to stdout.
    -v                Verbosity of the logging module, up to -vvv.
    -h, --help        Show this help text.
    --version         Show current version of blockifydbus.
"""
import logging
import re

import dbus

import util


log = logging.getLogger("dbus")


try:
    from docopt import docopt
except ImportError:
    log.error("ImportError: Please install docopt to use the DBus CLI.")


class BlockifyDBus(object):
    "Wrapper for Spotify's DBus interface."

    def __init__(self, bus=None):
        self.obj_path = "/org/mpris/MediaPlayer2"
        self.prop_path = "org.freedesktop.DBus.Properties"
        self.player_path = "org.mpris.MediaPlayer2.Player"
        self.spotify_path = None

        self.connect_to_spotify_dbus(bus)

    def connect_to_spotify_dbus(self, bus):
        if not bus:
            bus = dbus.SessionBus()
        self.session_bus = bus

        for name in bus.list_names():
            if re.match(r".*mpris.*spotify", name):
                self.spotify_path = str(name)

        try:
            self.proxy = self.session_bus.get_object(self.spotify_path,
                                                     self.obj_path)
            self.properties = dbus.Interface(self.proxy, self.prop_path)
            self.player = dbus.Interface(self.proxy, self.player_path)
        except Exception as e:
            log.error("Could not connect to Spotify dbus session: {}".format(e))

    def get_property(self, key):
        "Gets the value from any available property."
        prop = None
        try:
            prop = self.properties.Get(self.player_path, key)
        except dbus.exceptions.DBusException as e:
            self.connect_to_spotify_dbus(None)
            log.error("Failed to get DBus property: {}".format(e))
        return prop

    def set_property(self, key, value):
        "Sets the value for any available property."
        try:
            self.properties.Set(self.player_path, key, value)
        except Exception as e:
            self.connect_to_spotify_dbus(None)
            log.warn("Cannot Set Property: {}".format(e))

    def playpause(self):
        "Toggles the current song between Play and Pause."
        try:
            self.player.PlayPause()
        except Exception as e:
            log.warn("Cannot Play/Pause: {}".format(e))

    def play(self):
        "Tries to play the current title."
        try:
            self.player.Play()
        except Exception as e:
            log.warn("Cannot Play: {}".format(e))

    def pause(self):
        "Tries to pause the current title."
        try:
            self.player.Pause()
        except Exception as e:
            log.warn("Cannot Pause: {}".format(e))

    def stop(self):
        "Tries to stop playback. PlayPause is probably preferable."
        try:
            self.player.Stop()
        except Exception as e:
            log.warn("Cannot Stop playback: {}".format(e))

    def next(self):
        "Tries to skip to next song."
        try:
            self.player.Next()
        except Exception as e:
            log.warn("Cannot Go Next: {}".format(e))

    def prev(self):
        "Tries to go back to last song."
        try:
            self.player.Previous()
        except Exception as e:
            log.warn("Cannot Go Previous: {}".format(e))

    def set_position(self, track, position):
        try:
            self.player.SetPosition(track, position)
        except Exception as e:
            log.warn("Cannot Set Position: {}".format(e))


    def open_uri(self, uri):
        try:
            self.player.OpenUri(uri)
        except Exception as e:
            log.warn("Cannot Open URI: {}".format(e))


    def seek(self, seconds):
        "Skips n seconds forward."
        try:
            self.player.Seek(seconds)
        except Exception as e:
            log.warn("Cannot Seek: {}".format(e))

    def get_art_url(self):
        "Get album cover"
        url = ""
        try:
            metadata = self.get_property("Metadata")
            url = metadata["mpris:artUrl"].encode("utf-8")
        except Exception as e:
            log.error("Cannot fetch album cover: {}".format(e))
        return url

    def get_song_status(self):
        "Get current PlaybackStatus (Paused/Playing...)."
        status = ""
        try:
            status = self.get_property("PlaybackStatus")
        except Exception as e:
            log.warn("Cannot get PlaybackStatus: {}".format(e))

        return status

    def get_song_length(self):
        "Gets the length of current song from metadata (in seconds)."
        length = 0
        try:
            metadata = self.get_property("Metadata")
            length = int(metadata["mpris:length"] / 1000000)
        except Exception as e:
            log.warn("Cannot get song length: {}".format(e))

        return length

    def get_song_title(self):
        "Gets title of current song from metadata"
        title = ""
        try:
            metadata = self.get_property("Metadata")
            title = metadata["xesam:title"].encode("utf-8")
        except Exception as e:
            log.warn("Cannot get song title: {}".format(e))

        return title

    def get_song_album(self):
        "Gets album of current song from metadata"
        album = ""
        try:
            metadata = self.get_property("Metadata")
            album = metadata["xesam:album"].encode("utf-8")
        except Exception as e:
            log.warn("Cannot get song album: {}".format(e))

        return album

    def get_song_artist(self):
        "Gets the artist of current song from metadata"
        artist = ""
        try:
            metadata = self.get_property("Metadata")
            artist = metadata["xesam:artist"][0].encode("utf-8")
        except Exception as e:
            log.warn("Cannot get song artist: {}".format(e))

        return artist

    def print_info(self):
        "Print all the DBus info we can get our hands on."
        try:
            metadata = self.get_property("Metadata")

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



def main():
    "Entry point for the CLI DBus interface."
    args = docopt(__doc__, version="0.2")
    util.init_logger(args["--log"], args["-v"], args["--quiet"])
    dbus = BlockifyDBus()

    if args["toggle"]:
        dbus.playpause()
    elif args["next"]:
        dbus.next()
    elif args["prev"]:
        dbus.prev()
    elif args["play"]:
        dbus.play()
    elif args["pause"]:
        dbus.pause()
    elif args["stop"]:
        dbus.stop()

    if args["openuri"]:
        dbus.open_uri(args["<uri>"])
    elif args["seek"]:
        dbus.seek(args["<secs>"])
    elif args["setpos"]:
        dbus.set_pos(args["<pos>"])

    if args["title"]:
        print dbus.get_song_title()
    elif args["artist"]:
        print dbus.get_song_artist()
    elif args["status"]:
        print dbus.get_song_status()
    elif args["all"]:
        dbus.print_info()
    elif args["get"]:
        length = dbus.get_song_length()
        m, s = divmod(length, 60)
        if args["length"]:
            print "{}m{}s ({})".format(m, s, length)
        else:
            rating = dbus.get_property("Metadata")["xesam:autoRating"]
            artist = dbus.get_song_artist()
            title = dbus.get_song_title()
            album = dbus.get_song_album()
            state = dbus.get_song_status()
            print "{} - {} ({}), {}m{}s, {} ({})".format(artist, title, album,
                                                         m, s, rating, state)


if __name__ == "__main__":
    main()
