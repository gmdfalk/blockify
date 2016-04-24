#!/usr/bin/env python3
"""dbusclient

Usage:
    dbusclient (toggle | next | prev | stop | play | pause) [-v...] [options]
    dbusclient get [song | title | artist | album | length | status | all] [-v...] [options]
    dbusclient (openuri <uri> | seek <secs> | setpos <pos>) [-v...] [options]

Options:
    -l, --log=<path>  Enables logging to the logfile/-path specified.
    -q, --quiet       Don't print anything to stdout.
    -v                Verbosity of the logging module, up to -vvv.
    -h, --help        Show this help text.
    --version         Show current version of dbusclient.
"""
import logging
import re

import dbus
import sys

from blockify import util

log = logging.getLogger("dbus")


class DBusClient(object):
    """Wrapper for Spotify's DBus interface."""

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
        """Gets the value from any available property."""
        prop = None
        try:
            prop = self.properties.Get(self.player_path, key)
        except dbus.exceptions.DBusException as e:
            self.connect_to_spotify_dbus(None)
            log.error("Failed to get DBus property: {}".format(e))

        return prop

    def set_property(self, key, value):
        """Sets the value for any available property."""
        try:
            self.properties.Set(self.player_path, key, value)
        except Exception as e:
            self.connect_to_spotify_dbus(None)
            log.warn("Cannot Set Property: {}".format(e))

    def playpause(self):
        """Toggles the current song between Play and Pause."""
        try:
            self.player.PlayPause()
        except Exception as e:
            log.warn("Cannot Play/Pause: {}".format(e))

    def play(self):
        """Tries to play the current title."""
        try:
            self.player.Play()
        except Exception as e:
            log.warn("Cannot Play: {}".format(e))

    def pause(self):
        """Tries to pause the current title."""
        try:
            self.player.Pause()
        except Exception as e:
            log.warn("Cannot Pause: {}".format(e))

    def stop(self):
        """Tries to stop playback. PlayPause is probably preferable."""
        try:
            self.player.Stop()
        except Exception as e:
            log.warn("Cannot Stop playback: {}".format(e))

    def next(self):
        """Tries to skip to next song."""
        try:
            self.player.Next()
        except Exception as e:
            log.warn("Cannot Go Next: {}".format(e))

    def prev(self):
        """Tries to go back to last song."""
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
        """Skips n seconds forward."""
        try:
            self.player.Seek(seconds)
        except Exception as e:
            log.warn("Cannot Seek: {}".format(e))

    def get_song_length(self):
        """Gets the length of current song from metadata (in seconds)."""
        length = 0
        try:
            metadata = self.get_property("Metadata")
            length = int(metadata["mpris:length"] / 1000000)
        except Exception as e:
            log.warn("Cannot get song length: {}".format(e))

        return length

    def get_art_url(self):
        """Get album cover"""
        art_url = ""
        try:
            metadata = self.get_property("Metadata")
            art_url = str(metadata["mpris:artUrl"])
        except Exception as e:
            log.error("Cannot fetch album cover url: {}".format(e))

        return art_url

    def get_spotify_url(self):
        """Get spotify url for the track."""
        spotify_url = ""
        try:
            metadata = self.get_property("Metadata")
            spotify_url = str(metadata["xesam:url"])
        except Exception as e:
            log.error("Cannot fetch spotify url: {}".format(e))

        return spotify_url

    def get_song_status(self):
        """Get current PlaybackStatus (Paused/Playing...)."""
        status = ""
        try:
            status = str(self.get_property("PlaybackStatus"))
        except Exception as e:
            log.warn("Cannot get PlaybackStatus: {}".format(e))

        return status

    def get_song(self):
        artist = self.get_song_artist()
        title = self.get_song_title()
        album = self.get_song_album()

        return "{} - {} [{}]".format(artist, title, album)

    def get_song_title(self):
        """Gets title of current song from metadata"""
        title = ""
        try:
            metadata = self.get_property("Metadata")
            title = str(metadata["xesam:title"])
        except Exception as e:
            log.warn("Cannot get song title: {}".format(e))

        return title

    def get_song_album(self):
        """Gets album of current song from metadata"""
        album = ""
        try:
            metadata = self.get_property("Metadata")
            album = str(metadata["xesam:album"])
        except Exception as e:
            log.warn("Cannot get song album: {}".format(e))

        return album

    def get_song_artist(self):
        """Gets the artist of current song from metadata"""
        artist = ""
        try:
            metadata = self.get_property("Metadata")
            artist = str(metadata["xesam:artist"][0])
        except Exception as e:
            log.warn("Cannot get song artist: {}".format(e))

        return artist


def print_all(dbus_client):
    """Print all the DBus info we can get our hands on."""
    try:
        metadata = dbus_client.get_property("Metadata")

        d_keys = list(metadata.keys())
        d_keys.sort()

        for k in d_keys:
            d = k.split(":")[1]

            if d == "artist":
                print("{0}\t\t= {1}".format(d, metadata[k][0]))
            # elif d == "length":
            elif len(d) < 7:
                print("{0}\t\t= {1}".format(d, metadata[k]))
            else:
                print("{0}\t= {1}".format(d, metadata[k]))
    except AttributeError as e:
        log.error("Could not get properties: {}".format(e))


def print_song(dbus_client):
    length = dbus_client.get_song_length()
    m, s = divmod(length, 60)
    rating = dbus_client.get_property("Metadata")["xesam:autoRating"]
    song = dbus_client.get_song()
    print("{}, {}m{}s, {}".format(song, m, s, rating))


def wrap_action(action, *args):
    return {"action": action, "args": args}


def main():
    """Entry point for the CLI DBus interface."""
    args = util.docopt(__doc__, version="0.4.1")
    util.init_logger(args["--log"], args["-v"], args["--quiet"])
    dbus_client = DBusClient()

    args_mapper = {
        "setpos": wrap_action(dbus_client.set_position, args["<pos>"]),
        "openuri": wrap_action(dbus_client.open_uri, args["<uri>"]),
        "seek": wrap_action(dbus_client.seek, args["<secs>"]),
        "toggle": wrap_action(dbus_client.playpause),
        "next": wrap_action(dbus_client.next),
        "prev": wrap_action(dbus_client.prev),
        "play": wrap_action(dbus_client.play),
        "pause": wrap_action(dbus_client.pause),
        "stop": wrap_action(dbus_client.pause),
        "song": wrap_action(dbus_client.get_song),
        "album": wrap_action(dbus_client.get_song_album),
        "artist": wrap_action(dbus_client.get_song_artist),
        "length": wrap_action(dbus_client.get_song_length),
        "title": wrap_action(dbus_client.get_song_title),
        "status": wrap_action(dbus_client.get_song_status),
        "all": wrap_action(print_all, dbus_client),
    }

    for arg_key, arg_value in args.items():
        action_info = args_mapper.get(arg_key, None)
        if arg_value and action_info:
            action = action_info.get("action", None)
            if action:
                action_args = action_info.get("args", None)
                result = action(*action_args) if action_args else action()
                if result:
                    print(result)
                sys.exit()

    # Since get can have follow-up actions it has to be handled last and separately.
    if args.get("get", None):
        print_song(dbus_client)


if __name__ == "__main__":
    main()
