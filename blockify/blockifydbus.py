#!/usr/bin/env python2
"""blockifydbus

Usage:
    blockifydbus (toggle | next | prev | stop | play) [-v...] [options]
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

        if not bus:
            bus = dbus.SessionBus()
        self.session_bus = bus

        for name in bus.list_names():
            if re.match(r".*mpris.*spotify", name):
                self.spotify_path = str(name)

        if self.is_running():
            self.proxy = self.session_bus.get_object(self.spotify_path,
                                                     self.obj_path)
            self.properties = dbus.Interface(self.proxy, self.prop_path)
            self.player = dbus.Interface(self.proxy, self.player_path)
        else:
            self.properties = None
            self.player = None
            self.proxy = None
            log.error("Spotify not found in DBus session. Is it running?")

    def is_running(self):
        "TODO: This is  redundant"
        return self.spotify_path is not None

    def get_property(self, key):
        "Gets the value from any available property."
        if self.is_running():
            try:
                return self.properties.Get(self.player_path, key)
            except dbus.exceptions.DBusException as e:
                log.error("Failed to get DBus property. Disabling dbus-mode. Msg: {}".format(e))
                self.spotify_path = None

    def set_property(self, key, value):
        "Sets the value for any available property."
        if self.is_running():
            return self.properties.Set(self.player_path, key, value)

    def playpause(self):
        "Toggles the current song between Play and Pause."
        if self.is_running():
            can_pause = self.get_property("CanPause")
            can_play = self.get_property("CanPlay")
            if can_pause and can_play:
                self.player.PlayPause()
            else:
                log.warn("Cannot Play/Pause")

    def play(self):
        "DEFUNCT: Tries to play the current title."
        if self.is_running():
            can_play = self.get_property("CanPlay")
            if can_play:
                self.player.Play()
            else:
                log.warn("Cannot Play")

    def stop(self):
        "Tries to stop playback. PlayPause is probably preferable."
        if self.is_running():
            self.player.Stop()

    def next(self):
        "Tries to skip to next song."
        if self.is_running():
            can_next = self.get_property("CanGoNext")
            if can_next:
                self.player.Next()
            else:
                log.warn("Cannot Go Next")

    def prev(self):
        "Tries to go back to last song."
        if self.is_running():
            can_prev = self.get_property("CanGoPrevious")
            if can_prev:
                self.player.Previous()
            else:
                log.warn("Cannot Go Previous.")

    def set_position(self, track, position):
        if self.is_running():
            self.player.SetPosition(track, position)

    def open_uri(self, uri):
        if self.is_running():
            self.player.OpenUri(uri)

    def seek(self, seconds):
        "DEFUNCT: Calls seek method."
        if self.is_running():
            can_seek = self.get_property("CanSeek")
            if can_seek:
                self.player.Seek(seconds)
            else:
                log.warn("Cannot Seek.")

    def get_art_url(self):
        "Get album cover"
        url = ""
        if self.is_running():
            metadata = self.get_property("Metadata")
            if metadata:
                url = metadata["mpris:artUrl"].encode("utf-8")
        return url

    def get_song_status(self):
        "Get current PlaybackStatus (Paused/Playing...)."
        status = ""
        if self.is_running():
            status = self.get_property("PlaybackStatus")
        return status

    def get_song_length(self):
        "Gets the length of current song from metadata (in seconds)."
        length = 0
        if self.is_running():
            metadata = self.get_property("Metadata")
            if metadata:
                length = int(metadata["mpris:length"] / 1000000)
        return length

    def get_song_title(self):
        "Gets title of current song from metadata"
        title = ""
        if self.is_running():
            metadata = self.get_property("Metadata")
            if metadata:
                title = metadata["xesam:title"].encode("utf-8")
        return title

    def get_song_album(self):
        "Gets album of current song from metadata"
        album = ""
        if self.is_running():
            metadata = self.get_property("Metadata")
            if metadata:
                album = metadata["xesam:album"].encode("utf-8")
        return album

    def get_song_artist(self):
        "Gets the artist of current song from metadata"
        artist = ""
        if self.is_running():
            metadata = self.get_property("Metadata")
            if metadata:
                artist = metadata["xesam:artist"][0].encode("utf-8")
        return artist

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
