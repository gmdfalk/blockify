import ConfigParser
import codecs
import logging
import os
import sys


log = logging.getLogger("util")
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config/blockify")
CONFIG_FILE = os.path.join(CONFIG_DIR, "blockify.ini")
BLOCKLIST_FILE = os.path.join(CONFIG_DIR, "blocklist.txt")
PLAYLIST_FILE = os.path.join(CONFIG_DIR, "playlist.m3u")
THUMBNAIL_DIR = os.path.join(CONFIG_DIR, "thumbnails")


def init_logger(logpath=None, loglevel=0, quiet=False):
    "Initializes the logging module."
    logger = logging.getLogger()

    # Cap loglevel at 3 to avoid index errors.
    if loglevel > 3:
        loglevel = 3
    # Apply loglevel.
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logger.setLevel(levels[loglevel])

    logformat = "%(asctime)-14s %(levelname)-8s %(name)-8s %(message)s"

    formatter = logging.Formatter(logformat, "%Y-%m-%d %H:%M:%S")

    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log.debug("Added logging console handler.")
        log.info("Loglevel is {} (10=DEBUG, 20=INFO, 30=WARN).".format(levels[loglevel]))
    if logpath:
        try:
            logfile = os.path.abspath(logpath)
            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            log.debug("Added logging file handler: {}.".format(logfile))
        except IOError:
            log.error("Could not attach file handler.")

def rename_file(fname):
    if not os.path.isfile(fname):
        try:
            os.rename(fname[:-4], fname)
        except OSError:
            pass


def init_config_dir():
    "Determine if a config dir for blockify exists and if not, create it."
    if not os.path.isdir(CONFIG_DIR):
        log.info("Creating config directory.")
        os.makedirs(CONFIG_DIR)

    if not os.path.isdir(THUMBNAIL_DIR):
        log.info("Creating thumbnail directory.")
        os.makedirs(THUMBNAIL_DIR)

    # During transition from v1.6 to v1.7, rename the playlist and blocklist files.
    rename_file(PLAYLIST_FILE)
    rename_file(BLOCKLIST_FILE)

    if not os.path.isfile(CONFIG_FILE):
        save_options(CONFIG_DIR, get_default_options())


def get_default_options():
    options = {
        "general": {
            "autodetect": True,
            "automute": True
        },
        "cli": {
            "update_interval": 200,
            "unmute_delay": 700
        },
        "gui": {
            "update_interval": 350,
            "use_cover_art": True,
            "autohide_cover": False
        },
        "interlude": {
            "use_interlude_music": True,
            "playlist": PLAYLIST_FILE,
            "autoresume": False,
            "radio_timeout": 180,
            "playback_delay": 500
        }
    }

    return options


def load_options():
    options = {}
    config = ConfigParser.ConfigParser()
    try:
        config.read(CONFIG_FILE)

        options["general"] = {
            "autodetect":config.getboolean("general", "autodetect"),
            "automute":config.getboolean("general", "automute")
        }
        options["cli"] = {
            "update_interval":config.getint("cli", "update_interval"),
            "unmute_delay":config.getint("cli", "unmute_delay")
        }
        options["gui"] = {
            "use_cover_art":config.getboolean("gui", "use_cover_art"),
            "autohide_cover":config.getboolean("gui", "autohide_cover"),
            "update_interval":config.getint("gui", "update_interval"),
        }
        options["interlude"] = {
            "use_interlude_music":config.getboolean("interlude", "use_interlude_music"),
            "autoresume":config.getboolean("interlude", "autoresume"),
            "radio_timeout":config.getint("interlude", "radio_timeout"),
            "playback_delay":config.getint("interlude", "playback_delay"),
            "playlist":config.get("interlude", "playlist")
        }
        if not options["interlude"]["playlist"]:
            options["interlude"]["playlist"] = PLAYLIST_FILE
    except Exception as e:
        log.error("Could not read config file: {}. Merging with default options.".format(e))
        # Merge with default options to make sure we have everything we need.
        defoptions = get_default_options()
        options = dict(defoptions.items() + options.items())
    else:
        log.info("Configuration file loaded from {}.".format(CONFIG_FILE))

    return options


def save_options(CONFIG_DIR, options):
    configfile = os.path.join(CONFIG_DIR, CONFIG_FILE)
    config = ConfigParser.ConfigParser()
    # Write out the sections in this order.
    sections = ["general", "cli", "gui", "interlude"]
    for section in sections:
        config.add_section(section)
        for k, v in options[section].items():
            config.set(section, k, v)

    with codecs.open(configfile, "w", encoding="utf-8") as f:
        config.write(f)

    log.info("Configuration file written to {}.".format(configfile))
