#!/usr/bin/env python2
"""blockify

Usage:
    blockify [-l <path>] [-v...] [-q] [-h]

Options:
    -l, --log=<path>  Enables logging to the logfile/-path specified.
    -q, --quiet       Don't print anything to stdout.
    -v                Verbosity of the logging module, up to -vvv.
    -h, --help        Show this help text.
    --version         Show current version of blockify.
"""
import logging
import os
import re
import signal
import subprocess
import sys
from threading import Thread
import time

import gtk
import pygtk
import wnck

import audioplayer
from blocklist import Blocklist
import blockifydbus
import util


try:
    from docopt import docopt
except ImportError:
    print "ImportError: Please install docopt to use the blockify CLI."


pygtk.require("2.0")
log = logging.getLogger("main")
VERSION = "1.4"


class Blockify(object):

    def __init__(self, blocklist):
        self.blocklist = blocklist
        self.orglist = blocklist[:]
        self.configdir = blocklist.configdir
        self.automute = True
        self.autodetect = True
        self.current_song = ""
        self.song_status = ""
        self.is_fully_muted = False
        self.is_sink_muted = False
        self.check_for_blockify_process()
        self.check_for_spotify_process()
        self.dbus = self.init_dbus()
        self.channels = self.init_channels()
        self.player = audioplayer.AudioPlayer(self.configdir)
        self.play_interlude_music = True if len(self.player.playlist) else False

        # Determine if we can use sinks or have to use alsa.
        try:
            devnull = open(os.devnull)
            subprocess.check_output(["pacmd", "list-sink-inputs"], stderr=devnull)
            self.mutemethod = self.pulsesink_mute
        except (OSError, subprocess.CalledProcessError):
            self.mutemethod = self.alsa_mute


        log.info("Blockify initialized.")

    def check_for_blockify_process(self):
        try:
            pid = subprocess.check_output(["pgrep", "-f", "python.*blockify"])
        except subprocess.CalledProcessError:
            pass
        else:
            if pid.strip() != str(os.getpid()):
                log.error("A blockify process is already running. Exiting.")
                sys.exit()

    def check_for_spotify_process(self):
        try:
            subprocess.check_output(["pgrep", "spotify"])
            pidof_out = subprocess.check_output(["pidof", "spotify"])
            self.spotify_pids = pidof_out.decode("utf-8").strip().split(" ")
        except subprocess.CalledProcessError:
            log.error("No spotify process found. Exiting.")
            sys.exit()

    def init_channels(self):
        channel_list = ["Master"]
        amixer_output = subprocess.check_output("amixer")
        if "'Speaker',0" in amixer_output:
            channel_list.append("Speaker")
        if "'Headphone',0" in amixer_output:
            channel_list.append("Headphone")

        return channel_list

    def init_dbus(self):
        try:
            return blockifydbus.BlockifyDBus()
        except Exception as e:
            log.error("Cannot connect to DBus. Exiting.\n ({}).".format(e))
            sys.exit()

    def start(self):
        self.bind_signals()
        self.toggle_mute()
#         gtk.threads_init()
        while True:
            # Initiate gtk loop to enable the window list for .get_windows().
            while gtk.events_pending():
                gtk.main_iteration(False)
            found = self.update()
            if self.play_interlude_music:
                Thread(target=self.toggle_interlude_music(found)).start()
