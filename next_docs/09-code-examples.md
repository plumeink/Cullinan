# Code Examples and Patterns

## Executive Summary

This document provides comprehensive code examples demonstrating the enhanced Cullinan framework features, including dependency injection, lifecycle management, and testing patterns.

## 1. Basic Examples

### 1.1 Simple Service (No Dependencies)

```python
from cullinan.service import service, Service

@service
class LogService(Service):
    """Simple logging service with no dependencies."""
    
    def log(self, message, level='INFO'):
        """Log a message."""
        print(f"[{level}] {message}")
    
    def error(self, message):
        """Log an error message."""
        self.log(message, 'ERROR')
```

**Usage in Controller**:
```python
@controller(url='/api')
class HealthController:
    @get_api(url='/health')
    def health_check(self, query_params):
        self.service['LogService'].log("Health check requested")
        return self.response_build(status=200, message="OK")
```

### 1.2 Service with Lifecycle Hooks

```python
@service
class DatabaseService(Service):
    """Database service with connection pooling."""
    
    def on_init(self):
        """Initialize connection pool on startup."""
        self.pool = create_connection_pool(
            host='localhost',
            port=5432,
            max_connections=10
        )
        print("Database connection pool created")
    
    def query(self, sql, params=None):
        """Execute a database query."""
        with self.pool.get_connection() as conn:
            return conn.execute(sql, params or [])
    
    def on_destroy(self):
        """Close connection pool on shutdown."""
        self.pool.close()
        print("Database connection pool closed")
```

## 2. Dependency Injection Examples

### 2.1 Simple Dependency Injection

```python
@service
class ConfigService(Service):
    """Configuration service."""
    
    def get(self, key, default=None):
        # Load from environment or config file
        return os.getenv(key, default)

@service(dependencies=['ConfigService'])
class EmailService(Service):
    """Email service with configuration."""
    
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.smtp_host = config.get('SMTP_HOST', 'localhost')
        self.smtp_port = int(config.get('SMTP_PORT', '587'))
        print(f"Email service configured: {self.smtp_host}:{self.smtp_port}")
    
    def send(self, to, subject, body):
        # Email sending logic using self.smtp_host and self.smtp_port
        return {'sent': True, 'to': to}
```

### 2.2 Multiple Dependencies

```python
@service
class ConfigService(Service):
    def get(self, key, default=None):
        return os.getenv(key, default)

@service(dependencies=['ConfigService'])
class DatabaseService(Service):
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.db_url = config.get('DATABASE_URL')
        self.pool = create_pool(self.db_url)
    
    def query(self, sql):
        return self.pool.execute(sql)

@service(dependencies=['ConfigService'])
class EmailService(Service):
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.smtp_host = config.get('SMTP_HOST')
    
    def send(self, to, subject, body):
        # Send email logic
        pass

@service(dependencies=['DatabaseService', 'EmailService'])
class UserService(Service):
    """User service with multiple dependencies."""
    
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
        self.email = self.dependencies['EmailService']
        print("UserService initialized with DB and Email")
    
    def create_user(self, name, email):
        # Save to database
        user = {'name': name, 'email': email}
        self.db.query(f"INSERT INTO users VALUES ('{name}', '{email}')")
        
        # Send welcome email
        self.email.send(email, 'Welcome', f'Hello {name}!')
        
        return user
```

### 2.3 Nested Dependencies

```python
# Level 1: No dependencies
@service
class LogService(Service):
    def log(self, message):
        print(f"LOG: {message}")

# Level 2: Depends on Level 1
@service(dependencies=['LogService'])
class ConfigService(Service):
    def on_init(self):
        self.log = self.dependencies['LogService']
        self.log.log("ConfigService initialized")
    
    def get(self, key):
        self.log.log(f"Config key requested: {key}")
        return os.getenv(key)

# Level 3: Depends on Level 2
@service(dependencies=['ConfigService'])
class DatabaseService(Service):
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.db_url = config.get('DATABASE_URL')
        # Config will log the request automatically

# Level 4: Depends on Level 3
@service(dependencies=['DatabaseService'])
class UserService(Service):
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
```

