import ConfigParser
import codecs
import logging
import os
import sys

log = logging.getLogger("util")

try:
    from docopt import docopt
except ImportError:
    log.error("ImportError: Please install docopt to use the CLI.")

VERSION = "1.8.2"
CONFIG = None
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
            "automute": True,
            "substring_search": False
            # "pacmd_muted_value":"yes"
        },
        "cli": {
            "update_interval": 200,
            "unmute_delay": 700
        },
        "gui": {
            "update_interval": 350,
            "unmute_delay": 650,
            "use_cover_art": True,
            "autohide_cover": False
        },
        "interlude": {
            "use_interlude_music": True,
            "start_shuffled": False,
            "autoresume": False,
            "playlist": PLAYLIST_FILE,
            "radio_timeout": 180,
            "playback_delay": 500
        }
    }

    return options


def load_options():
    log.info("Loading configuration.")
    options = get_default_options()
    config = ConfigParser.ConfigParser()
    try:
        config.read(CONFIG_FILE)
    except Exception as e:
        log.error("Could not read config file: {}. Using default options.".format(e))
    else:
        option_tuples = [("general", "autodetect", "bool"), ("general", "automute", "bool"), ("general", "substring_search", "bool"),
          ("cli", "update_interval", "int"), ("cli", "unmute_delay", "int"),
          ("gui", "use_cover_art", "bool"), ("gui", "autohide_cover", "bool"), ("gui", "update_interval", "int"), ("gui", "unmute_delay", "int"),
          ("interlude", "use_interlude_music", "bool"), ("interlude", "start_shuffled", "bool"), ("interlude", "autoresume", "bool"),
          ("interlude", "radio_timeout", "int"), ("interlude", "playback_delay", "int"), ("interlude", "playlist", "str")
          ]
        for option_tuple in option_tuples:
            load_option(config, options, option_tuple)
        if not options["interlude"]["playlist"]:
            options["interlude"]["playlist"] = PLAYLIST_FILE
        log.info("Configuration file loaded from {}.".format(CONFIG_FILE))

    return options


def load_option(config, options, option_tuple):
    section_name, option_name, option_type = option_tuple[0], option_tuple[1], option_tuple[2]
    try:
        option = None
        if (option_type == "bool"):
            option = config.getboolean(section_name, option_name)
        elif (option_type == "int"):
            option = config.getint(section_name, option_name)
        else:
            option = config.get(section_name, option_name)
        options[section_name][option_name] = option
    except Exception:
        log.error("Could not parse option %s for section %s. Using default value.", option_name, section_name)


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


def initialize(doc):
    try:
        args = docopt(doc, version=VERSION)
        init_logger(args["--log"], args["-v"], args["--quiet"])
    except NameError:
        init_logger()

    global CONFIG
    CONFIG = load_options()

    # Set up the configuration directory & files, if necessary.
    init_config_dir()