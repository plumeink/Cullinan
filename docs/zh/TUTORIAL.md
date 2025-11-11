# 完整教程：构建 Todo API

在本教程中，您将使用 Cullinan 构建一个完整的 RESTful API Todo 应用。

## 您将构建什么

一个包含以下功能的 Todo API：
- ✅ CRUD 操作（创建、读取、更新、删除）
- ✅ 业务逻辑服务层
- ✅ 内存数据库
- ✅ 依赖注入
- ✅ 错误处理

## 前置要求

- Python 3.8+
- 已安装 Cullinan 框架
- 基本 Python 知识

## 步骤 1：项目设置

创建项目结构：

```bash
mkdir todo-api
cd todo-api
mkdir controllers services models
touch app.py .env
touch controllers/__init__.py services/__init__.py models/__init__.py
```

您的结构：
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

## 步骤 2：定义模型

创建 `models/todo.py`：

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    """Todo 项目模型"""
    id: int
    title: str
    completed: bool = False
    description: Optional[str] = None
    
    def to_dict(self):
        """转换为字典用于 JSON 序列化"""
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'description': self.description
        }
```

## 步骤 3：创建服务

创建 `services/todo_service.py`：

```python
from cullinan.service import service, Service
from models.todo import Todo
from typing import List, Optional

@service
class TodoService(Service):
    """Todo 业务逻辑服务"""
    
    def __init__(self):
        super().__init__()
        self._todos = {}
        self._next_id = 1
    
    def get_phase(self) -> int:
        """早启动以初始化数据"""
        return -50
    
    def on_startup(self):
        """初始化示例数据"""
        print("正在初始化 TodoService 示例数据...")
        self.create_todo("学习 Cullinan", "阅读文档")
        self.create_todo("构建 API", "完成教程")
    
    def get_all_todos(self) -> List[Todo]:
        """获取所有 todos"""
        return list(self._todos.values())
    
    def get_todo(self, todo_id: int) -> Optional[Todo]:
        """根据 ID 获取特定 todo"""
        return self._todos.get(todo_id)
    
    def create_todo(self, title: str, description: str = None) -> Todo:
        """创建新 todo"""
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
        """更新现有 todo"""
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
        """删除 todo"""
        if todo_id in self._todos:
            del self._todos[todo_id]
            return True
        return False
    
    def toggle_completed(self, todo_id: int) -> Optional[Todo]:
        """切换 todo 完成状态"""
        todo = self._todos.get(todo_id)
        if todo:
            todo.completed = not todo.completed
        return todo
```

## 步骤 4：创建控制器

创建 `controllers/todo_controller.py`：

```python
from cullinan.controller import controller, get_api, post_api, put_api, delete_api
from cullinan.core import Inject

@controller(url='/api/todos')
class TodoController:
    """Todo API 端点"""
    
    # 注入 TodoService（无需 import！）
    todo_service: 'TodoService' = Inject()
    
    @get_api(url='')
    def list_todos(self, query_params):
        """GET /api/todos - 列出所有 todos"""
        todos = self.todo_service.get_all_todos()
        return {
            'success': True,
            'count': len(todos),
            'todos': [todo.to_dict() for todo in todos]
        }
    
    @get_api(url='/([0-9]+)')
    def get_todo(self, todo_id):
        """GET /api/todos/{id} - 获取特定 todo"""
        todo = self.todo_service.get_todo(int(todo_id))
        
        if not todo:
            return {
                'success': False,
                'error': '未找到 Todo'
            }
        
        return {
            'success': True,
            'todo': todo.to_dict()
        }
    
    @post_api(url='')
    def create_todo(self, body_params):
        """POST /api/todos - 创建新 todo"""
        title = body_params.get('title')
        
        if not title:
            return {
                'success': False,
                'error': '标题为必填项'
            }
        
        description = body_params.get('description')
        todo = self.todo_service.create_todo(title, description)
        
        return {
            'success': True,
            'message': 'Todo 已创建',
            'todo': todo.to_dict()
        }
    
    @put_api(url='/([0-9]+)')
    def update_todo(self, todo_id, body_params):
        """PUT /api/todos/{id} - 更新 todo"""
        todo = self.todo_service.update_todo(
            int(todo_id),
            title=body_params.get('title'),
            description=body_params.get('description'),
            completed=body_params.get('completed')
        )
        
        if not todo:
            return {
                'success': False,
                'error': '未找到 Todo'
            }
        
        return {
            'success': True,
            'message': 'Todo 已更新',
            'todo': todo.to_dict()
        }
    
    @post_api(url='/([0-9]+)/toggle')
    def toggle_todo(self, todo_id):
        """POST /api/todos/{id}/toggle - 切换完成状态"""
        todo = self.todo_service.toggle_completed(int(todo_id))
        
        if not todo:
            return {
                'success': False,
                'error': '未找到 Todo'
            }
        
        return {
            'success': True,
            'message': 'Todo 状态已切换',
            'todo': todo.to_dict()
        }
    
    @delete_api(url='/([0-9]+)')
    def delete_todo(self, todo_id):
        """DELETE /api/todos/{id} - 删除 todo"""
        deleted = self.todo_service.delete_todo(int(todo_id))
        
        if not deleted:
            return {
                'success': False,
                'error': '未找到 Todo'
            }
        
        return {
            'success': True,
            'message': 'Todo 已删除'
        }