## 3. Real-World Application Examples

### 3.1 E-Commerce Order Processing

```python
# services/inventory_service.py
@service(dependencies=['DatabaseService'])
class InventoryService(Service):
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
    
    def check_stock(self, product_id, quantity):
        stock = self.db.query(
            "SELECT stock FROM inventory WHERE product_id = ?",
            [product_id]
        )[0]['stock']
        return stock >= quantity
    
    def reserve_stock(self, product_id, quantity):
        self.db.query(
            "UPDATE inventory SET stock = stock - ? WHERE product_id = ?",
            [quantity, product_id]
        )

# services/payment_service.py
@service(dependencies=['ConfigService'])
class PaymentService(Service):
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.stripe_key = config.get('STRIPE_SECRET_KEY')
    
    def charge(self, amount, currency, card_token):
        # Stripe payment processing
        return {'success': True, 'transaction_id': 'txn_123'}

# services/notification_service.py
@service(dependencies=['EmailService', 'ConfigService'])
class NotificationService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
        self.config = self.dependencies['ConfigService']
        self.sms_enabled = self.config.get('SMS_ENABLED', 'false') == 'true'
    
    def notify_order_placed(self, user_email, order_id):
        self.email.send(
            user_email,
            'Order Confirmation',
            f'Your order #{order_id} has been placed!'
        )

# services/order_service.py
@service(dependencies=[
    'InventoryService',
    'PaymentService',
    'NotificationService',
    'DatabaseService'
])
class OrderService(Service):
    """Order service orchestrates the order process."""
    
    def on_init(self):
        self.inventory = self.dependencies['InventoryService']
        self.payment = self.dependencies['PaymentService']
        self.notification = self.dependencies['NotificationService']
        self.db = self.dependencies['DatabaseService']
    
    def place_order(self, user_email, items, card_token):
        """Place an order with inventory check, payment, and notification."""
        
        # 1. Check inventory for all items
        for item in items:
            if not self.inventory.check_stock(item['product_id'], item['quantity']):
                raise ValueError(f"Insufficient stock for {item['product_id']}")
        
        # 2. Calculate total
        total = sum(item['price'] * item['quantity'] for item in items)
        
        # 3. Process payment
        payment_result = self.payment.charge(total, 'USD', card_token)
        if not payment_result['success']:
            raise ValueError("Payment failed")
        
        # 4. Reserve inventory
        for item in items:
            self.inventory.reserve_stock(item['product_id'], item['quantity'])
        
        # 5. Create order record
        order_id = self.db.query(
            "INSERT INTO orders (user_email, total, status) VALUES (?, ?, 'placed') RETURNING id",
            [user_email, total]
        )[0]['id']
        
        # 6. Send notification
        self.notification.notify_order_placed(user_email, order_id)
        
        return {
            'order_id': order_id,
            'total': total,
            'transaction_id': payment_result['transaction_id']
        }

# controllers/order_controller.py
@controller(url='/api')
class OrderController:
    @post_api(url='/orders', body_params=['items', 'card_token'])
    def place_order(self, body_params):
        try:
            # Get user email from session/auth
            user_email = self.get_current_user_email()
            
            # Place order using service
            result = self.service['OrderService'].place_order(
                user_email,
                body_params['items'],
                body_params['card_token']
            )
            
            return self.response_build(
                status=201,
                message="Order placed successfully",
                data=result
            )
        except ValueError as e:
            return self.response_build(
                status=400,
                message=str(e)
            )
```

### 3.2 User Authentication System

