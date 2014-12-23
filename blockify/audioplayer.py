import logging
import os

import gst
import re
import urlparse
import urllib


log = logging.getLogger("player")


class AudioPlayer(object):
    "A simple gstreamer audio player to play a list of mp3 files."
    def __init__(self, blockify):
        self.b = blockify
        self._index = 0
        # (NYI) Automatically resume spotify playback after 600 seconds.
        self.max_timeout = self.b.options["interlude"]["max_timeout"]
        self.autoresume = self.b.options["interlude"]["autoresume"]
        self.uri_rx = re.compile("[A-Za-z]+:\/\/")
        self.formats = ["mp3", "mp4", "flac", "wav", "wma", "ogg", "avi", "mov", "mpg", "flv", "wmv", \
                        "spx", "3gp", "b-mtp", "aac", "aiff", "raw", "midi", "ulaw", "alaw", "gsm" ]
        self.playlist = self.load_playlist()
        self.max_index = len(self.playlist) - 1
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.connect("about-to-finish", self.on_about_to_finish)
        # Get and watch the bus. We use this in blockify-ui.
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        # self.bus.connect("message::tag", self.on_tag_changed)
        # self.bus.connect("message::eos", self.on_finish)
        self.set_uri()

    def load_playlist(self):
        "Read the music to be played instead of commercials into a list."
        playlist = []
        playlist_file = self.b.options["interlude"]["playlist"]
        if os.path.exists(playlist_file):
            playlist = self.parse_playlist_file(playlist_file)
            log.info("Interlude playlist is: {0}".format(playlist))
        else:
            open(playlist_file, "w").close()
            log.info("No interlude playlist found. Created one at {0}.".format(playlist_file))

        return playlist

    def parse_playlist_file(self, playlist_file):
        playlist = []
        for line in open(playlist_file):
            line = line.strip()
            if not self.is_valid_uri(line):
                continue
            # The line is not a recognizable URI so we assume it's a file.
            if not self.uri_rx.match(line):
                print "not uri", line
                # The line is not an absolute path so we treat it as relative.
                if not os.path.isabs(line):
                    line = os.path.join(os.path.abspath(playlist_file), line)
                if any([line.lower().endswith("." + f) for f in self.formats]):
                    line = self.path2url(line)
            playlist.append(line)

        return playlist

    def path2url(self, path):
        return urlparse.urljoin("file:", urllib.pathname2url(path))

    def on_about_to_finish(self, player):
        "Song is ending. What do we do?"
        self.queue_next()
        if not self.autoresume and self.b.dbus.get_song_status() != "Playing":
            self.pause()
            self.b.dbus.playpause()

    def get_current_uri(self):
        if self.index > self.max_index:
            return "(none)"
        return self.playlist[self.index]

    def is_radio(self):
        "Spot radio tracks so we can deal with them appropriately."
        return self.get_current_uri().startswith("http://")

    def is_valid_uri(self, line):
        "Determine if a line in the playlist file is a valid URI."
        # Lines we exclude right away, these are not valid URIs.
        exclusions = [not line, line.startswith("#")]
        # Lines we include as these are likely to be valid URIs.
#         inclusions = [line.startswith("file://"), line.startswith("http://"), line.startswith("mms://")]
        return not any(exclusions)  # and any(inclusions)

    def is_playing(self):
        return self.player.get_state()[1] == gst.STATE_PLAYING

    def is_playable(self):
        return self.player.get_state()[0] == gst.STATE_CHANGE_SUCCESS

    def play(self):
        if not self.is_playable():
            log.info("Skipping: {} (not playable).".format(self.get_current_uri()))
            self.queue_next()
        self.player.set_state(gst.STATE_PLAYING)
        log.debug("Play: State is {0}.".format(self.player.get_state()))

    def pause(self):
        self.player.set_state(gst.STATE_PAUSED)
        log.debug("Pause: State is {0}.".format(self.player.get_state()))

    def stop(self):
        self.player.set_state(gst.STATE_NULL)
        log.debug("Stop: State is {0}.".format(self.player.get_state()))

    def prev(self):
        self.stop()
        self.queue_previous()
        self.play()

    def next(self):
        self.stop()
        self.queue_next()
        self.play()

    def queue_next(self):
        self.index += 1
        self.set_uri()

    def queue_previous(self):
        self.index -= 1
        self.set_uri()

    def set_uri(self):
        # Only allow playback if the playlist is non-empty.
        if self.max_index >= 0:
            uri = self.get_current_uri()
            log.debug("Setting interlude to: {0}".format(uri))
            self.player.set_property("uri", uri)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, n):
        idx = n
        # If we reached the end of the playlist, loop back to the start.
        # Also, don't decrement index below 0.
        if idx > self.max_index or idx < 0:
            idx = 0
        log.debug("Setting index to: {}.".format(idx))
        self._index = idx