#                 self.toggle_interlude_music(found)

            time.sleep(0.25)

    def current_song_is_ad(self):
        """Compares the wnck song info to dbus song info."""
        if self.song_status == "Playing":
            try:
                return self.current_song != self.dbus.get_song_artist() + \
                u" \u2013 " + self.dbus.get_song_title()
            except TypeError:
                # Spotify has technically stopped playing and has stopped
                # sending dbus metadata so we get NoneType-errors.
                # However, it might still play one last ad so we assume that
                # is the case here.
                return True

    def toggle_interlude_music(self, found):
        playing = self.player.is_playing()
        if found and not playing:
            self.player.play()
        elif not found and playing:
           self.player.pause()

    def update(self):
        "Main loop. Checks for blocklist match and mutes accordingly."

        self.current_song = self.get_current_song()
        self.song_status = self.dbus.get_song_status()

        # Manual control is enabled so we exit here.
        if not self.automute:
            return False

        # No song playing, force unmute.
        if not self.current_song:
            self.toggle_mute(2)
            return False

        if self.autodetect:
            if self.current_song_is_ad():  # Ad found, force mute.
                self.toggle_mute(1)
                return True

        # Check if the blockfile has changed.
        try:
            current_timestamp = self.blocklist.get_timestamp()
        except OSError:
            self.blocklist.__init__()
            current_timestamp = self.blocklist.timestamp
        if self.blocklist.timestamp != current_timestamp:
            log.info("Blockfile changed. Reloading.")
            self.blocklist.__init__(self.configdir)

        for i in self.blocklist:
            if self.current_song.startswith(i):
                self.toggle_mute(1)
                return True  # Return boolean to use as self.found in GUI.

        self.toggle_mute()

        return False

    def get_windows(self):
        "Libwnck list of currently open windows."
        # Get the current screen.
        screen = wnck.screen_get_default()

        # Object list of windows in screen.
        windows = screen.get_windows()

        # Return the Spotify window or an empty list.
        return [win.get_icon_name() for win in windows\
                if len(windows) and "Spotify" in win.get_application().get_name()]

    def get_current_song(self):
        "Checks if a Spotify window exists and returns the current songname."
        spotify_window = self.get_windows()
        song = ""

        if spotify_window:
            song = " ".join(spotify_window[0].split()[2:]).decode("utf-8")

        return song

    def block_current(self):
        if self.current_song:
            self.blocklist.append(self.current_song)

    def unblock_current(self):
        if self.current_song:
            song = self.blocklist.find(self.current_song)
            if song:
                self.blocklist.remove(song)
            else:
                log.error("Not found in blocklist or block pattern too short.")

    def toggle_mute(self, mode=0):
        # 0 = automatic, 1 = force mute, 2 = force unmute
        self.mutemethod(mode)

    def is_muted(self):
        for channel in self.channels:
            output = subprocess.check_output(["amixer", "get", channel])
            if "[off]" in output:
                return True
        return False

    def get_state(self, mode):
        muted = self.is_muted()
        self.is_fully_muted = muted

        state = None

        if muted and (mode == 2 or not self.current_song):
            state = "unmute"
        elif muted and mode == 0:
            state = "unmute"
            log.info("Unmuting.")
        elif not muted and mode == 1:
            state = "mute"
            log.info("Muting {}.".format(self.current_song))


        return state

    def alsa_mute(self, mode):
        "Mute method for systems without Pulseaudio. Mutes sound system-wide."
        state = self.get_state(mode)
        if not state:
            return

        for channel in self.channels:
            subprocess.Popen(["amixer", "-q", "set", channel, state])

    def pulse_mute(self, mode):
        "Used if pulseaudio is installed but no sinks are found. System-wide."
        state = self.get_state(mode)
        if not state:
            return

        for channel in self.channels:
            subprocess.Popen(["amixer", "-qD", "pulse", "set", channel, state])

    def pulsesink_mute(self, mode):
        "Finds spotify's audio sink and toggles its mute state."
        try:
            pacmd_out = subprocess.check_output(["pacmd", "list-sink-inputs"])
        except subprocess.CalledProcessError:
            log.error("Spotify sink not found. Is Pulse running?")
            log.error("Resorting to amixer as mute method.")
            self.mutemethod = self.pulse_mute  # Fall back to amixer mute.
            return

        # Match muted and application.process.id values.
        pattern = re.compile(r"(?: index|muted|application\.process\.id).*?(\w+)")
        # Put valid spotify PIDs in a list
        output = pacmd_out.decode("utf-8")

        spotify_sink_list = [" index: " + i for i in output.split("index: ") if "spotify" in i]

        if not len(spotify_sink_list):
            return

        sink_infos = [pattern.findall(sink) for sink in spotify_sink_list]
        # Every third element per sublist is a key, the value is the preceding
        # two elements in the form of a tuple - {pid : (index, muted)}
        idxd = {info[2]: (info[0], info[1]) for info in sink_infos if len(info) == 3}

        try:
            pid = [k for k in idxd.keys() if k in self.spotify_pids][0]
            index, muted = idxd[pid]
            self.is_sink_muted = True if muted == "yes" else False
        except IndexError:
            return

        if muted == "yes" and (mode == 2 or not self.current_song):
            log.info("Forcing unmute.")
            subprocess.call(["pacmd", "set-sink-input-mute", index, "0"])
        elif muted == "no" and mode == 1:
            log.info("Muting {}.".format(self.current_song))
            subprocess.call(["pacmd", "set-sink-input-mute", index, "1"])
        elif muted == "yes" and not mode:
            log.info("Unmuting.")
            subprocess.call(["pacmd", "set-sink-input-mute", index, "0"])

    def bind_signals(self):
        "Catch SIGINT and SIGTERM to exit cleanly & SIGUSR1 to block a song."
        signal.signal(signal.SIGUSR1, lambda sig, hdl: self.block_current())
        signal.signal(signal.SIGUSR2, lambda sig, hdl: self.unblock_current())
        signal.signal(signal.SIGTERM, lambda sig, hdl: self.stop())
        signal.signal(signal.SIGINT, lambda sig, hdl: self.stop())

    def stop(self):
        log.info("Exiting safely. Bye.")
        # Save the list only if it changed during runtime.
        if self.blocklist != self.orglist:
            self.blocklist.save()
        # Unmute before exiting.
        self.toggle_mute(2)
        sys.exit()

    @property
    def automute(self):
        return self._automute

    @automute.setter
    def automute(self, boolean):
        log.debug("Setting automute to: {}.".format(boolean))
        self._automute = boolean

    @property
    def autodetect(self):
        return self._autodetect

    @autodetect.setter
    def autodetect(self, boolean):
        log.info("Setting autodetect to: {}.".format(boolean))
        self._autodetect = boolean


def initialize():
    try:
        args = docopt(__doc__, version=VERSION)
        util.init_logger(args["--log"], args["-v"] or 2, args["--quiet"])
    except NameError:
        util.init_logger(logpath=None, loglevel=2, quiet=False)
        log.error("Please install docopt to use the CLI.")

    blockify = Blockify(Blocklist(util.get_configdir()))

    return blockify


def main():
    "Entry point for the CLI-version of Blockify."

    blockify = initialize()
    blockify.start()


if __name__ == "__main__":
    main()