```python
# services/hash_service.py
@service
class HashService(Service):
    """Password hashing service."""
    
    def hash_password(self, password):
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password, hashed):
        import bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())

# services/token_service.py
@service(dependencies=['ConfigService'])
class TokenService(Service):
    """JWT token service."""
    
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.secret_key = config.get('JWT_SECRET_KEY')
        self.expiry_hours = int(config.get('JWT_EXPIRY_HOURS', '24'))
    
    def generate_token(self, user_id):
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.expiry_hours)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        import jwt
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# services/auth_service.py
@service(dependencies=['DatabaseService', 'HashService', 'TokenService'])
class AuthService(Service):
    """Authentication service."""
    
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
        self.hash = self.dependencies['HashService']
        self.token = self.dependencies['TokenService']
    
    def register(self, email, password, name):
        """Register a new user."""
        # Check if user exists
        existing = self.db.query(
            "SELECT id FROM users WHERE email = ?",
            [email]
        )
        if existing:
            raise ValueError("User already exists")
        
        # Hash password
        hashed_password = self.hash.hash_password(password)
        
        # Create user
        user_id = self.db.query(
            "INSERT INTO users (email, password, name) VALUES (?, ?, ?) RETURNING id",
            [email, hashed_password, name]
        )[0]['id']
        
        # Generate token
        token = self.token.generate_token(user_id)
        
        return {'user_id': user_id, 'token': token}
    
    def login(self, email, password):
        """Authenticate a user."""
        # Get user
        user = self.db.query(
            "SELECT id, password FROM users WHERE email = ?",
            [email]
        )
        if not user:
            raise ValueError("Invalid credentials")
        
        user = user[0]
        
        # Verify password
        if not self.hash.verify_password(password, user['password']):
            raise ValueError("Invalid credentials")
        
        # Generate token
        token = self.token.generate_token(user['id'])
        
        return {'user_id': user['id'], 'token': token}
    
    def verify_token(self, token):
        """Verify a JWT token."""
        user_id = self.token.verify_token(token)
        if not user_id:
            return None
        
        # Get user
        user = self.db.query(
            "SELECT id, email, name FROM users WHERE id = ?",
            [user_id]
        )
        return user[0] if user else None

# controllers/auth_controller.py
@controller(url='/api/auth')
class AuthController:
    @post_api(url='/register', body_params=['email', 'password', 'name'])
    def register(self, body_params):
        try:
            result = self.service['AuthService'].register(
                body_params['email'],
                body_params['password'],
                body_params['name']
            )
            return self.response_build(status=201, data=result)
        except ValueError as e:
            return self.response_build(status=400, message=str(e))
    
    @post_api(url='/login', body_params=['email', 'password'])
    def login(self, body_params):
        try:
            result = self.service['AuthService'].login(
                body_params['email'],
                body_params['password']
            )
            return self.response_build(status=200, data=result)
        except ValueError as e:
            return self.response_build(status=401, message=str(e))
```

## 4. Testing Examples

### 4.1 Testing Service with Mocks

```python
from cullinan.testing import TestRegistry, MockService

class MockEmailService(MockService):
    def send(self, to, subject, body):
        self.record_call('send', to=to, subject=subject, body=body)
        return True

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.registry = TestRegistry()
        self.mock_email = MockEmailService()
        self.registry.register_mock('EmailService', self.mock_email)
        self.registry.register('UserService', UserService, 
                              dependencies=['EmailService'])
    
    def test_create_user_sends_welcome_email(self):
        service = self.registry.get('UserService')
        user = service.create_user('John', 'john@example.com')
        
        # Verify email was sent
        self.assertTrue(self.mock_email.was_called('send'))
        args = self.mock_email.get_call_args('send')
        self.assertEqual(args['to'], 'john@example.com')
        self.assertIn('Welcome', args['subject'])
    
    def tearDown(self):
        self.registry.clear()
```

### 4.2 Testing Complex Service Interactions

