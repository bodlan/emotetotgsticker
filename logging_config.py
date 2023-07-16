import logging.config

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y/%m/%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "run.log",
            "mode": "w",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "WARNING", "propagate": False},  # root logger
        "run": {"handlers": ["file"], "level": "DEBUG", "propagate": False},
        "__main__": {"handlers": ["file"], "level": "DEBUG", "propagate": False},  # if __name__ == '__main__'
    },
}
logging.config.dictConfig(LOGGING)
