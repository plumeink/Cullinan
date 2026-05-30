# -*- coding: utf-8 -*-
"""
Tests for configuration management.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

from cullinan.config import (
    CullinanConfig,
    get_config,
    configure,
)


class TestCullinanConfig(unittest.TestCase):
    """Test CullinanConfig class."""
    
    def setUp(self):
        """Create a fresh config instance for each test."""
        self.config = CullinanConfig()
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CullinanConfig()
        
        self.assertEqual(config.user_packages, [])
        self.assertIsNone(config.project_root)
        self.assertFalse(config.verbose)
        self.assertTrue(config.auto_scan)
        self.assertIn('test', config.exclude_packages)
    
    def test_add_user_package(self):
        """Test adding user packages."""
        self.config.add_user_package('myapp')
        self.assertIn('myapp', self.config.user_packages)
        
        # Adding same package twice should not duplicate
        self.config.add_user_package('myapp')
        self.assertEqual(self.config.user_packages.count('myapp'), 1)
    
    def test_set_project_root(self):
        """Test setting project root."""
        self.config.set_project_root('/path/to/project')
        self.assertTrue(self.config.project_root.endswith('project'))
    
    def test_set_verbose(self):
        """Test setting verbose flag."""
        self.config.set_verbose(True)
        self.assertTrue(self.config.verbose)
        
        self.config.set_verbose(False)
        self.assertFalse(self.config.verbose)
    
    def test_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            'user_packages': ['app1', 'app2'],
            'project_root': '/test/root',
            'verbose': True,
            'auto_scan': False,
            'exclude_packages': ['test', 'build']
        }
        
        self.config.from_dict(config_dict)
        
        self.assertEqual(self.config.user_packages, ['app1', 'app2'])
        self.assertEqual(self.config.project_root, '/test/root')
        self.assertTrue(self.config.verbose)
        self.assertFalse(self.config.auto_scan)
        self.assertEqual(self.config.exclude_packages, ['test', 'build'])
    
    def test_to_dict(self):
        """Test exporting configuration to dictionary."""
        self.config.user_packages = ['myapp']
        self.config.project_root = '/test'
        self.config.verbose = True
        
        config_dict = self.config.to_dict()
        
        self.assertEqual(config_dict['user_packages'], ['myapp'])
        self.assertEqual(config_dict['project_root'], '/test')
        self.assertTrue(config_dict['verbose'])


class TestConfigureFunction(unittest.TestCase):
    """Test the configure function."""
    
    def test_configure_with_user_packages(self):
        """Test configure with user packages."""
        result = configure(user_packages=['test_app'], verbose=False)
        
        self.assertIsInstance(result, CullinanConfig)
        self.assertIn('test_app', result.user_packages)
    
    def test_configure_verbose(self):
        """Test configure with verbose flag."""
        result = configure(verbose=True)
        self.assertTrue(result.verbose)
    
    def test_configure_auto_scan(self):
        """Test configure with auto_scan flag."""
        result = configure(auto_scan=False)
        self.assertFalse(result.auto_scan)
    
    def test_configure_exclude_packages(self):
        """Test configure with custom exclude packages."""
        result = configure(exclude_packages=['custom_exclude'])
        self.assertEqual(result.exclude_packages, ['custom_exclude'])
    
    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the global config instance."""
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same object
        self.assertIs(config1, config2)


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation and edge cases."""
    
    def test_empty_user_packages(self):
        """Test with empty user packages."""
        config = CullinanConfig()
        config.from_dict({'user_packages': []})
        self.assertEqual(config.user_packages, [])
    
    def test_none_project_root(self):
        """Test with None project root."""
        config = CullinanConfig()
        config.from_dict({'project_root': None})
        self.assertIsNone(config.project_root)
    
    def test_partial_config_dict(self):
        """Test from_dict with partial configuration."""
        config = CullinanConfig()
        config.from_dict({'verbose': True})
        
        # Should update only specified fields
        self.assertTrue(config.verbose)
        # Other fields should remain default
        self.assertEqual(config.user_packages, [])


class TestExcludePackages(unittest.TestCase):
    """Test exclude packages functionality."""
    
    def test_default_exclude_packages(self):
        """Test default exclude packages list."""
        config = CullinanConfig()
        
        # Should have common directories to exclude
        self.assertIn('test', config.exclude_packages)
        self.assertIn('tests', config.exclude_packages)
        self.assertIn('__pycache__', config.exclude_packages)
        self.assertIn('.git', config.exclude_packages)
    
    def test_custom_exclude_packages(self):
        """Test setting custom exclude packages."""
        config = CullinanConfig()
        config.exclude_packages = ['custom1', 'custom2']
        
        self.assertEqual(config.exclude_packages, ['custom1', 'custom2'])


class TestProjectRootDetection(unittest.TestCase):
    """Test project root detection."""
    
    def test_project_root_absolute_path(self):
        """Test that project root is converted to absolute path."""
        config = CullinanConfig()
        config.set_project_root('.')
        
        # Should be converted to absolute path
        self.assertTrue(os.path.isabs(config.project_root))
    
    def test_project_root_with_relative_path(self):
        """Test project root with relative path."""
        config = CullinanConfig()
        
        # Use current directory
        cwd = os.getcwd()
        config.set_project_root(cwd)
        
        self.assertEqual(config.project_root, cwd)


if __name__ == '__main__':
    unittest.main()
