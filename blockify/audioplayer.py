import logging
import os

import gst


log = logging.getLogger("player")


class AudioPlayer(object):
    "A simple gstreamer audio player to play a list of mp3 files."
    def __init__(self, configdir, dbus):
        self._index = 0
        self.autoresume = True
        self.configdir = configdir
        self.dbus = dbus
        self.playlist = self.open_playlist()
        self.max_index = len(self.playlist) - 1
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.connect("about-to-finish", self.on_about_to_finish)
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
#         self.bus.connect("message::tag", self.on_tag_changed)
#         self.bus.connect("message::eos", self.on_finish)

        self.set_uri()

    def open_playlist(self):
        "Read the music to be played instead of commercials into a list."
        playlist = []
        playlist_file = os.path.join(self.configdir, "playlist")
        if os.path.exists(playlist_file):
            playlist = [line.strip() for line in open(playlist_file) if self.is_valid_uri(line)]
            log.debug("Interlude playlist is: {0}".format(playlist))
        else:
            open(playlist_file, "w").close()
            log.info("No interlude playlist found. Created one at {0}.".format(playlist_file))

        return playlist

    def on_about_to_finish(self, player):
        "Song is ending. What do we do?"
        self.queue_next()
        if not self.autoresume:
            self.stop()
            self.dbus.playpause()

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
        inclusions = [line.startswith("file://"), line.startswith("http://"), line.startswith("mms://")]
        return not any(exclusions) and any(inclusions)

    def is_playing(self):
        return self.player.get_state()[1] is gst.STATE_PLAYING

    def is_playable(self):
        return self.player.get_state()[0] is gst.STATE_CHANGE_SUCCESS

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
