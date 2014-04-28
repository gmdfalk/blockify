#!/usr/bin/env python2
"""blockify

Usage:
    blockify [-l <path>] [-v...] [-q] [-h]

Options:
    -l, --logfile=<path>  Enables logging to the logfile/-path specified.
    -q, --quiet           Don't print anything to stdout.
    -v                    Set the log verbosity, up to -vvv.
"""
import logging
import os
import re
import signal
import subprocess
import sys
import time

from docopt import docopt

import spotifydbus


log = logging.getLogger("main")
# automute, if muted, return


class Blockify(object):

    def __init__(self, spotify):
        self.spotify = spotify
        self.channels = self.get_channels()
        log.info("Blockify started.")


    def update(self):
        self.spotify.prev()

        now = int(time.time())
        title = self.spotify.get_song_title()
        length = self.spotify.get_song_length()
        end_time = now + length

        while self.spotify.is_running():
            now = int(time.time())
            cur_title = self.spotify.get_song_title()

            if cur_title != title:
                print("CHANGED: Song ends in", self.spotify.get_song_length(), "seconds")
                length = self.spotify.get_song_length()
                end_time = now + length
                title = cur_title

            status = str(self.spotify.get_property('PlaybackStatus'))

            if status == 'Paused':
                print("PAUSED: Song ends in", end_time - now, "seconds")
                while status == 'Paused':
                    time.sleep(1)
                    end_time += 1
                    status = str(self.spotify.get_property('PlaybackStatus'))
                print("PLAYING")

            if now > end_time and cur_title == title:
                print("MUTING")
                self.toggle_mute(True)
                while cur_title == title:
                    cur_title = self.spotify.get_song_title()
                    time.sleep(0.5)
                print("UNUTING")
                self.toggle_mute()

            time.sleep(1)


    def get_channels(self):
        channel_list = ["Master"]
        amixer_output = subprocess.check_output("amixer")
        if "'Speaker',0" in amixer_output:
            channel_list.append("Speaker")

        return channel_list


    def toggle_mute(self, force=False, automute=True):
        # TODO: Determine mute type here.
        soundcontrol = "alsa"
        mutemethod = getattr(self, soundcontrol + "_mute", None)

        if mutemethod is not None:
            log.debug("Calling mutemethod: {}".format(mutemethod))
            mutemethod(force, automute)


    def alsa_mute(self, force=False, automute=True):
        if automute:
            if force:
                state = "mute"
                log.info("Muting {} - {}.".format(self.spotify.get_song_artist(),
                                             self.spotify.get_song_title()))
            else:
                state = "unmute"
                log.info("Unmuting.")

            for channel in self.channels:
                subprocess.Popen(["amixer", "-q", "set", channel, state])


    def alsa_muted(self):
        "Check if system sound is muted."
        master = subprocess.check_output(["amixer", "get", "Master"])
        if "[off]" in master:
            return True
        return False


    def pulse_mute(self, force=False, automute=True):
        "Finds spotify's audio sink and toggles its mute state."

        pacmd_out = subprocess.check_output(["pacmd", "list-sink-inputs"])
        pidof_out = subprocess.check_output(["pidof", "spotify"])

        pattern = re.compile(r'(?: index|muted|application\.process\.id).*?(\w+)')
        pids = pidof_out.decode('utf-8').strip().split(' ')
        output = pacmd_out.decode('utf-8')

        # Every third element is a key, the value is the preceding two
        # elements in the form of a tuple - {pid : (index, muted)}
        info = pattern.findall(output)
        idxd = {info[3 * n + 2] : (info[3 * n], info[3 * n + 1])
                for n in range(0, len(info) // 3)}

        pid = [k for k in idxd.keys() if k in pids][0]
        index, muted = idxd[pid]

        if muted == 'no' or force:
            subprocess.call(["pacmd", "set-sink-input-mute", index, '1'])
        else:
            subprocess.call(["pacmd", "set-sink-input-mute", index, '0'])


    def bind_signals(self):
        "Traps SIGTERM and SIGINT for some cleanup in shutdown()."
        signal.signal(signal.SIGTERM, lambda sig, hdl: self.shutdown())
        signal.signal(signal.SIGINT, lambda sig, hdl: self.shutdown())


    def shutdown(self):
        "Safely shut down blockify by unmuting first."
        self.toggle_mute()
        sys.exit()


def init_logger(logpath=None, loglevel=1, quiet=False):
    "Initializes the logger for system messages."
    logger = logging.getLogger()

    # Set the loglevel.
    if loglevel > 3:
        loglevel = 3  # Cap at 3, incase someone likes their v-key too much.
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logger.setLevel(levels[loglevel])

    logformat = "%(asctime)-14s %(levelname)-8s %(name)-8s %(message)s"

    formatter = logging.Formatter(logformat, "%Y-%m-%d %H:%M:%S")

    # Only attach a console handler if both nologs and quiet are disabled.
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log.debug("Added logging console handler.")
        log.info("Loglevel is {}.".format(levels[loglevel]))
    if logpath:
        try:
            logfile = os.path.abspath(logpath)
            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            log.debug("Added logging file handler: {}.".format(logfile))
        except IOError:
            log.error("Could not attach file handler.")


def main():
    spotify = spotifydbus.SpotifyDBus()
    blockify = Blockify(spotify)

    blockify.bind_signals()
    blockify.toggle_mute()

    while True:
        blockify.update()


def cli_entry():
    args = docopt(__doc__, version="0.8")
    init_logger(args["--logfile"], args["-v"], args["--quiet"])
    main()


if __name__ == "__main__":
    cli_entry()