```

## 步骤 5：创建主应用

创建 `app.py`：

```python
from cullinan import application

# 导入控制器和服务以注册它们
from controllers.todo_controller import TodoController
from services.todo_service import TodoService

if __name__ == '__main__':
    print("启动 Todo API...")
    print("API 端点:")
    print("  GET    /api/todos        - 列出所有 todos")
    print("  GET    /api/todos/{id}   - 获取特定 todo")
    print("  POST   /api/todos        - 创建新 todo")
    print("  PUT    /api/todos/{id}   - 更新 todo")
    print("  DELETE /api/todos/{id}   - 删除 todo")
    print("  POST   /api/todos/{id}/toggle - 切换完成状态")
    print("\n服务器启动于 http://localhost:4080")
    
    application.run()
```

## 步骤 6：配置环境

创建 `.env`：

```env
SERVER_PORT=4080
SERVER_THREAD=1
```

## 步骤 7：运行应用

```bash
python app.py
```

您应该看到：

```
启动 Todo API...
API 端点:
  GET    /api/todos        - 列出所有 todos
  ...
服务器启动于 http://localhost:4080
|||	server is starting
|||	port is 4080
```

## 步骤 8：测试 API

### 列出所有 todos

```bash
curl http://localhost:4080/api/todos
```

响应：
```json
{
  "success": true,
  "count": 2,
  "todos": [
    {
      "id": 1,
      "title": "学习 Cullinan",
      "completed": false,
      "description": "阅读文档"
    },
    {
      "id": 2,
      "title": "构建 API",
      "completed": false,
      "description": "完成教程"
    }
  ]
}
```

### 创建新 todo

```bash
curl -X POST http://localhost:4080/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "测试 API", "description": "使用 curl 测试"}'
```

### 获取特定 todo

```bash
curl http://localhost:4080/api/todos/1
```

### 更新 todo

```bash
curl -X PUT http://localhost:4080/api/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### 切换完成状态

```bash
curl -X POST http://localhost:4080/api/todos/1/toggle
```

### 删除 todo

```bash
curl -X DELETE http://localhost:4080/api/todos/1
```

## 您学到了什么

✅ **项目结构** - 将代码组织到控制器、服务和模型中  
✅ **服务** - 使用 `@service` 创建业务逻辑层  
✅ **依赖注入** - 使用字符串注解注入服务  
✅ **生命周期钩子** - 在 `on_startup()` 中初始化数据  
✅ **控制器** - 定义 RESTful API 端点  
✅ **HTTP 方法** - 使用 GET、POST、PUT、DELETE 装饰器  
✅ **URL 参数** - 使用正则表达式捕获路径变量  

## 下一步

### 添加数据库持久化

用真实数据库替换内存存储：

```python
@service
class TodoService(Service):
    database: 'DatabaseService' = Inject()
    
    def create_todo(self, title, description):
        # 使用数据库而不是字典
        return self.database.insert('todos', {
            'title': title,
            'description': description
        })
```

### 添加认证

创建认证服务：

```python
@service
class AuthService(Service):
    def verify_token(self, token):
        # 验证 JWT token
        pass

@controller(url='/api/todos')
class TodoController:
    auth: 'AuthService' = Inject()
    
    @get_api(url='', headers=['Authorization'])
    def list_todos(self, query_params, headers):
        token = headers.get('Authorization')
        if not self.auth.verify_token(token):
            return {'error': '未授权'}
        # ...
```

### 添加 WebSocket 支持

用于实时更新：

```python
from cullinan.websocket_registry import websocket_handler

@websocket_handler(url='/ws/todos')
class TodoWebSocket:
    todo_service: 'TodoService' = Inject()
    
    def on_message(self, message):
        # 处理实时更新
        self.write_message({'todos': self.todo_service.get_all_todos()})
```

## 完整代码

本教程的完整代码位于：
- `examples/tutorial_todo_api/`

## 资源

- [依赖注入指南](./DEPENDENCY_INJECTION.md)
- [生命周期管理](./LIFECYCLE_MANAGEMENT.md)
- [API 参考](./API_REFERENCE.md)
- [更多示例](../examples/)

---

**恭喜！** 🎉 您已使用 Cullinan 构建了一个完整的 API！

