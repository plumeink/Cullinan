# -*- coding: utf-8 -*-
"""Enhanced Service base class for Cullinan framework.

Provides lifecycle management and dependency injection support
while maintaining backward compatibility with simple Service usage.
"""

import logging

logger = logging.getLogger(__name__)


class Service(object):
    """Enhanced base class for services with lifecycle support.
    
    Services can optionally implement lifecycle methods:
    - on_init(): Called after dependencies are injected
    - on_destroy(): Called during service shutdown
    
    Services can access injected dependencies via self.dependencies dict.
    
    Examples:
        # Simple service (backward compatible)
        @service
        class EmailService(Service):
            def send_email(self, to, subject, body):
                print(f"Sending email to {to}")
        
        # Service with dependencies
        @service(dependencies=['EmailService'])
        class UserService(Service):
            def on_init(self):
                self.email = self.dependencies['EmailService']
            
            def create_user(self, name):
                user = {'name': name}
                self.email.send_email(name, "Welcome", "Welcome!")
                return user
    """
    
    def __init__(self):
        """Initialize the service.
        
        Dependencies will be injected by the ServiceRegistry before on_init is called.
        """
        self.dependencies = {}
    
    def on_init(self):
        """Lifecycle hook called after service is created and dependencies are injected.
        
        Override this method to perform initialization that requires dependencies.
        """
        pass
    
    def on_destroy(self):
        """Lifecycle hook called when service is being destroyed.
        
        Override this method to perform cleanup (close connections, release resources, etc.).
        """
        pass
