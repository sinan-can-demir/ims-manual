import logging
import sys


def setup_logger():
    # create a logger for the inventory management system
    logger = logging.getLogger("ims")
    logger.setLevel(logging.INFO)

    # create a stream handler to output logs to stdout
    handler = logging.StreamHandler(sys.stdout)

    # define a log format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # set the formatter for the handler and add the handler to the logger
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)

    # return the configured
    return logger

logger = setup_logger()