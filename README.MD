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
