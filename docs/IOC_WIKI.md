# Cullinan IoC/DI Wiki

Welcome to the complete Wiki for Cullinan's IoC/DI system!

---

## 📚 Documentation Navigation

### Getting Started
- [Quick Start](IOC_USER_GUIDE.md#quick-start)
- [Core Concepts](IOC_USER_GUIDE.md#core-concepts)
- [First Application](#first-application)

### Core Features
- [Dependency Injection](Wiki_Dependency_Injection.md)
- [Provider System](Wiki_Provider_System.md)
- [Scope Management](Wiki_Scope_Management.md)

### Advanced Topics
- [Lifecycle Management](Wiki_Lifecycle.md)
- [Thread Safety](Wiki_Thread_Safety.md)
- [Performance Optimization](Wiki_Performance.md)

### Practical Tutorials
- [Web Application Development](#web-application-development)
- [Microservices Architecture](#microservices-architecture)
- [Testing Strategies](#testing-strategies)

### API Reference
- [Complete API Documentation](API_REFERENCE.md)
- [Decorator Reference](#decorator-reference)
- [Class Reference](#class-reference)

---

## First Application

### Create a Service

```python
# services/user_service.py
from cullinan.service import service

@service
class UserService:
    """User service"""
    
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

### Create a Controller

```python
# controllers/user_controller.py
from cullinan.controller import controller, get, post
from cullinan.core import injectable, Inject
from services.user_service import UserService

@controller('/users')
@injectable
class UserController:
    """User controller"""
    
    user_service: UserService = Inject()
    
    @get('/')
    def list_users(self):
        """List all users"""
        users = self.user_service.list_users()
        return {'users': users}
    
    @get('/{user_id}')
    def get_user(self, user_id: int):
        """Get a single user"""
        user = self.user_service.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return {'user': user}
    
    @post('/')
    def create_user(self, name: str, email: str):
        """Create a user"""
        user = self.user_service.create_user(name, email)
        return {'user': user}, 201
```

### Start the Application

```python
# app.py
from cullinan import Cullinan

app = Cullinan()

# Auto-scan and register services and controllers
app.scan_packages(['services', 'controllers'])

if __name__ == '__main__':
    app.run(port=8080)
```

---

## Web Application Development

### Multi-tier Architecture

```
app/
├── models/          # Data models
│   └── user.py
├── repositories/    # Data access layer
│   └── user_repository.py
├── services/        # Business logic layer
│   └── user_service.py
└── controllers/     # Control layer
    └── user_controller.py
```

#### 1. Data Model

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

#### 2. Data Access Layer

```python
# repositories/user_repository.py
from cullinan.service import service
from cullinan.core import injectable, Inject
from models.user import User

@service
class UserRepository:
    """User data access layer"""
    
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

#### 3. Business Logic Layer

```python
# services/user_service.py
from cullinan.service import service
from cullinan.core import injectable, Inject
from repositories.user_repository import UserRepository
from models.user import User

@service
@injectable
class UserService:
    """User business logic"""
    
    user_repository: UserRepository = Inject()
    email_service: EmailService = Inject()
    logger: Logger = Inject()
    
    def create_user(self, name: str, email: str) -> User:
        """Create a user"""
        # Validate email
        if not self._validate_email(email):
            raise ValueError("Invalid email address")
        
        # Check if email exists
        existing = self.user_repository.find_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        
        # Create user
        user = User(id=None, name=name, email=email)
        user = self.user_repository.save(user)
        
        # Send welcome email
        self.email_service.send_welcome_email(user)
        
        self.logger.info(f"User created: {user.id}")
        return user
    
    def get_user(self, user_id: int) -> User:
        """Get a user"""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user
    
    def list_users(self, active_only: bool = True) -> list[User]:
        """List users"""
        users = self.user_repository.find_all()
        if active_only:
            users = [u for u in users if u.active]
        return users
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> User:
        """Update a user"""
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
        """Delete a user"""
        success = self.user_repository.delete(user_id)
        if success:
            self.logger.info(f"User deleted: {user_id}")
        return success
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None
```

#### 4. Control Layer

```python
# controllers/user_controller.py
from cullinan.controller import controller, get, post, put, delete
from cullinan.core import injectable, Inject
from services.user_service import UserService

@controller('/api/users')
@injectable
class UserController:
    """User API controller"""
    
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

## Microservices Architecture

### Service Configuration

```python
# config/service_config.py
from cullinan.core import SingletonScope, ProviderRegistry, ScopedProvider

def configure_services(app):
    """Configure service dependencies"""
    
    registry = ProviderRegistry()
    
    # Singleton services
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
    
    # Register to IoC container
    from cullinan.core import get_injection_registry
    get_injection_registry().add_provider_registry(registry)
```

### Inter-service Communication

```python
# services/user_service.py
from cullinan.service import service
from cullinan.core import injectable, Inject

@service
@injectable
class UserService:
    """User service"""
    
    database: Database = Inject()
    order_service_client: OrderServiceClient = Inject()
    logger: Logger = Inject()
    
    def get_user_with_orders(self, user_id: int):
        """Get user with orders"""
        # Get user from local database
        user = self.database.get_user(user_id)
        
        # Call order service for orders (inter-service communication)
        orders = self.order_service_client.get_user_orders(user_id)
        
        return {
            'user': user,
            'orders': orders
        }
```

---

## Testing Strategies

### Unit Testing

```python
# tests/test_user_service.py
import pytest
from services.user_service import UserService
from repositories.user_repository import UserRepository

class MockUserRepository:
    """Mock user repository"""
    
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
    """Test creating a user"""
    # Create service
    service = UserService()
    
    # Inject mock dependencies
    service.user_repository = MockUserRepository()
    service.email_service = MockEmailService()
    service.logger = MockLogger()
    
    # Test
    user = service.create_user('John Doe', 'john@example.com')
    
    assert user.id == 1
    assert user.name == 'John Doe'
    assert user.email == 'john@example.com'

def test_create_user_invalid_email():
    """Test creating a user with invalid email"""
    service = UserService()
    service.user_repository = MockUserRepository()
    service.email_service = MockEmailService()
    service.logger = MockLogger()
    
    with pytest.raises(ValueError, match="Invalid email"):
        service.create_user('John Doe', 'invalid-email')
```

### Integration Testing

```python
# tests/test_integration.py
import pytest
from cullinan import Cullinan
from cullinan.core import get_injection_registry, reset_injection_registry

@pytest.fixture
def app():
    """Create test application"""
    reset_injection_registry()
    
    app = Cullinan()
    app.scan_packages(['services', 'controllers'])
    
    yield app
    
    reset_injection_registry()

def test_user_api_integration(app):
    """Test user API integration"""
    client = app.test_client()
    
    # Create user
    response = client.post('/api/users', json={
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    assert response.status_code == 201
    user_id = response.json['user']['id']
    
    # Get user
    response = client.get(f'/api/users/{user_id}')
    assert response.status_code == 200
    assert response.json['user']['name'] == 'John Doe'
    
    # Update user
    response = client.put(f'/api/users/{user_id}', json={
        'name': 'Jane Doe'
    })
    assert response.status_code == 200
    assert response.json['user']['name'] == 'Jane Doe'
    
    # Delete user
    response = client.delete(f'/api/users/{user_id}')
    assert response.status_code == 204
```

---

## Decorator Reference

### @injectable

Mark a class as injectable, enabling dependency injection.

```python
@injectable
class MyClass:
    service: MyService = Inject()
```

### @inject_constructor

Enable constructor injection.

```python
@inject_constructor
class MyClass:
    def __init__(self, service: MyService):
        self.service = service
```

### @service

Register a class as a service (singleton).

```python
@service
class MyService:
    pass
```

### @controller

Register a class as a controller with route prefix.

```python
@controller('/api/users')
class UserController:
    pass
```

---

## Class Reference

### Inject

Dependency injection descriptor.

```python
class Inject:
    def __init__(self, name: str = None, required: bool = True):
        """
        Args:
            name: Dependency name (optional, auto-inferred)
            required: Whether required (default True)
        """
```

### Provider

Abstract base class for dependency providers.

```python
class Provider(ABC):
    @abstractmethod
    def get(self) -> Any:
        """Get dependency instance"""
        pass
    
    @abstractmethod
    def is_singleton(self) -> bool:
        """Is singleton"""
        pass
```

### Scope

Abstract base class for scopes.

```python
class Scope(ABC):
    @abstractmethod
    def get(self, key: str, factory: Callable) -> Any:
        """Get or create instance"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear scope"""
        pass
```

---

## Related Links

- [GitHub Repository](https://github.com/yourusername/cullinan)
- [Issue Tracker](https://github.com/yourusername/cullinan/issues)
- [Changelog](CHANGELOG.md)
- [Contributing Guide](CONTRIBUTING.md)

---

**Last Updated**: 2025-01-13  
**Version**: v0.8.0-beta

