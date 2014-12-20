import logging
import os

import gst


log = logging.getLogger("player")


class AudioPlayer(object):
    "A simple gstreamer audio player to play a list of mp3 files."
    def __init__(self, configdir):
        self._index = 0
        self.configdir = configdir
        self.playlist = self.open_playlist()
        self.max_index = len(self.playlist) - 1
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.connect("about-to-finish", self.on_about_to_finish)
#         self.bus = self.player.get_bus()
#         self.bus.add_signal_watch()
#         self.bus.connect("message::eos", self.on_finish)
        self.set_uri()

    def open_playlist(self):
        "Read the music to be played instead of commercials into a list."
        playlist = []
        playlist_file = os.path.join(self.configdir, "playlist")
        if os.path.exists(playlist_file):
            playlist = [line.strip() for line in open(playlist_file) if self.is_valid_uri(line)]  # if line and not line.startswith("#")]
            log.debug("Interlude playlist is: {0}".format(playlist))
        else:
            open(playlist_file, "w").close()
            log.info("No interlude playlist found. Created one at {0}.".format(playlist_file))

        return playlist

    def on_about_to_finish(self, player):
        "Queue the queue_next song right before the current one ends"
        self.queue_next()

    def get_current_index(self):
        if self.index > self.max_index:
            return "(none)"
        return self.playlist[self.index]

    def is_radio(self):
        return self.get_current_index().startswith("http://")

    def is_valid_uri(self, line):
        exclusions = [not line, line.startswith("#")]
        inclusions = [line.startswith("file://"), line.startswith("http://"), line.startswith("mms://")]
        derp = not any(exclusions) and any(inclusions)
        print line, derp, exclusions, inclusions
        return derp

    def is_playing(self):
        return self.player.get_state()[1] is gst.STATE_PLAYING

    def is_playable(self):
        return self.player.get_state()[0] is gst.STATE_CHANGE_SUCCESS

    def play(self):
        if not self.is_playable():
            log.info("Skipping: {} (not playable).".format(self.get_current_index()))
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
            uri = self.get_current_index()
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
        print self.max_index
        if idx > self.max_index or idx < 0:
            idx = 0
        log.debug("Setting index to: {}.".format(idx))
        self._index = idx