```python
class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.registry = TestRegistry()
        
        # Register mocks
        self.mock_inventory = MockInventoryService()
        self.mock_payment = MockPaymentService()
        self.mock_notification = MockNotificationService()
        
        self.registry.register_mock('InventoryService', self.mock_inventory)
        self.registry.register_mock('PaymentService', self.mock_payment)
        self.registry.register_mock('NotificationService', self.mock_notification)
        self.registry.register_mock('DatabaseService', MockDatabaseService())
        
        # Register service under test
        self.registry.register('OrderService', OrderService,
            dependencies=['InventoryService', 'PaymentService', 
                         'NotificationService', 'DatabaseService'])
    
    def test_place_order_success(self):
        # Setup mock behaviors
        self.mock_inventory.stock_available = True
        self.mock_payment.will_succeed = True
        
        # Test
        service = self.registry.get('OrderService')
        result = service.place_order(
            'user@example.com',
            [{'product_id': 1, 'quantity': 2, 'price': 10.00}],
            'card_token_123'
        )
        
        # Verify
        self.assertIsNotNone(result['order_id'])
        self.assertEqual(result['total'], 20.00)
        
        # Verify inventory was checked and reserved
        self.assertTrue(self.mock_inventory.was_called('check_stock'))
        self.assertTrue(self.mock_inventory.was_called('reserve_stock'))
        
        # Verify payment was processed
        self.assertTrue(self.mock_payment.was_called('charge'))
        
        # Verify notification was sent
        self.assertTrue(self.mock_notification.was_called('notify_order_placed'))
    
    def test_place_order_insufficient_stock(self):
        # Setup: Inventory check fails
        self.mock_inventory.stock_available = False
        
        # Test
        service = self.registry.get('OrderService')
        
        with self.assertRaises(ValueError) as context:
            service.place_order(
                'user@example.com',
                [{'product_id': 1, 'quantity': 2, 'price': 10.00}],
                'card_token_123'
            )
        
        # Verify error message
        self.assertIn('Insufficient stock', str(context.exception))
        
        # Verify payment was NOT attempted
        self.assertFalse(self.mock_payment.was_called('charge'))
```

## 5. Advanced Patterns

### 5.1 Service Factory Pattern

```python
@service(dependencies=['ConfigService'])
class EmailServiceFactory(Service):
    """Factory for creating email services based on configuration."""
    
    def on_init(self):
        config = self.dependencies['ConfigService']
        self.provider = config.get('EMAIL_PROVIDER', 'smtp')
    
    def create_email_service(self):
        if self.provider == 'smtp':
            return SMTPEmailService()
        elif self.provider == 'sendgrid':
            return SendGridEmailService()
        else:
            raise ValueError(f"Unknown email provider: {self.provider}")
```

### 5.2 Service Decorator Pattern

```python
@service(dependencies=['EmailService'])
class RetryEmailService(Service):
    """Decorator that adds retry logic to email sending."""
    
    def on_init(self):
        self.email_service = self.dependencies['EmailService']
        self.max_retries = 3
    
    def send(self, to, subject, body):
        for attempt in range(self.max_retries):
            try:
                return self.email_service.send(to, subject, body)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

### 5.3 Service Observer Pattern

```python
@service
class EventBus(Service):
    """Event bus for pub/sub pattern."""
    
    def on_init(self):
        self.subscribers = {}
    
    def subscribe(self, event_name, callback):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
    
    def publish(self, event_name, data):
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                callback(data)

@service(dependencies=['EventBus'])
class UserService(Service):
    def on_init(self):
        self.event_bus = self.dependencies['EventBus']
    
    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        # Publish event
        self.event_bus.publish('user.created', user)
        return user

@service(dependencies=['EventBus', 'EmailService'])
class WelcomeEmailListener(Service):
    def on_init(self):
        event_bus = self.dependencies['EventBus']
        self.email = self.dependencies['EmailService']
        
        # Subscribe to user.created event
        event_bus.subscribe('user.created', self.on_user_created)
    
    def on_user_created(self, user):
        self.email.send(user['email'], 'Welcome', f"Hello {user['name']}!")
```

---

**Document Version**: 1.0  
**Author**: Cullinan Framework Team  
**Date**: 2025-11-10  
**Status**: Final Draft
