# Complete Tutorial: Building a Todo API

In this tutorial, you'll build a complete RESTful API for a Todo application using Cullinan.

## What You'll Build

A Todo API with:
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Service layer for business logic
- ✅ In-memory database
- ✅ Dependency injection
- ✅ Proper error handling

## Prerequisites

- Python 3.8+
- Cullinan framework installed
- Basic Python knowledge

## Step 1: Project Setup

Create project structure:

```bash
mkdir todo-api
cd todo-api
mkdir controllers services models
touch app.py .env
touch controllers/__init__.py services/__init__.py models/__init__.py
```

Your structure:
```
todo-api/
├── app.py
├── .env
├── controllers/
│   ├── __init__.py
│   └── todo_controller.py
├── services/
│   ├── __init__.py
│   └── todo_service.py
└── models/
    ├── __init__.py
    └── todo.py
```

## Step 2: Define the Model

Create `models/todo.py`:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    """Todo item model"""
    id: int
    title: str
    completed: bool = False
    description: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'description': self.description
        }
```

## Step 3: Create the Service

Create `services/todo_service.py`:

```python
from cullinan.service import service, Service
from models.todo import Todo
from typing import List, Optional

@service
class TodoService(Service):
    """Todo business logic service"""
    
    def __init__(self):
        super().__init__()
        self._todos = {}
        self._next_id = 1
    
    def get_phase(self) -> int:
        """Start early to initialize data"""
        return -50
    
    def on_startup(self):
        """Initialize with sample data"""
        print("Initializing TodoService with sample data...")
        self.create_todo("Learn Cullinan", "Read the documentation")
        self.create_todo("Build an API", "Complete the tutorial")
    
    def get_all_todos(self) -> List[Todo]:
        """Get all todos"""
        return list(self._todos.values())
    
    def get_todo(self, todo_id: int) -> Optional[Todo]:
        """Get a specific todo by ID"""
        return self._todos.get(todo_id)
    
    def create_todo(self, title: str, description: str = None) -> Todo:
        """Create a new todo"""
        todo = Todo(
            id=self._next_id,
            title=title,
            description=description,
            completed=False
        )
        self._todos[todo.id] = todo
        self._next_id += 1
        return todo
    
    def update_todo(self, todo_id: int, title: str = None, 
                   description: str = None, completed: bool = None) -> Optional[Todo]:
        """Update an existing todo"""
        todo = self._todos.get(todo_id)
        if not todo:
            return None
        
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if completed is not None:
            todo.completed = completed
        
        return todo
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo"""
        if todo_id in self._todos:
            del self._todos[todo_id]
            return True
        return False
    
    def toggle_completed(self, todo_id: int) -> Optional[Todo]:
        """Toggle todo completed status"""
        todo = self._todos.get(todo_id)
        if todo:
            todo.completed = not todo.completed
        return todo
```

## Step 4: Create the Controller

Create `controllers/todo_controller.py`:

```python
from cullinan.controller import controller, get_api, post_api, put_api, delete_api
from cullinan.core import Inject

@controller(url='/api/todos')
class TodoController:
    """Todo API endpoints"""
    
    # Inject TodoService (no import needed!)
    todo_service: 'TodoService' = Inject()
    
    @get_api(url='')
    def list_todos(self, query_params):
        """GET /api/todos - List all todos"""
        todos = self.todo_service.get_all_todos()
        return {
            'success': True,
            'count': len(todos),
            'todos': [todo.to_dict() for todo in todos]
        }
    
    @get_api(url='/([0-9]+)')
    def get_todo(self, todo_id):
        """GET /api/todos/{id} - Get specific todo"""
        todo = self.todo_service.get_todo(int(todo_id))
        
        if not todo:
            return {
                'success': False,
                'error': 'Todo not found'
            }
        
        return {
            'success': True,
            'todo': todo.to_dict()
        }
    
    @post_api(url='')
    def create_todo(self, body_params):
        """POST /api/todos - Create new todo"""
        title = body_params.get('title')
        
        if not title:
            return {
                'success': False,
                'error': 'Title is required'
            }
        
        description = body_params.get('description')
        todo = self.todo_service.create_todo(title, description)
        
        return {
            'success': True,
            'message': 'Todo created',
            'todo': todo.to_dict()
        }
    
    @put_api(url='/([0-9]+)')
    def update_todo(self, todo_id, body_params):
        """PUT /api/todos/{id} - Update todo"""
        todo = self.todo_service.update_todo(
            int(todo_id),
            title=body_params.get('title'),
            description=body_params.get('description'),
            completed=body_params.get('completed')
        )
        
        if not todo:
            return {
                'success': False,
                'error': 'Todo not found'
            }
        
        return {
            'success': True,
            'message': 'Todo updated',
            'todo': todo.to_dict()
        }
    
    @post_api(url='/([0-9]+)/toggle')
    def toggle_todo(self, todo_id):
        """POST /api/todos/{id}/toggle - Toggle completed status"""
        todo = self.todo_service.toggle_completed(int(todo_id))
        
        if not todo:
            return {
                'success': False,
                'error': 'Todo not found'
            }
        
        return {
            'success': True,
            'message': 'Todo toggled',
            'todo': todo.to_dict()
        }
    
    @delete_api(url='/([0-9]+)')
    def delete_todo(self, todo_id):
        """DELETE /api/todos/{id} - Delete todo"""
        deleted = self.todo_service.delete_todo(int(todo_id))
        
        if not deleted:
            return {
                'success': False,
                'error': 'Todo not found'
            }
        
        return {
            'success': True,
            'message': 'Todo deleted'
        }
```

## Step 5: Create the Main Application

Create `app.py`:

```python
from cullinan import application

# Import controllers and services to register them
from controllers.todo_controller import TodoController
from services.todo_service import TodoService

if __name__ == '__main__':
    print("Starting Todo API...")
    print("API endpoints:")
    print("  GET    /api/todos        - List all todos")
    print("  GET    /api/todos/{id}   - Get specific todo")
    print("  POST   /api/todos        - Create new todo")
    print("  PUT    /api/todos/{id}   - Update todo")
    print("  DELETE /api/todos/{id}   - Delete todo")
    print("  POST   /api/todos/{id}/toggle - Toggle completed")
    print("\nServer starting on http://localhost:4080")
    
    application.run()
```

## Step 6: Configure Environment

Create `.env`:

```env
SERVER_PORT=4080
SERVER_THREAD=1
```

## Step 7: Run the Application

```bash
python app.py
```

You should see:

```
Starting Todo API...
API endpoints:
  GET    /api/todos        - List all todos
  ...
Server starting on http://localhost:4080
|||	server is starting
|||	port is 4080
```

## Step 8: Test the API

### List all todos

```bash
curl http://localhost:4080/api/todos
```

Response:
```json
{
  "success": true,
  "count": 2,
  "todos": [
    {
      "id": 1,
      "title": "Learn Cullinan",
      "completed": false,
      "description": "Read the documentation"
    },
    {
      "id": 2,
      "title": "Build an API",
      "completed": false,
      "description": "Complete the tutorial"
    }
  ]
}
```

### Create a new todo

```bash
curl -X POST http://localhost:4080/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test the API", "description": "Use curl to test"}'
```

### Get specific todo

```bash
curl http://localhost:4080/api/todos/1
```

### Update todo

```bash
curl -X PUT http://localhost:4080/api/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### Toggle completed

```bash
curl -X POST http://localhost:4080/api/todos/1/toggle
```

### Delete todo

```bash
curl -X DELETE http://localhost:4080/api/todos/1
```

## What You Learned

✅ **Project structure** - Organized code into controllers, services, and models  
✅ **Services** - Created business logic layer with `@service`  
✅ **Dependency Injection** - Used string annotations to inject services  
✅ **Lifecycle hooks** - Initialized data in `on_startup()`  
✅ **Controllers** - Defined RESTful API endpoints  
✅ **HTTP methods** - Used GET, POST, PUT, DELETE decorators  
✅ **URL parameters** - Captured path variables with regex  

## Next Steps

### Add Database Persistence

Replace in-memory storage with a real database:

```python
@service
class TodoService(Service):
    database: 'DatabaseService' = Inject()
    
    def create_todo(self, title, description):
        # Use database instead of dict
        return self.database.insert('todos', {
            'title': title,
            'description': description
        })
```

### Add Authentication

Create an auth service:

```python
@service
class AuthService(Service):
    def verify_token(self, token):
        # Verify JWT token
        pass

@controller(url='/api/todos')
class TodoController:
    auth: 'AuthService' = Inject()
    
    @get_api(url='', headers=['Authorization'])
    def list_todos(self, query_params, headers):
        token = headers.get('Authorization')
        if not self.auth.verify_token(token):
            return {'error': 'Unauthorized'}
        # ...
```

### Add WebSocket Support

For real-time updates:

```python
from cullinan.websocket_registry import websocket_handler

@websocket_handler(url='/ws/todos')
class TodoWebSocket:
    todo_service: 'TodoService' = Inject()
    
    def on_message(self, message):
        # Handle real-time updates
        self.write_message({'todos': self.todo_service.get_all_todos()})
```

## Complete Code

The complete code for this tutorial is available in:
- `examples/tutorial_todo_api/`

## Resources

- [Dependency Injection Guide](./DEPENDENCY_INJECTION.md)
- [Lifecycle Management](./LIFECYCLE_MANAGEMENT.md)
- [API Reference](./API_REFERENCE.md)
- [More Examples](../examples/)

---

**Congratulations!** 🎉 You've built a complete API with Cullinan!

