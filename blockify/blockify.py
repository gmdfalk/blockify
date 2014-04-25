"""blockify

Usage:
    blockify [-l <dir>] [-q] [-v...] [-h]

Options:
    -l, --logdir=<dir>  Will enable file logging to dir/blockify.log.
    -q, --quiet         Don't anything to stdout.
    -v                  Log verbosity.
"""
# TODO: pacmd option (complementing alsa/amixer).
from codecs import open
from os import path
from subprocess import check_output, Popen
import logging
import signal
import sys
import time

from docopt import docopt
import gtk
import pygtk
import wnck


pygtk.require("2.0")


class Blocklist(list):

    def __init__(self):
        self.home = path.expanduser("~")
        self.location = path.join(self.home, ".blockify_list")
        self.timestamp = self.get_timestamp()

    def append(self, item):
        "Overloading list.append to automatically save the list to a file."
        # Only allow nonempty strings.
        if not item or not isinstance(item, str):
            return
        log.info("Adding {} to {}.".format(item, self.location))
        super(Blocklist, self).append(item)
        self.save_file()

    def get_timestamp(self):
        return path.getmtime(self.location)

    def load_file(self):
        log.info("Loading {}.".format(self.location))
        try:
            with open(self.location, "r", encoding="utf-8") as f:
                blocklist = f.read()
        except IOError:
            with open(self.location, "w+", encoding="utf-8") as f:
                blocklist = f.read()

        return [i for i in blocklist.split("\n") if i]

    def save_file(self):
        log.info("Saving blocklist to {}.".format(self.location))
        with open(self.location, "w", encoding="utf-8") as f:
            f.writelines([i + "\n" for i in self])
        self.timestamp = self.get_timestamp()

    def check_file(self):
        # Reload blockfile if it changed.
        current_timestamp = self.get_timestamp()
        if self.timestamp != current_timestamp:
            log.info("Blockfile changed. Reloading.")
            self.load_file()
            self.timestamp = current_timestamp


class Blockify(object):

    def __init__(self, blocklist):
        self.blocklist = blocklist
        self.channels = self.get_channels()
        self.song = self.get_current_song()
        log.info("Blockify started.")

    def get_windows(self):
        "Libwnck list of currently open windows."
        # Get the current screen.
        screen = wnck.screen_get_default()

        while gtk.events_pending():
            gtk.main_iteration(False)

        # Object list of windows in screen.
        windows = screen.get_windows()
        # Return the actual list of windows or an empty list.
        return [win.get_icon_name() for win in windows if len(windows)]

    def get_current_song(self):
        "Checks if a Spotify window exists and returns the current songname."
        pipe = self.get_windows()
        for line in pipe:
            if line.find("Spotify - ") >= 0:
                # Remove "Spotify - " and return the rest of the songname.
                return " ".join(line.split()[2:])

        # No song playing, so return an empty string.
        return ""

    def block_current(self):
        current_song = self.get_current_song()

        if current_song:
            self.blocklist.append(current_song)

    def get_channels(self):
        channel_list = ["Master"]
        amixer_output = check_output("amixer")
        if "'Speaker',0" in amixer_output:
            channel_list.append("Speaker")

        return channel_list

    def toggle_mute(self, mute=False):
        if mute:
            state = "mute"
            log.info("Muting {}.".format(self.get_current_song()))
        else:
            state = "unmute"
            log.info("Unmuting")

        for channel in self.channels:
            Popen(["amixer", "-q", "set", channel, state])

    def sound_muted(self):
        "Check if system sound is muted."
        master = check_output("amixer get Master | grep -o off", shell=True)
        if "off" in master:
            return True
        return False

    def bind_signals(self):
        signal.signal(signal.SIGUSR1, lambda sig, hdl: self.block_current())
        signal.signal(signal.SIGTERM, lambda sig, hdl: self.trap_exit())
        signal.signal(signal.SIGINT, lambda sig, hdl: self.trap_exit())

    def trap_exit(self):
        self.blocklist.save()
        self.unmute()
        sys.exit()


def init_logger(logdir, loglevel, quiet):
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
    if not args["--quiet"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log.debug("Added logging console handler.")
        log.info("Loglevel is {}.".format(levels[loglevel]))
    if logdir:
        try:
            logfile = path.join(logdir, "blockify.log")
            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            log.debug("Added logging file handler.")
        except IOError:
            log.error("Could not attach file handler.")


def main():
    blocklist = Blocklist()
    blockify = Blockify(blocklist)

    blockify.bind_signals()
    blockify.toggle_mute()

    # Start the main loop.
    while True:
        blocklist.check_blocklist()

        time.sleep(1)


if __name__ == "__main__":
    args = docopt(__doc__, version="0.7")
    init_logger(args["--logdir"], args["-v"], args["--quiet"])
    log = logging.getLogger("blockify")
    main()
