import logging
import os

import gst
import re
import urlparse
import urllib


log = logging.getLogger("player")


class InterludePlayer(object):
    "A simple gstreamer audio player to play interlude music."
    def __init__(self, blockify):
        self.gst = gst
        self.b = blockify
        self._index = 0
        self.manual_control = False
        # Automatically resume spotify playback after n seconds.
        self.max_timeout = self.b.options["interlude"]["max_timeout"]
        self.autoresume = self.b.options["interlude"]["autoresume"]
        self.uri_rx = re.compile("[A-Za-z]+:\/\/")
        self.formats = ["mp3", "mp4", "flac", "wav", "wma", "ogg", "avi", "mov", "mpg", "flv", "wmv", \
                        "spx", "3gp", "b-mtp", "aac", "aiff", "raw", "midi", "ulaw", "alaw", "gsm" ]
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.connect("about-to-finish", self.on_about_to_finish)
        # Get and watch the bus. We use this in blockify-ui.
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        # self.bus.connect("message::tag", self.on_tag_changed)
        # self.bus.connect("message::eos", self.on_finish)
        # Finally, load the playlist file.
        log.info("InterludePlayer initialized.")
        self.load_playlist(self.parse_playlist())

    def load_playlist(self, playlist):
        "Read the music to be played instead of commercials into a list."
        log.debug("Loading playlist.")
        self.playlist = playlist
        self.max_index = len(self.playlist) - 1
        self.stop()
        self.set_uri()
        log.info("Playlist loaded (Length: {}).".format(len(playlist)))
        log.info("Playlist: {0}".format(playlist))

    def parse_playlist(self, sourcelist=None, source=None):
        playlist = []

        if sourcelist is None:
            sourcelist = [self.b.options["interlude"]["playlist"]]

        try:
            for item in sourcelist:
                item = item.strip()
                if self.is_valid_uri(item):
                    # The item is not a recognizable URI so we assume it's a file.
                    if not self.uri_rx.match(item):
                        # The item is not an absolute path so we treat it as relative.
                        if not os.path.isabs(item):
                            if os.path.isdir(source):
                                item = os.path.join(source, item)
                            item = os.path.join(os.path.dirname(os.path.abspath(source)), item)

                        # Add file protocol prefix to those audio files that are missing it.
                        if any([item.lower().endswith("." + f) for f in self.formats]):
                            item = "file://" + item
                        # Skip non-existing files.
                        if item.startswith("file://") and not os.path.isfile(item[7:]):
                            continue
                    if item.lower().endswith(".m3u"):
                        playlist += self.parse_playlist(open(item), source=item)
                    elif os.path.isdir(item):
                        playlist += self.parse_playlist(os.listdir(item), source=item)
                    else:
                        playlist.append(item)
        except RuntimeError as e:
            # Maximum Recursion Depth exceeded, most likely.
            log.error("Faulty playlist source: {}".format(e))
        except Exception as e:
            log.error("Could not parse playlist source: {}".format(e))

        return playlist

    def path2url(self, path):
        "Properly translate a string to a file URI (i.e. space to %20)."
        return urlparse.urljoin("file:", urllib.pathname2url(path))

    def on_about_to_finish(self, player):
        "Song is ending. What do we do?"
        self.queue_next()
        log.debug("Interlude song finished. Queued: {}.".format(self.get_current_uri()))
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

    def is_valid_uri(self, item):
        "Determine if a item in the playlist file is a valid URI."
        # Lines we exclude right away, these are either:
        # * comments
        # * invalid (empty)
        # * or incompatible (e.g. mms will cause a freeze).
        exclusions = [not item, item.startswith("#"), item.startswith("mms://")]

        item = item.lower()
        # Lines we include as these are likely to be valid URIs.
#         inclusions = [item.startswith("file://"), item.startswith("http://"), item.startswith("mms://")]

        # If item is a file uri, make sure it has a valid (audio/video) format.
        valid_format = [True]
        if item.startswith("file://"):
            valid_format = [item.endswith("." + fmt) for fmt in self.formats + ["m3u"]]

        return not any(exclusions) and any(valid_format)

    def is_playing(self):
        return self.player.get_state()[1] == gst.STATE_PLAYING

    def is_playable(self):
        return self.player.get_state()[0] == gst.STATE_CHANGE_SUCCESS

    def play(self):
        if not self.is_playable():
            uri = self.get_current_uri()
            log.warn("Skipping unplayable item: {}.".format(uri))
            self.queue_next()
            # Remove the troublemaker from the playlist.
            try:
                self.playlist.remove(uri)
                self.max_index = len(self.playlist) - 1
                self.index -= 1
                log.info("Removed unplayable item from playlist: {}.".format(uri))
            except ValueError:
                pass
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
