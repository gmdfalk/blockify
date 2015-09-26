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
import time

import gtk
import pygtk
import wnck

import blockifydbus
import blocklist
import util


log = logging.getLogger("main")
pygtk.require("2.0")


class Blockify(object):


    def __init__(self, blocklist):
        self.blocklist = blocklist
        self.orglist = blocklist[:]
        self.check_for_blockify_process()
        self.start_spotify_if_necessary()

        self._autodetect = util.CONFIG["general"]["autodetect"]
        self._automute = util.CONFIG["general"]["automute"]
        self.autoplay = util.CONFIG["general"]["autoplay"]
        self.update_interval = util.CONFIG["cli"]["update_interval"]
        self.unmute_delay = util.CONFIG["cli"]["unmute_delay"]
        self.pulse_unmuted_value = ""
        self.song_delimiter = " - "  # u" \u2013 "
        self.found = False
        self.current_song = ""
        self.previous_song = ""
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

        self.initialize_mute_method()

        self.initialize_pulse_unmuted_value()

        # Only use interlude music if we use pulse sinks and the interlude playlist is non-empty.
        self.use_interlude_music = util.CONFIG["interlude"]["use_interlude_music"] and \
                                   self.mutemethod == self.pulsesink_mute and \
                                   self.player.max_index >= 0

        log.info("Blockify initialized.")


    def start_spotify_if_necessary(self):
        if self.check_for_spotify_process():
            return
        log.error("No spotify process found.")

        if not util.CONFIG["general"]["start_spotify"]:
            log.info("Exiting. Bye.")
            sys.exit()

        self.start_spotify()
        if not self.check_for_spotify_process():
            log.error("Failed to start Spotify!")
            log.info("Exiting. Bye.")
            sys.exit()


    def initialize_pulse_unmuted_value(self):
        """Set 'no' as self.pulse_unmuted_value and try to translate if necessary."""
        unmuted_value = 'no'
        try:
            self.install_locale()
            # Translate 'no' to the system locale.
            unmuted_value = _(unmuted_value)
        except (Exception):
            log.debug("Could not install localization. If your system "
                      "language is not english this *might* lead to unexpected "
                      "mute behaviour. A possible fix is to replace the "
                      "value of unmuted_value in blockify.py with your "
                      "translation of 'no', e.g. 'tak' in polish.")
        self.pulse_unmuted_value = unmuted_value


    def initialize_mute_method(self):
        """Determine if we can use sinks or have to use alsa."""
        try:
            devnull = open(os.devnull)
            subprocess.check_output(["pacmd", "list-sink-inputs"], stderr=devnull)
            self.mutemethod = self.pulsesink_mute
            log.debug("Mute method is pulse sink.")
        except (OSError, subprocess.CalledProcessError):
            log.debug("Mute method is alsa or pulse without sinks.")
            log.info("No pulse sinks found, falling back to system mute via alsa/pulse.")
            self.mutemethod = self.alsa_mute


    def install_locale(self):
        import locale
        import gettext

        current_locale, encoding = locale.getdefaultlocale()
        pulseaudio_domain = 'pulseaudio'
        localedir = gettext.find(pulseaudio_domain, languages=[current_locale])
        localedir = localedir[:localedir.find('locale/')] + 'locale'
        locale = gettext.translation(pulseaudio_domain, localedir=localedir, languages=[current_locale])
        locale.install()


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
            return True
        except subprocess.CalledProcessError:
            return False


    def start_spotify(self):
        if util.CONFIG["general"]["start_spotify"]:
            log.info("Starting Spotify ...")
            null = open('/dev/null', 'w')
            subprocess.Popen(['/usr/bin/spotify'], stdout=null, stderr=null)  # .pid
            for _ in range(20):
                time.sleep(1)
                spotify_is_running = self.check_for_spotify_process()
                if spotify_is_running:
                    log.info("Spotify launched!")
                    break

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
        # Force unmute to properly initialize unmuted state
        self.toggle_mute()

        gtk.timeout_add(self.update_interval, self.update)
        # Delay autoplayback until self.spotify_is_playing was called at least once.
        gtk.timeout_add(self.update_interval + 100, self.start_autoplay)

        log.info("Blockify started.")

        gtk.main()


    def start_autoplay(self):
        if self.autoplay:
            log.debug("Autoplay is activated.")
            log.info("Starting Spotify autoplayback.")
            self.dbus.play()
        return False


    def adjust_interlude(self):
        if self.use_interlude_music:
            self.player.toggle_music()


    def spotify_is_playing(self):
        return self.song_status == "Playing"


    def update(self):
        "Main update routine, looped every self.update_interval milliseconds."
        # Determine if a commercial is running and act accordingly.
        self.found = self.find_ad()

        self.adjust_interlude()

        # Always return True to keep looping this method.
        return True


    def find_ad(self):
        "Main loop. Checks for ads and mutes accordingly."
        self.previous_song = self.current_song
        self.current_song = self.get_current_song()
        # self.song_status = self.dbus.get_song_status()

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

        if self.blocklist.find(self.current_song):
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
            dbus_song = self.dbus.get_song_artist() + self.song_delimiter + self.dbus.get_song_title()
            is_ad = self.current_song != dbus_song
            return is_ad
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

    def find_spotify_window_wmctrl(self):
        spotify_window = []
        try:
            pipe = subprocess.Popen(['wmctrl', '-lx'], stdout=subprocess.PIPE).stdout
            window_list = pipe.read().split("\n")
            for window in window_list:
                if (window.find("spotify.Spotify") >= 0):
                    # current_song = " ".join(window.split()[5:])
                    spotify_window.append(window)
                    break

        except OSError:
            print "wmctrl needs to be installed"
            sys.exit(1)

        return spotify_window


    def find_spotify_window(self):
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
        song = ""
        spotify_window = self.find_spotify_window_wmctrl()

        if spotify_window:
            try:
                song = " ".join(spotify_window[0].split()[4:]).decode("utf-8")
            except Exception as e:
                log.debug("Could not match spotify pid to sink pid: %s", e, exc_info=1)

        return song


    def block_current(self):
        if self.current_song:
            self.blocklist.append(self.current_song)


    def unblock_current(self):
        if self.current_song:
            if self.use_interlude_music:
                self.player.pause()
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


    def extract_pulse_sink_status(self, pacmd_out):
        sink_status = ("", "")
        # Match muted_value and application.process.id values.
        pattern = re.compile(r"(?: index|muted|application\.process\.id).*?(\w+)")
        # Put valid spotify PIDs in a list
        output = pacmd_out.decode("utf-8")

        spotify_sink_list = [" index: " + i for i in output.split("index: ") if "spotify" in i]

        if len(spotify_sink_list) and self.spotify_pids:
            sink_infos = [pattern.findall(sink) for sink in spotify_sink_list]
            # Every third element per sublist is a key, the value is the preceding
            # two elements in the form of a tuple - {pid : (index, muted_value)}
            idxd = {sink_status[2]: (sink_status[0], sink_status[1]) for sink_status in sink_infos if len(sink_status) == 3}

            while True:
                try:
                    pid = [k for k in idxd.keys() if k in self.spotify_pids][0]
                    break
                except IndexError:
                    self.check_for_spotify_process()
            sink_status = idxd[pid]  # tuple of 2 elements: (index, muted_value)

        return sink_status


    def pulsesink_mute(self, mode):
        "Finds spotify's audio sink and toggles its mute state."
        try:
            pacmd_out = subprocess.check_output(["pacmd", "list-sink-inputs"])
        except subprocess.CalledProcessError:
            log.error("Spotify sink not found. Is Pulse running? Resorting to pulse amixer as mute method.")
            self.mutemethod = self.pulse_mute  # Fall back to amixer mute.
            self.use_interlude_music = False
            return

        index, muted_value = self.extract_pulse_sink_status(pacmd_out)

        self.is_sink_muted = False if muted_value == self.pulse_unmuted_value else True

        if index:
            if self.is_sink_muted and (mode == 2 or not self.current_song):
                log.info("Forcing unmute.")
                subprocess.call(["pacmd", "set-sink-input-mute", index, "0"])
            elif not self.is_sink_muted and mode == 1:
                log.info("Muting {}.".format(self.current_song))
                subprocess.call(["pacmd", "set-sink-input-mute", index, "1"])
            elif self.is_sink_muted and not mode:
                log.info("Unmuting.")
                subprocess.call(["pacmd", "set-sink-input-mute", index, "0"])


    def prev(self):
        self.dbus.prev()
        self.player.try_resume_spotify_playback()


    def next(self):
        self.dbus.next()
        self.player.try_resume_spotify_playback()


    def signal_stop_received(self, sig, hdl):
        log.debug("{} received. Exiting safely.".format(sig))
        self.stop()


    def signal_block_received(self, sig, hdl):
        log.debug("Signal {} received. Blocking current song.".format(sig))
        self.block_current()


    def signal_unblock_received(self, sig, hdl):
        log.debug("Signal {} received. Unblocking current song.".format(sig))
        self.unblock_current()


    def signal_prev_received(self, sig, hdl):
        log.debug("Signal {} received. Playing previous interlude.".format(sig))
        self.prev()


    def signal_next_received(self, sig, hdl):
        log.debug("Signal {} received. Playing next song.".format(sig))
        self.next()


    def signal_playpause_received(self, sig, hdl):
        log.debug("Signal {} received. Toggling play state.".format(sig))
        self.dbus.playpause()


    def signal_toggle_block_received(self, sig, hdl):
        log.debug("Signal {} received. Toggling blocked state.".format(sig))
        self.toggle_block()


    def signal_prev_interlude_received(self, sig, hdl):
        log.debug("Signal {} received. Playing previous interlude.".format(sig))
        self.player.prev()


    def signal_next_interlude_received(self, sig, hdl):
        log.debug("Signal {} received. Playing next interlude.".format(sig))
        self.player.next()


    def signal_playpause_interlude_received(self, sig, hdl):
        log.debug("Signal {} received. Toggling interlude play state.".format(sig))
        self.player.playpause()


    def signal_toggle_autoresume_received(self, sig, hdl):
        log.debug("Signal {} received. Toggling autoresume.".format(sig))
        self.player.toggle_autoresume()


    def bind_signals(self):
        "Catch signals because it seems like a great idea, right? ... Right?"
        signal.signal(signal.SIGINT, self.signal_stop_received)  # 9
        signal.signal(signal.SIGTERM, self.signal_stop_received)  # 15

        signal.signal(signal.SIGUSR1, self.signal_block_received)  # 10
        signal.signal(signal.SIGUSR2, self.signal_unblock_received)  # 12

        signal.signal(signal.SIGRTMIN, self.signal_prev_received)  # 34
        signal.signal(signal.SIGRTMIN + 1, self.signal_next_received)  # 35
        signal.signal(signal.SIGRTMIN + 2, self.signal_playpause_received)  # 35
        signal.signal(signal.SIGRTMIN + 3, self.signal_toggle_block_received)  # 37

        signal.signal(signal.SIGRTMIN + 10, self.signal_prev_interlude_received)  # 44
        signal.signal(signal.SIGRTMIN + 11, self.signal_next_interlude_received)  # 45
        signal.signal(signal.SIGRTMIN + 12, self.signal_playpause_interlude_received)  # 46
        signal.signal(signal.SIGRTMIN + 13, self.signal_toggle_autoresume_received)  # 47


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


    def toggle_block(self):
        "Block/unblock the current song."
        if self.found:
            self.unblock_current()
        else:
            self.block_current()
            if self.use_interlude_music:
                self.player.manual_control = False


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
    util.initialize(doc)

    blockify = Blockify(blocklist.Blocklist())

    return blockify


def main():
    "Entry point for the CLI-version of Blockify."
    blockify = initialize()
    blockify.start()


if __name__ == "__main__":
    main()
