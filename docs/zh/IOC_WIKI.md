# Cullinan IoC/DI Wiki

欢迎来到 Cullinan IoC/DI 系统的完整 Wiki！

---

## 📚 文档导航

### 入门指南
- [快速开始](IOC_USER_GUIDE.md#快速开始)
- [核心概念](IOC_USER_GUIDE.md#核心概念)
- [第一个应用](#第一个应用)

### 核心功能
- [依赖注入](Wiki_Dependency_Injection.md)
- [Provider 系统](Wiki_Provider_System.md)
- [作用域管理](Wiki_Scope_Management.md)

### 高级主题
- [生命周期管理](Wiki_Lifecycle.md)
- [线程安全](Wiki_Thread_Safety.md)
- [性能优化](Wiki_Performance.md)

### 实战教程
- [Web 应用开发](#web-应用开发)
- [微服务架构](#微服务架构)
- [测试策略](#测试策略)

### API 参考
- [完整 API 文档](API_REFERENCE.md)
- [装饰器参考](#装饰器参考)
- [类参考](#类参考)

---

## 第一个应用

### 创建服务

```python
# services/user_service.py
from cullinan.service import service

@service
class UserService:
    """用户服务"""
    
    def __init__(self):
        self.users = {}
    
    def create_user(self, name, email):
        user_id = len(self.users) + 1
        user = {'id': user_id, 'name': name, 'email': email}
        self.users[user_id] = user
        return user
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def list_users(self):
        return list(self.users.values())
```

### 创建控制器

```python
# controllers/user_controller.py
from cullinan.controller import controller, get, post
from cullinan.core import injectable, Inject
from services.user_service import UserService

@controller('/users')
@injectable
class UserController:
    """用户控制器"""
    
    user_service: UserService = Inject()
    
    @get('/')
    def list_users(self):
        """列出所有用户"""
        users = self.user_service.list_users()
        return {'users': users}
    
    @get('/{user_id}')
    def get_user(self, user_id: int):
        """获取单个用户"""
        user = self.user_service.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return {'user': user}
    
    @post('/')
    def create_user(self, name: str, email: str):
        """创建用户"""
        user = self.user_service.create_user(name, email)
        return {'user': user}, 201
```

### 启动应用

```python
# app.py
from cullinan import Cullinan

app = Cullinan()

# 自动扫描并注册服务和控制器
app.scan_packages(['services', 'controllers'])

if __name__ == '__main__':
    app.run(port=8080)
```

---

## Web 应用开发

### 多层架构

```
app/
├── models/          # 数据模型
│   └── user.py
├── repositories/    # 数据访问层
│   └── user_repository.py
├── services/        # 业务逻辑层
│   └── user_service.py
└── controllers/     # 控制层
    └── user_controller.py
```

#### 1. 数据模型

```python
# models/user.py
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    active: bool = True
```

#### 2. 数据访问层

```python
# repositories/user_repository.py
from cullinan.service import service
from cullinan.core import injectable, Inject
from models.user import User

@service
class UserRepository:
    """用户数据访问层"""
    
    database: Database = Inject()
    
    def find_by_id(self, user_id: int) -> User:
        row = self.database.query_one(
            "SELECT * FROM users WHERE id = ?", user_id
        )
        return User(**row) if row else None
    
    def find_all(self) -> list[User]:
        rows = self.database.query_all("SELECT * FROM users")
        return [User(**row) for row in rows]
    
    def save(self, user: User) -> User:
        if user.id:
            self.database.execute(
                "UPDATE users SET name=?, email=?, active=? WHERE id=?",
                user.name, user.email, user.active, user.id
            )
        else:
            user.id = self.database.execute(
                "INSERT INTO users (name, email, active) VALUES (?, ?, ?)",
                user.name, user.email, user.active
            )
        return user
    
    def delete(self, user_id: int) -> bool:
        affected = self.database.execute(
            "DELETE FROM users WHERE id = ?", user_id
        )
        return affected > 0
```

#### 3. 业务逻辑层

```python
# services/user_service.py
from cullinan.service import service
from cullinan.core import injectable, Inject
from repositories.user_repository import UserRepository
from models.user import User

@service
@injectable
class UserService:
    """用户业务逻辑"""
    
    user_repository: UserRepository = Inject()
    email_service: EmailService = Inject()
    logger: Logger = Inject()
    
    def create_user(self, name: str, email: str) -> User:
        """创建用户"""
        # 验证邮箱
        if not self._validate_email(email):
            raise ValueError("Invalid email address")
        
        # 检查邮箱是否已存在
        existing = self.user_repository.find_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        
        # 创建用户
        user = User(id=None, name=name, email=email)
        user = self.user_repository.save(user)
        
        # 发送欢迎邮件
        self.email_service.send_welcome_email(user)
        
        self.logger.info(f"User created: {user.id}")
        return user
    
    def get_user(self, user_id: int) -> User:
        """获取用户"""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user
    
    def list_users(self, active_only: bool = True) -> list[User]:
        """列出用户"""
        users = self.user_repository.find_all()
        if active_only:
            users = [u for u in users if u.active]
        return users
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> User:
        """更新用户"""
        user = self.get_user(user_id)
        
        if name:
            user.name = name
        if email:
            if not self._validate_email(email):
                raise ValueError("Invalid email address")
            user.email = email
        
        user = self.user_repository.save(user)
        self.logger.info(f"User updated: {user.id}")
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        success = self.user_repository.delete(user_id)
        if success:
            self.logger.info(f"User deleted: {user_id}")
        return success
    
    def _validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None
```

#### 4. 控制层

```python
# controllers/user_controller.py
from cullinan.controller import controller, get, post, put, delete
from cullinan.core import injectable, Inject
from services.user_service import UserService

@controller('/api/users')
@injectable
class UserController:
    """用户 API 控制器"""
    
    user_service: UserService = Inject()
    
    @get('/')
    def list_users(self, active: bool = True):
        """GET /api/users?active=true"""
        users = self.user_service.list_users(active_only=active)
        return {'users': [u.__dict__ for u in users]}
    
    @get('/{user_id}')
    def get_user(self, user_id: int):
        """GET /api/users/123"""
        try:
            user = self.user_service.get_user(user_id)
            return {'user': user.__dict__}
        except ValueError as e:
            return {'error': str(e)}, 404
    
    @post('/')
    def create_user(self, name: str, email: str):
        """POST /api/users"""
        try:
            user = self.user_service.create_user(name, email)
            return {'user': user.__dict__}, 201
        except ValueError as e:
            return {'error': str(e)}, 400
    
    @put('/{user_id}')
    def update_user(self, user_id: int, name: str = None, email: str = None):
        """PUT /api/users/123"""
        try:
            user = self.user_service.update_user(user_id, name, email)
            return {'user': user.__dict__}
        except ValueError as e:
            return {'error': str(e)}, 400
    
    @delete('/{user_id}')
    def delete_user(self, user_id: int):
        """DELETE /api/users/123"""
        success = self.user_service.delete_user(user_id)
        if success:
            return {'message': 'User deleted'}, 204
        return {'error': 'User not found'}, 404
```

---

## 微服务架构

### 服务配置

```python
# config/service_config.py
from cullinan.core import SingletonScope, ProviderRegistry, ScopedProvider

def configure_services(app):
    """配置服务依赖"""
    
    registry = ProviderRegistry()
    
    # 单例服务
    registry.register_provider(
        'Database',
        ScopedProvider(
            lambda: Database(app.config.get('DATABASE_URL')),
            SingletonScope(),
            'Database'
        )
    )
    
    registry.register_provider(
        'Cache',
        ScopedProvider(
            lambda: RedisCache(app.config.get('REDIS_URL')),
            SingletonScope(),
            'Cache'
        )
    )
    
    # 注册到 IoC 容器
    from cullinan.core import get_injection_registry
    get_injection_registry().add_provider_registry(registry)
```

### 服务间通信

```python
# services/user_service.py
from cullinan.service import service
from cullinan.core import injectable, Inject

@service
@injectable
class UserService:
    """用户服务"""
    
    database: Database = Inject()
    order_service_client: OrderServiceClient = Inject()
    logger: Logger = Inject()
    
    def get_user_with_orders(self, user_id: int):
        """获取用户及其订单"""
        # 从本地数据库获取用户
        user = self.database.get_user(user_id)
        
        # 调用订单服务获取订单（微服务间通信）
        orders = self.order_service_client.get_user_orders(user_id)
        
        return {
            'user': user,
            'orders': orders
        }
```

---

## 测试策略

### 单元测试

```python
# tests/test_user_service.py
import pytest
from services.user_service import UserService
from repositories.user_repository import UserRepository

class MockUserRepository:
    """Mock 用户仓储"""
    
    def __init__(self):
        self.users = {}
    
    def find_by_id(self, user_id):
        return self.users.get(user_id)
    
    def save(self, user):
        if not user.id:
            user.id = len(self.users) + 1
        self.users[user.id] = user
        return user

def test_create_user():
    """测试创建用户"""
    # 创建服务
    service = UserService()
    
    # 注入 Mock 依赖
    service.user_repository = MockUserRepository()
    service.email_service = MockEmailService()
    service.logger = MockLogger()
    
    # 测试
    user = service.create_user('John Doe', 'john@example.com')
    
    assert user.id == 1
    assert user.name == 'John Doe'
    assert user.email == 'john@example.com'

def test_create_user_invalid_email():
    """测试创建用户 - 无效邮箱"""
    service = UserService()
    service.user_repository = MockUserRepository()
    service.email_service = MockEmailService()
    service.logger = MockLogger()
    
    with pytest.raises(ValueError, match="Invalid email"):
        service.create_user('John Doe', 'invalid-email')
```

### 集成测试

```python
# tests/test_integration.py
import pytest
from cullinan import Cullinan
from cullinan.core import get_injection_registry, reset_injection_registry

@pytest.fixture
def app():
    """创建测试应用"""
    reset_injection_registry()
    
    app = Cullinan()
    app.scan_packages(['services', 'controllers'])
    
    yield app
    
    reset_injection_registry()

def test_user_api_integration(app):
    """测试用户 API 集成"""
    client = app.test_client()
    
    # 创建用户
    response = client.post('/api/users', json={
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    assert response.status_code == 201
    user_id = response.json['user']['id']
    
    # 获取用户
    response = client.get(f'/api/users/{user_id}')
    assert response.status_code == 200
    assert response.json['user']['name'] == 'John Doe'
    
    # 更新用户
    response = client.put(f'/api/users/{user_id}', json={
        'name': 'Jane Doe'
    })
    assert response.status_code == 200
    assert response.json['user']['name'] == 'Jane Doe'
    
    # 删除用户
    response = client.delete(f'/api/users/{user_id}')
    assert response.status_code == 204
```

---

## 装饰器参考

### @injectable

标记类可注入，启用依赖注入。

```python
@injectable
class MyClass:
    service: MyService = Inject()
```

### @inject_constructor

启用构造器注入。

```python
@inject_constructor
class MyClass:
    def __init__(self, service: MyService):
        self.service = service
```

### @service

注册类为服务（单例）。

```python
@service
class MyService:
    pass
```

### @controller

注册类为控制器并定义路由前缀。

```python
@controller('/api/users')
class UserController:
    pass
```

---

## 类参考

### Inject

依赖注入描述符。

```python
class Inject:
    def __init__(self, name: str = None, required: bool = True):
        """
        Args:
            name: 依赖名称（可选，自动推断）
            required: 是否必需（默认 True）
        """
```

### Provider

依赖提供者抽象基类。

```python
class Provider(ABC):
    @abstractmethod
    def get(self) -> Any:
        """获取依赖实例"""
        pass
    
    @abstractmethod
    def is_singleton(self) -> bool:
        """是否为单例"""
        pass
```

### Scope

作用域抽象基类。

```python
class Scope(ABC):
    @abstractmethod
    def get(self, key: str, factory: Callable) -> Any:
        """获取或创建实例"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清理作用域"""
        pass
```

---

## 相关链接

- [GitHub 仓库](https://github.com/yourusername/cullinan)
- [问题反馈](https://github.com/yourusername/cullinan/issues)
- [更新日志](CHANGELOG.md)
- [贡献指南](CONTRIBUTING.md)

---

**最后更新**: 2025-01-13  
**版本**: v0.8.0-beta

