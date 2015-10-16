import logging
import os
import re
import urllib

from gi.repository import GObject
GObject.threads_init()

from gi import require_version
require_version('Gst', '1.0')

from gi.repository import Gst
from gi.repository import Gtk
import random
from blockify import util


log = logging.getLogger("player")


class InterludePlayer(object):
    "A simple gstreamer audio player to play interlude music."
    def __init__(self, blockify):
        Gst.init(None)
        self.Gst = Gst
        self.b = blockify
        self.manual_control = False
        self.temp_autoresume = False
        self.temp_disable = False
        self._index = 0
        self._autoresume = util.CONFIG["interlude"]["autoresume"]
        self.playback_delay = util.CONFIG["interlude"]["playback_delay"]
        # Automatically resume spotify playback after n seconds.
        self.radio_timeout = util.CONFIG["interlude"]["radio_timeout"]
        self.uri_rx = re.compile("[A-Za-z]+:\/\/")
        self.formats = ["mp3", "mp4", "flac", "wav", "wma", "ogg", "avi", "mov", "mpg", "flv", "wmv", \
                        "spx", "3gp", "b-mtp", "aac", "aiff", "raw", "midi", "ulaw", "alaw", "gsm" ]
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.player.connect("about-to-finish", self.on_about_to_finish)
        # Get and watch the bus. We use this in blockify-ui.
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        # self.bus.connect("message::tag", self.on_tag_changed)
        # self.bus.connect("message::eos", self.on_finish)
        # Finally, load the playlist file.
        log.info("InterludePlayer initialized.")
        self.load_playlist(self.parse_playlist(), util.CONFIG["interlude"]["start_shuffled"])

    def load_playlist(self, playlist, shuffle=False):
        "Read the music to be played instead of commercials into a list."
        log.debug("Loading playlist.")
        self.playlist = playlist
        self.max_index = len(self.playlist) - 1
        if shuffle:
            self.shuffle()
        self.stop()
        self.set_uri()
        log.info("Playlist loaded (Length: {}).".format(len(playlist)))
        self.show_playlist()

    def show_playlist(self):
        log.info("Playlist: {0}".format([os.path.basename(i) for i in self.playlist]))

    def parse_playlist(self, sourcelist=None, source=None):
        playlist = []

        if sourcelist is None:
            sourcelist = [util.CONFIG["interlude"]["playlist"]]

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
        return urllib.parse.urljoin("file:", urllib.pathname2url(path))

    def on_about_to_finish(self, player):
        "Song is ending. What do we do?"
        self.queue_next()
        log.debug("Interlude song finished. Queued: {}.".format(self.get_current_uri()))
        if not self.autoresume and not self.b.spotify_is_playing():
            self.pause()
            self.b.dbus.playpause()

    def get_current_uri(self):
        if self.index > self.max_index:
            return "(none)"
        return self.playlist[self.index]

    def is_radio(self):
        "Spot radio tracks so we can deal with them appropriately."
        uri = self.get_current_uri()
        # We assume the URI is a radio station if it doesn't have a file ending we associate with (audio) files.
        return uri.startswith("http://") and not any([uri.endswith("." + fmt) for fmt in self.formats])

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

    def try_resume_spotify_playback(self, ignore_player=False):
        log.info("Trying to resume spotify playback.")
        if (self.is_playing() or ignore_player) and not self.b.found:
            self.pause()
            self.b.dbus.play()

    def resume_spotify_playback(self):
        if not self.b.found:
            self.pause()
            self.b.dbus.play()
            log.info("Switched from radio back to Spotify.")
            return True
        else:
            log.info("Tried to switch from radio to Spotify but commercial still playing. Will resume when commercial ends.")
            self.temp_autoresume = True

        return False

    def playpause(self):
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def play_with_delay(self):
        self.temp_disable = False
        self.toggle_music()
        return False

    def toggle_autoresume(self):
        if self.autoresume:
            self.autoresume = False
        else:
            self.autoresume = True

    def toggle_music(self):
        "Method that gets called every update_interval ms via update()."
        # In some cases (autodetection), we are going to delay toggling a bit,
        # see b.find_ads() and self.play_with_delay().
        if self.temp_disable:
            return
        playing = self.is_playing()
        if self.b.found and not playing and not self.manual_control:
            self.play()
            if self.is_radio() and self.radio_timeout:
                log.info("Radio is playing. Switching back to spotify in "
                         "{}s (or when the ad has finished).".format(self.radio_timeout))
                GObject.timeout_add(self.radio_timeout * 1000, self.resume_spotify_playback)
        elif not self.b.found and playing and self.b.current_song:
            if self.autoresume or self.temp_autoresume:
                self.pause()
                self.temp_autoresume = False
            elif self.b.spotify_is_playing():
                self.b.dbus.playpause()

    def is_playing(self):
        return self.player.get_state(0)[1] == Gst.State.PLAYING

    def is_playable(self):
        return self.player.get_state(0)[0] == Gst.StateChangeReturn.SUCCESS

    def play(self):
        uri = self.get_current_uri()
        if not self.is_playable():
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
        self.player.set_state(Gst.State.PLAYING)
        log.info("Playing interlude: {}".format(self.get_current_uri()))
        log.debug("Play: State is {0}.".format(self.player.get_state(0)))

    def pause(self):
        self.player.set_state(Gst.State.PAUSED)
        log.debug("Pause: State is {0}.".format(self.player.get_state(0)))

    def stop(self):
        self.player.set_state(Gst.State.NULL)
        log.debug("Stop: State is {0}.".format(self.player.get_state(0)))

    def prev(self):
        self.stop()
        self.queue_previous()
        self.play()

    def next(self):
        self.stop()
        self.queue_next()
        self.play()

    def shuffle(self):
#         uri = self.get_current_uri()
        random.shuffle(self.playlist)
        log.info("Playlist was shuffled.")
        # Adjust index to make sure self.get_current_uri() returns the current song.
#         try:
#             self.index = self.playlist.index(uri)
#         except ValueError:
#             self.index = 0

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
    def autoresume(self):
        return self._autoresume

    @autoresume.setter
    def autoresume(self, autoresume):
        log.debug("Setting autoresume to: {0}".format(autoresume))
        self._autoresume = autoresume

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
