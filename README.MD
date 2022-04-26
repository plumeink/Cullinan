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
        return self.TestService.test(query_params['id'], query_params['name'])
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

wiki and other related references: https://github.com/orestu/Cullinan/wiki

## Maintainer

[<img src="https://avatars.githubusercontent.com/u/104434649?v=4" width = "40" height = "40"/>](https://github.com/plumeink)
