import logging
import os
import sys


log = logging.getLogger("util")


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


def get_configdir():
    "Determine if an XDG_CONFIG_DIR for blockify exists and if not, create it."
    configdir = os.path.join(os.path.expanduser("~"), ".config/blockify")

    if not os.path.isdir(configdir):
        log.info("Creating config directory.")
        os.makedirs(configdir)

    thumbnaildir = os.path.join(configdir, "thumbnails")
    if not os.path.isdir(thumbnaildir):
        log.info("Creating thumbnail directory.")
        os.makedirs(thumbnaildir)

    return configdir
