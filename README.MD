![Python version](https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8%20|%203.9%20|%203.10|%203.11|%203.12|%203.13-blue)
![PyPI version](https://img.shields.io/pypi/v/cullinan.svg?style=flat&logo=pypi&color=green)
![PyPI downloads](https://img.shields.io/pypi/dm/cullinan.svg?style=flat&logo=pypi&color=blue)
![GitHub stars](https://img.shields.io/github/stars/plumeink/cullinan.svg?style=flat&logo=github&color=white)
![License](https://img.shields.io/github/license/plumeink/cullinan.svg?style=flat&color=white)
```                                              
   _____      _ _ _                      
  / ____|    | | (_)                     
 | |    _   _| | |_ _ __   __ _ _ __     
 | |   | | | | | | | '_ \ / _` | '_ \    
 | |___| |_| | | | | | | | (_| | | | |   
 \_____\__, _|_|_|_|_| |_|\__,_|_| |_|  
```
# Cullinan

Cullinan is written based on tornado and Sqlalchemy to help the project quickly build web application

## How to use
    
#### install
     
    pip install cullinan
    
---
#### demo

File controller:
```python
from cullinan.controller import controller, get_api

@controller()
class TestController:
    
    @get_api(uri='/get', query_params=['id', 'name'])
    def get(self, query_params):
        return self.service['TestService'].test(query_params['id'], query_params['name'])
```

File service:
```python
from cullinan.service import Service, service

@service
class TestService(Service):
    def test(self, id, name):
        self.response.set_body({ 'id': id, 'name': name })
        return self.response
```

File application:
```python
from cullinan import application

def main():
    application.run()

if __name__ == '__main__':
    main()
```
Now, A web application demo is completed!

---
#### File structure:
```
project
   |----application.py                               # Web Application main entrance
   |----controller                                   # Controller package
   |  |----TestController.py                            
   |----service                                      # Service package
   |  |----TestService.py                               
```

## Wiki

wiki and other related references: https://github.com/plumeink/Cullinan/wiki

## Maintainer

[<img src="https://avatars.githubusercontent.com/u/104434649?v=4" width = "40" height = "40"/>](https://github.com/plumeink)

## Logging

Cullinan does not configure logging handlers by itself. The framework modules use standard Python loggers (module-level `logging.getLogger(__name__)`) and the package installs a `NullHandler` to avoid noisy "No handlers could be found" warnings when the package is imported.

As an application developer you should configure logging at your program entry point. Below are two common patterns you can copy into your `app.py` (or equivalent) to direct framework logs to the console only.

### Console-only (recommended)

This example configures a single console handler for the framework and the application. It will not write any files; file handlers can be added by you if desired.

```python
# app.py - application entry
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
        # control all framework logging from the package root
        "cullinan": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

config.dictConfig(LOGGING)

# then start the framework
from cullinan import application
application.run()
```

### Per-module / fine-grained control

Because modules use module-level loggers (`logging.getLogger(__name__)`), you can control logging per-module. Example: only enable debug for controller code while keeping other parts at INFO.

```python
LOGGING['loggers'].update({
    'cullinan.controller': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    'cullinan.request': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
})

config.dictConfig(LOGGING)
```

Notes
- The library will not create files or configure handlers for you. This keeps the library side-effect free and lets each application decide how to handle logs (console, files, remote logging, etc.).
- If you want the simplest possible behavior (prints to console), the `Console-only` example is all you need.

## Access logs

Cullinan emits access logs for each HTTP request. The framework provides a configurable access log emitter and a dedicated logger name `cullinan.access` so applications can route or filter access logs separately from other framework logs.

Configuration
- Format: control the access log format with the environment variable `CULLINAN_ACCESS_LOG_FORMAT`:
  - `combined` (default): Apache combined-like single-line log
  - `json`: structured JSON object (useful for log aggregation)

- Example env usage:
  - `CULLINAN_ACCESS_LOG_FORMAT=combined`
  - `CULLINAN_ACCESS_LOG_FORMAT=json`

- Handler: access logs are emitted via logger `cullinan.access`. Configure logging in your application entry point to route access logs to console or files. Example (console-only):

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
        # route framework logs
        "cullinan": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # route access logs separately if desired
        "cullinan.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

config.dictConfig(LOGGING)

from cullinan import application
application.run()
```

Debug / development convenience
- If you start the process in an environment where the framework can't detect a direct `__main__` (for example some IDE run configurations), the framework won't auto-install a console handler by default. For quick development you can force console logging with:

- `CULLINAN_FORCE_CONSOLE=1` and optionally set `CULLINAN_AUTO_CONSOLE_LEVEL=INFO` (or DEBUG) to control the temporary console handler level.

Examples
- Combined format (default):
```
127.0.0.1 - - [05/Nov/2025:01:10:23] "GET /path HTTP/1.1" 200 123 "-" "curl/7.XX" 0.123
```
- JSON format (set `CULLINAN_ACCESS_LOG_FORMAT=json`):
```
{"remote_addr":"127.0.0.1","method":"GET","path":"/path","status_code":200,"duration":0.123,"content_length":123,"referer":"-","user_agent":"curl/7.XX"}
```
