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

import gtk
import pygtk
import wnck

import blockifydbus
import blocklist
import util


log = logging.getLogger("main")
pygtk.require("2.0")

try:
    from docopt import docopt
except ImportError:
    log.error("ImportError: Please install docopt to use the CLI.")


class Blockify(object):

    def __init__(self, blocklist):
        self.blocklist = blocklist
        self.orglist = blocklist[:]
        self.check_for_blockify_process()
        self.check_for_spotify_process()

        self.options = util.load_options()

        self._autodetect = self.options["general"]["autodetect"]
        self._automute = self.options["general"]["automute"]
        self.update_interval = self.options["cli"]["update_interval"]
        self.unmute_delay = self.options["cli"]["unmute_delay"]
        self.found = False
        self.current_song = ""
        self.song_status = ""
        self.is_fully_muted = False
        self.is_sink_muted = False
        self.dbus = self.init_dbus()
        self.channels = self.init_channels()
        # The gst library used by interludeplayer for some reason modifies
        # argv, overwriting some of docopts functionality in the process,
        # so we import gst here, where docopts cannot be broken anymore.
        import interludeplayer
        self.player = interludeplayer.InterludePlayer(self)

        # Determine if we can use sinks or have to use alsa.
        try:
            devnull = open(os.devnull)
            subprocess.check_output(["pacmd", "list-sink-inputs"], stderr=devnull)
            self.mutemethod = self.pulsesink_mute
            log.debug("Mute method is pulse sink.")
        except (OSError, subprocess.CalledProcessError):
            log.info("No pulse sinks found, falling back to system mute via alsa.")
            self.mutemethod = self.alsa_mute

        # Only use interlude music if we use pulse sinks and the interlude playlist is non-empty.
        self.use_interlude_music = self.options["interlude"]["use_interlude_music"] and \
                                   self.mutemethod == self.pulsesink_mute and \
                                   self.player.max_index >= 0

        log.info("Blockify initialized.")

    def check_for_blockify_process(self):
        try:
            pid = subprocess.check_output(["pgrep", "-f", "python.*blockify"])
        except subprocess.CalledProcessError:
            # No blockify process found. Great, this is what we want.
            pass
        else:
            if pid.strip() != str(os.getpid()):
                log.error("A blockify process is already running. Exiting.")
                sys.exit()

    def check_for_spotify_process(self):
        try:
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

        gtk.threads_init()
        gtk.timeout_add(self.update_interval, self.update)
        log.info("Blockify started.")
        gtk.main()

    def update(self):
        "Main update routine, looped every self.update_interval milliseconds."
        # Determine if a commercial is running and act accordingly.
        self.found = self.find_ad()

        # Adjust playback of interlude music.
        if self.use_interlude_music:
            self.player.toggle_music()

        # Always return True to keep looping this method.
        return True

    def find_ad(self):
        "Main loop. Checks for ads and mutes accordingly."
        self.current_song = self.get_current_song()
        self.song_status = self.dbus.get_song_status()
        self.dbus.is_playing = self.song_status == "Playing"

        # Manual control is enabled so we exit here.
        if not self.automute:
            return False

        if self.autodetect and self.current_song and self.current_song_is_ad():
            if self.use_interlude_music and not self.player.temp_disable:
                self.player.temp_disable = True
                gtk.timeout_add(self.player.playback_delay, self.player.play_with_delay)
            self.ad_found()
            return True

        # Check if the blockfile has changed.
        try:
            current_timestamp = self.blocklist.get_timestamp()
        except OSError as e:
            log.debug("Failed reading blocklist timestamp: {}. Recovering.".format(e))
            self.blocklist.__init__()
            current_timestamp = self.blocklist.timestamp
        if self.blocklist.timestamp != current_timestamp:
            log.info("Blockfile changed. Reloading.")
            self.blocklist.__init__()

        for i in self.blocklist:
            if self.current_song.startswith(i):
                self.ad_found()
                return True

        # Unmute with a certain delay to avoid the last second
        # of commercial you sometimes hear because it's unmuted too early.
        gtk.timeout_add(self.unmute_delay, self.unmute_with_delay)

        return False

    def ad_found(self):
        # log.debug("Ad found: {0}".format(self.current_song))
        self.toggle_mute(1)

    def current_song_is_ad(self):
        "Compares the wnck song info to dbus song info."
        try:
            is_ad = self.current_song != self.dbus.get_song_artist() + u" \u2013 " + self.dbus.get_song_title()
            return self.dbus.is_playing and is_ad
        except TypeError as e:
            # Spotify has technically stopped playing and sending dbus
            # metadata so we get NoneType-errors.
            # However, it might still play one last ad so we assume that
            # is the case here.
            log.debug("TypeError during ad detection: {}".format(e))
            return True

    def unmute_with_delay(self):
        if not self.found:
            self.toggle_mute()
        return False

    def get_windows(self):
        "Libwnck list of currently open windows."
        # Get the current screen.
        screen = wnck.screen_get_default()
        screen.force_update()

        # Object list of windows in screen.
        windows = screen.get_windows()

        # Return the Spotify window or an empty list.
        return [win.get_icon_name() for win in windows\
                if len(windows) and "Spotify" in win.get_application().get_name()]

    def get_current_song(self):
        "Checks if a Spotify window exists and returns the current songname."
        song = ""
        spotify_window = self.get_windows()

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
            log.error("Spotify sink not found. Is Pulse running? Resorting to pulse amixer as mute method.")
            self.mutemethod = self.pulse_mute  # Fall back to amixer mute.
            self.use_interlude_music = False
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
        except IndexError as e:
            log.debug("Could not match spotify pid to sink pid: {}".format(e))
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
        # Stop the interlude player.
        if self.use_interlude_music:
            self.use_interlude_music = False
            self.player.stop()
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
        log.debug("Automute: {}.".format(boolean))
        self._automute = boolean

    @property
    def autodetect(self):
        return self._autodetect

    @autodetect.setter
    def autodetect(self, boolean):
        log.debug("Autodetect: {}.".format(boolean))
        self._autodetect = boolean


def initialize(doc=__doc__):
    # Set up the configuration directory & files, if necessary.
    util.init_config_dir()

    try:
        args = docopt(doc, version=util.BLOCKIFY_VERSION)
        util.init_logger(args["--log"], args["-v"], args["--quiet"])
    except NameError:
        util.init_logger()

    blockify = Blockify(blocklist.Blocklist())

    return blockify


def main():
    "Entry point for the CLI-version of Blockify."
    blockify = initialize()
    blockify.start()


if __name__ == "__main__":
    main()
