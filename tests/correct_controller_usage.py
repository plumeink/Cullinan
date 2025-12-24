# -*- coding: utf-8 -*-
"""正确使用 Controller 的示例

演示如何正确使用 @controller 和 @get_api/@post_api 装饰器

作者：Plumeink
日期：2025-12-24
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_correct_controller_usage():
    """测试正确的 Controller 使用方式"""
    logger.info("=" * 80)
    logger.info("正确的 Controller 使用示例")
    logger.info("=" * 80)
    
    # 1. 导入必要组件
    logger.info("\n[1] 导入组件...")
    from cullinan.service import service
    from cullinan.controller import controller, get_api, post_api
    from cullinan.core import Inject
    from cullinan.controller import get_controller_registry
    from cullinan.service import get_service_registry
    
    # 2. 创建服务
    logger.info("\n[2] 创建服务...")
    @service
    class UserService:
        def get_users(self):
            return [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        
        def create_user(self, name):
            return {"id": 3, "name": name, "created": True}
    
    logger.info("✓ UserService 已定义")
    
    # 3. 创建 Controller（正确方式）
    logger.info("\n[3] 创建 Controller（使用 @get_api/@post_api）...")
    
    @controller(url='/api/users')
    class UserController:
        user_service: UserService = Inject()
        
        @get_api(url='')  # GET /api/users
        def list_users(self):
            """获取用户列表"""
            logger.info("UserController.list_users() 被调用")
            users = self.user_service.get_users()
            return {'users': users, 'count': len(users)}
        
        @get_api(url='/{user_id}')  # GET /api/users/123
        def get_user(self, user_id):
            """获取单个用户"""
            logger.info(f"UserController.get_user({user_id}) 被调用")
            return {'user_id': user_id, 'name': 'User ' + user_id}
        
        @post_api(url='', body_params=['name'])  # POST /api/users
        def create_user(self, name):
            """创建用户"""
            logger.info(f"UserController.create_user(name={name}) 被调用")
            user = self.user_service.create_user(name)
            return user
    
    logger.info("✓ UserController 已定义")
    
    # 4. 检查注册情况
    logger.info("\n[4] 检查注册情况...")
    controller_registry = get_controller_registry()
    service_registry = get_service_registry()
    
    logger.info(f"已注册的 Controller 数量: {controller_registry.count()}")
    logger.info(f"已注册的 Service 数量: {service_registry.count()}")
    
    # 检查方法注册
    methods = controller_registry.get_methods('UserController')
    logger.info(f"\n已注册的方法数量: {len(methods)}")
    
    if methods:
        for url, http_method, handler_func in methods:
            logger.info(f"  ✓ {http_method.upper()} /api/users{url} -> {handler_func.__name__}")
    else:
        logger.error("  ✗ 没有注册任何方法！")
        return False
    
    logger.info("\n" + "=" * 80)
    logger.info("示例完成")
    logger.info("=" * 80)
    
    return True


def show_common_mistakes():
    """展示常见错误"""
    logger.info("\n" + "=" * 80)
    logger.info("常见错误示例")
    logger.info("=" * 80)
    
    logger.info("""
❌ 错误方式1：直接定义方法，没有使用装饰器
    
    @controller(url='/api/test')
    class TestController:
        async def get(self):  # ❌ 错误！方法不会被注册
            return {"message": "Hello"}

✅ 正确方式：使用 @get_api 装饰器
    
    @controller(url='/api/test')
    class TestController:
        @get_api(url='')  # ✅ 正确！使用装饰器
        def get_data(self):
            return {"message": "Hello"}

---

❌ 错误方式2：方法名不规范
    
    @controller(url='/api/test')
    class TestController:
        @get_api(url='')
        def get(self):  # ⚠️ 方法名应该更具描述性
            return {"data": []}

✅ 正确方式：使用描述性的方法名
    
    @controller(url='/api/test')
    class TestController:
        @get_api(url='')
        def list_items(self):  # ✅ 清晰的方法名
            return {"data": []}
        
        @get_api(url='/{item_id}')
        def get_item(self, item_id):  # ✅ 清晰的方法名
            return {"id": item_id}

---

✅ 完整示例：RESTful API

    @controller(url='/api/products')
    class ProductController:
        product_service: ProductService = Inject()
        
        @get_api(url='')  # GET /api/products
        def list_products(self):
            products = self.product_service.get_all()
            return {'products': products}
        
        @get_api(url='/{product_id}')  # GET /api/products/123
        def get_product(self, product_id):
            product = self.product_service.get_by_id(product_id)
            return {'product': product}
        
        @post_api(url='', body_params=['name', 'price'])  # POST /api/products
        def create_product(self, name, price):
            product = self.product_service.create(name, price)
            return {'created': True, 'product': product}
        
        @put_api(url='/{product_id}', body_params=['name', 'price'])  # PUT /api/products/123
        def update_product(self, product_id, name, price):
            product = self.product_service.update(product_id, name, price)
            return {'updated': True, 'product': product}
        
        @delete_api(url='/{product_id}')  # DELETE /api/products/123
        def delete_product(self, product_id):
            self.product_service.delete(product_id)
            return {'deleted': True, 'id': product_id}
""")


if __name__ == '__main__':
    try:
        # 测试正确用法
        success = test_correct_controller_usage()
        
        # 显示常见错误
        show_common_mistakes()
        
        if success:
            logger.info("\n✅ 测试通过！现在你知道如何正确使用 Controller 了")
        else:
            logger.error("\n❌ 测试失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ 测试出错: {e}", exc_info=True)
        sys.exit(1)

