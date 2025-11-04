# Cullinan Wiki

## Author
[<img src="https://avatars.githubusercontent.com/u/104434649?v=4" width = "40" height = "40"/>](https://github.com/hansiondesu)  

Copyright©2023


# About Docs
## 1.About docs
This document is used to help developers use Cullinan

## 2.Assist
We can solve the problem for you about Cullinan
If you encounter problems, you can contact us in the following ways
* Internal testers report errors in the cullinan-feedback channel in IM
* Feedback in [Issues](https://github.com/orestu/Cullinan/issues), (select the corresponding tag to speed up our processing)

## 3.First
If you are starting to use Cullinan, please start with the following topics:
* Start：[install](https://github.com/orestu/Cullinan/wiki/Culinan-Wiki%EF%BC%9AInstall)
* Tutorial：[First Cullinan Web Application](https://github.com/orestu/Cullinan/wiki/Cullinan-Wiki%EF%BC%9AFirst-Cullinan-Web-Application)

## 4.Using Cullinan
To prepare you to actually start using Cullinan, we have:
* Practicing：[Code structure](https://github.com/orestu/Cullinan/wiki/Cullinan-Wiki%EF%BC%9ABuild-your-code)
* Run the code：[IDE/Terminal](https://github.com/orestu/Cullinan/wiki/Cullinan-Wiki%EF%BC%9ARun-the-code)

## 5.More Cullinan features
For more Cullinan features, we provide you with:
* Core feature：[application / ENV](https://github.com/orestu/Cullinan/wiki/Cullinan-Wiki%EF%BC%9AApplication) | [Method injection](https://github.com/orestu/Cullinan/wiki/Cullinan-Wiki%EF%BC%9AMethod-injection)
* DataBase：[SQL](https://github.com/orestu/Cullinan/wiki/Cullinan-Wiki%EF%BC%9Adatabase)

## Logging

Cullinan does not configure handlers; the framework modules use module-level loggers (`logging.getLogger(__name__)`) and the package installs a `NullHandler` so importing the library doesn't produce "No handlers" warnings.

To direct logs to the console only, configure logging in your application entry point. Example:

```python
# app.py
import logging
from logging import config
import sys

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "cullinan": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}

config.dictConfig(LOGGING)

from cullinan import application
application.run()
```

To enable debug only for controller module:

```python
LOGGING['loggers'].update({
    'cullinan.controller': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
})
config.dictConfig(LOGGING)
```
