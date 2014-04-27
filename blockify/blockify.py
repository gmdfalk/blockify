"""blockify

Usage:
    blockify [-l <path>] [-v...] [-q] [-h]

Options:
    -l, --logfile=<path>  Enables logging to the logfile/-path specified.
    -q, --quiet           Don't print anything to stdout.
    -v                    Set the log verbosity, up to -vvv.
"""
# TODO: pacmd mute/cli option (complementing alsa/amixer).
from subprocess import check_output, Popen
import codecs
import logging
import os
import signal
import sys
import time

from docopt import docopt
import gtk
import pygtk
import wnck


pygtk.require("2.0")
log = logging.getLogger()


class Blocklist(list):
    "Inheriting from list type is a bad idea. Lets see what happens."
    def __init__(self):
        list.__init__(self)
        self.home = os.path.expanduser("~")
        self.location = os.path.join(self.home, ".blockify_list")
        self.timestamp = self.get_timestamp()
        self.extend(self.load_file())

    def append(self, item):
        "Overloading list.append to automatically save the list to a file."
        # Only allow nonempty strings.
        if not isinstance(item, str) or not item:
            log.debug("Failed to add {} to blocklist.".format(item))
            return
        log.info("Adding {} to {}.".format(item, self.location))
        super(Blocklist, self).append(item)
        self.save_file()

    def get_timestamp(self):
        return os.path.getmtime(self.location)

    def load_file(self):
        log.info("Loading blockfile from {}.".format(self.location))
        try:
            with codecs.open(self.location, "r", encoding="utf-8") as f:
                blocklist = f.read()
        except IOError:
            with codecs.open(self.location, "w+", encoding="utf-8") as f:
                blocklist = f.read()

        return [i for i in blocklist.split("\n") if i]

    def save_file(self):
        log.info("Saving blocklist to {}.".format(self.location))
        with codecs.open(self.location, "w", encoding="utf-8") as f:
            f.write("\n".join(self) + "\n")
        self.timestamp = self.get_timestamp()


class Blockify(object):

    def __init__(self, blocklist):
        self.blocklist = blocklist
        self.channels = self.get_channels()
        log.info("Blockify started.")

    def update(self):
        current_song = self.get_current_song()

        if current_song == "":
            return

        # Check if the blockfile has changed.
        current_timestamp = self.blocklist.get_timestamp()
        if self.blocklist.timestamp != current_timestamp:
            log.info("Blockfile changed. Reloading.")
            self.blocklist.__init__()

        muted = self.sound_muted()

        if current_song in self.blocklist:
            if not muted:
                self.toggle_mute(True)
        else:
            if muted:
                self.toggle_mute()

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
            log.info("Unmuting.")

        for channel in self.channels:
            Popen(["amixer", "-q", "set", channel, state])

    def sound_muted(self):
        "Check if system sound is muted."
        master = check_output(["amixer", "get", "Master"])
        if "[off]" in master:
            return True
        return False

    def bind_signals(self):
        signal.signal(signal.SIGUSR1, lambda sig, hdl: self.block_current())
        signal.signal(signal.SIGTERM, lambda sig, hdl: self.shutdown())
        signal.signal(signal.SIGINT, lambda sig, hdl: self.shutdown())

    def shutdown(self):
        self.blocklist.save_file()
        self.toggle_mute()
        sys.exit()


def init_logger(logpath, loglevel, quiet):
    "Initializes the logger for system messages."
    logger = logging.getLogger()

    # Set the loglevel.
    if loglevel > 3:
        loglevel = 3  # Cap at 3, incase someone likes their v-key too much.
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logger.setLevel(levels[loglevel])

    logformat = "%(asctime)-14s %(levelname)-8s %(message)s"

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
    blocklist = Blocklist()
    blockify = Blockify(blocklist)

    blockify.bind_signals()
    blockify.toggle_mute()

    while True:
        blockify.update()
        time.sleep(1)


def cli_entry():
    args = docopt(__doc__, version="0.7")
    init_logger(args["--logfile"], args["-v"], args["--quiet"])
    main()


if __name__ == "__main__":
    cli_entry()
