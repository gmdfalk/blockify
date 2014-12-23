import logging
import os
import sys
import ConfigParser
import codecs


log = logging.getLogger("util")
CONFIG_FILE = "blockify.ini"
CONFIG_DIR = ".config/blockify"
THUMBNAIL_DIR = "thumbnails"


def init_logger(logpath=None, loglevel=2, quiet=False):
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


def init_configdir():
    "Determine if a config dir for blockify exists and if not, create it."
    configdir = os.path.join(os.path.expanduser("~"), CONFIG_DIR)
    thumbnaildir = os.path.join(configdir, THUMBNAIL_DIR)
    configfile = os.path.join(configdir, CONFIG_FILE)

    if not os.path.isdir(configdir):
        log.info("Creating config directory.")
        os.makedirs(configdir)

    if not os.path.isdir(thumbnaildir):
        log.info("Creating thumbnail directory.")
        os.makedirs(thumbnaildir)

    if not os.path.isfile(configfile):
        save_configfile(configdir, get_default_options())

    return configdir

def get_default_options():
    options = {
        "general": {
            "autodetect": True,
            "automute": True
        },
        "interlude": {
            "use_interlude_music": True,
            "playlist": "",
            "autoresume": True,
            "max_timeout": 600
        },
        "cli": {
            "update_interval": 0.25
        },
        "gui": {
            "update_interval": 400,
            "use_cover_art": True,
            "autohide_cover": False
        }
    }

    return options


def load_configfile(configdir):
    config = ConfigParser.ConfigParser()
    filepath = os.path.join(configdir, CONFIG_FILE)
    config.read(filepath)

    options = {}
    try:
        options["general"] = { k:config.getboolean("general", k) for k, _ in config.items("general") }
        options["cli"] = { k:config.getfloat("cli", k) for k, _ in config.items("cli") }
        options["interlude"] = {
            "use_interlude_music":config.getboolean("interlude", "use_interlude_music"),
            "autoresume":config.getboolean("interlude", "autoresume"),
            "max_timeout":config.getint("interlude", "max_timeout"),
            "playlist":config.get("interlude", "playlist")
        }
        options["gui"] = {
            "use_cover_art":config.getboolean("gui", "use_cover_art"),
            "autohide_cover":config.getboolean("gui", "autohide_cover"),
            "update_interval":config.getint("gui", "update_interval"),
        }
    except Exception as e:
        log.error("Could not completely read config file: {}. Using fallback options.".format(e))
        options = get_default_options()
    else:
        log.info("Configuration file loaded from {}.".format(configdir))

    return options


def save_configfile(configdir, options):
    configfile = os.path.join(configdir, CONFIG_FILE)
    config = ConfigParser.ConfigParser()
    # Write out the sections in this order.
    sections = ["general", "interlude", "cli", "gui"]
    for section in sections:
        config.add_section(section)
        for k, v in options[section].items():
            config.set(section, k, v)

    with codecs.open(configfile, "w", encoding="utf-8") as f:
        config.write(f)

    log.info("Configuration file written to {}.".format(configfile))
