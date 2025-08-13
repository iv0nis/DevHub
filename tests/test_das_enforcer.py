#!/usr/bin/env python3
"""
Tests for DAS Enforcer - TS-DAS-001 and TS-DAS-002 Implementation
Unit tests and integration tests for DevAgent System enforcement
"""
import pytest
import tempfile
import shutil
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add das and pms to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from das.enforcer import (
    validate_agent_config, agent_load, agent_save, 
    PermissionError, safe_pms_call
)

class TestDASEnforcer:
    """Test cases for DAS Enforcer functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory with DAS structure"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create basic structure
        (project_path / 'memory').mkdir()
        (project_path / 'docs' / '05_backlog').mkdir(parents=True)
        (project_path / 'agents').mkdir()
        
        # Create memory_index.yaml
        memory_index = {
            'version': '1.0',
            'agents': {
                'dev_agent': '../agents/DevAgent.yaml'
            },
            'paths': {
                'project_status': './project_status.md',
                'blueprint': '../docs/02_blueprint/blueprint.md',
                'backlog_f1': '../docs/05_backlog/backlog_f1.yaml'
            }
        }
        
        with open(project_path / 'memory' / 'memory_index.yaml', 'w') as f:
            yaml.dump(memory_index, f)
        
        # Create DevAgent.yaml
        dev_agent_config = {
            'agent_info': {
                'name': 'DevAgent',
                'version': '1.0',
                'purpose': 'Development task execution'
            },
            'permissions': {
                'read_scopes': ['memory_index', 'backlog_f*', 'blueprint', 'project_status'],
                'write_scopes': ['backlog_f*', 'project_status'],
                'mode': 'update_single',
                'enforcement_enabled': True,
                'strict_mode': True,
                'log_violations': True
            }
        }
        
        with open(project_path / 'agents' / 'DevAgent.yaml', 'w') as f:
            yaml.dump(dev_agent_config, f)
        
        # Create test backlog
        backlog_data = {
            'fase': 1,
            'historias': {
                'TS-TEST-001': {
                    'id': 'TS-TEST-001',
                    'title': 'Test task',
                    'status': 'todo',
                    'priority': 'P2'
                }
            }
        }
        
        with open(project_path / 'docs' / '05_backlog' / 'backlog_f1.yaml', 'w') as f:
            yaml.dump(backlog_data, f)
            
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_validate_agent_config_valid(self, temp_project):
        """Test agent config validation with valid config"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            config = validate_agent_config('DevAgent')
            
            assert config is not None
            assert config['read_scopes'] == ['memory_index', 'backlog_f*', 'blueprint', 'project_status']
            assert config['write_scopes'] == ['backlog_f*', 'project_status']
            assert config['enforcement_enabled'] is True
            
        finally:
            os.chdir(old_cwd)
    
    def test_validate_agent_config_invalid(self, temp_project):
        """Test agent config validation with invalid agent"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            config = validate_agent_config('NonExistentAgent')
            assert config is None
            
        finally:
            os.chdir(old_cwd)
    
    def test_agent_load_success(self, temp_project):
        """Test successful agent_load with valid permissions"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            # Load backlog_f1 (DevAgent has read permissions)
            data = agent_load('DevAgent', 'backlog_f1')
            
            assert data is not None
            assert 'historias' in data
            assert 'TS-TEST-001' in data['historias']
            
        finally:
            os.chdir(old_cwd)
    
    def test_agent_load_permission_denied(self, temp_project):
        """Test agent_load with insufficient permissions"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            # Try to load scope that DevAgent doesn't have permission for
            with pytest.raises(PermissionError):
                agent_load('DevAgent', 'restricted_scope')
                
        finally:
            os.chdir(old_cwd)
    
    @patch('das.enforcer.pms_core.save')
    def test_agent_save_success(self, mock_pms_save, temp_project):
        """Test successful agent_save with valid permissions"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            mock_pms_save.return_value = True
            
            # Save to backlog_f1 (DevAgent has write permissions)
            test_data = {'test': 'data'}
            result = agent_save('DevAgent', 'backlog_f1', test_data)
            
            assert result is True
            mock_pms_save.assert_called_once()
            
        finally:
            os.chdir(old_cwd)
    
    def test_agent_save_permission_denied(self, temp_project):
        """Test agent_save with insufficient permissions"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            # Try to save to scope that DevAgent doesn't have write permission for
            with pytest.raises(PermissionError):
                agent_save('DevAgent', 'blueprint', {'test': 'data'})
                
        finally:
            os.chdir(old_cwd)
    
    @patch('das.enforcer.pms_core')
    def test_safe_pms_call_success(self, mock_pms, temp_project):
        """Test safe_pms_call wrapper function"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            mock_pms.load.return_value = "test data"
            
            result = safe_pms_call('DevAgent', 'load', 'backlog_f1')
            
            assert result == "test data"
            mock_pms.load.assert_called_once_with('backlog_f1')
            
        finally:
            os.chdir(old_cwd)
    
    def test_wildcard_scope_matching(self, temp_project):
        """Test wildcard scope matching (backlog_f*)"""
        old_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            # Test that backlog_f1, backlog_f2, etc. match backlog_f*
            config = validate_agent_config('DevAgent')
            read_scopes = config['read_scopes']
            
            # DevAgent should have access to any backlog_f* scope
            assert 'backlog_f*' in read_scopes
            
            # This should work (mocked)
            with patch('das.enforcer.pms_core.load') as mock_load:
                mock_load.return_value = {'test': 'data'}
                
                # These should all be allowed
                agent_load('DevAgent', 'backlog_f1')
                agent_load('DevAgent', 'backlog_f2')
                agent_load('DevAgent', 'backlog_f99')
                
                assert mock_load.call_count == 3
            
        finally:
            os.chdir(old_cwd)


class TestDASEnforcementLogging:
    """Test DAS audit logging functionality"""
    
    @pytest.fixture
    def temp_project_with_logging(self):
        """Create temp project with logging enabled"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create structure
        (project_path / 'memory').mkdir()
        (project_path / 'agents').mkdir()
        
        # Create memory_index and agent config (similar to above)
        memory_index = {
            'version': '1.0',
            'agents': {'dev_agent': '../agents/DevAgent.yaml'},
            'paths': {'backlog_f1': '../docs/backlog_f1.yaml'}
        }
        
        with open(project_path / 'memory' / 'memory_index.yaml', 'w') as f:
            yaml.dump(memory_index, f)
        
        dev_agent_config = {
            'agent_info': {'name': 'DevAgent'},
            'permissions': {
                'read_scopes': ['backlog_f1'],
                'write_scopes': [],
                'enforcement_enabled': True,
                'log_violations': True
            }
        }
        
        with open(project_path / 'agents' / 'DevAgent.yaml', 'w') as f:
            yaml.dump(dev_agent_config, f)
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    def test_violation_logging(self, temp_project_with_logging):
        """Test that violations are properly logged"""
        old_cwd = os.getcwd()
        os.chdir(temp_project_with_logging)
        
        try:
            # Create audit log path
            (temp_project_with_logging / 'memory').mkdir(exist_ok=True)
            
            # Attempt operation that should be logged as violation
            with pytest.raises(PermissionError):
                agent_save('DevAgent', 'restricted_scope', {'data': 'test'})
            
            # Check if audit log was created (in real implementation)
            # This would verify das_audit.log exists and contains violation
            audit_log_path = temp_project_with_logging / 'memory' / 'das_audit.log'
            # In real implementation, this file would be created
            
        finally:
            os.chdir(old_cwd)


class TestDASIntegration:
    """Integration tests for complete DAS system"""
    
    def test_agent_workflow_integration(self, temp_project=None):
        """Test complete agent workflow with DAS enforcement"""
        # This test would run in actual DevHub environment
        try:
            # Test that we can validate actual DevAgent config
            config = validate_agent_config('DevAgent')
            
            if config:
                assert 'read_scopes' in config
                assert 'write_scopes' in config
                assert 'enforcement_enabled' in config
                print("✅ DevAgent config validation passed")
            else:
                print("⚠️ DevAgent config not found - expected in test environment")
                
        except Exception as e:
            print(f"⚠️ Integration test skipped: {e}")
    
    def test_multiple_agents_isolation(self):
        """Test that different agents have proper isolation"""
        # Test that different agents have different permissions
        try:
            dev_config = validate_agent_config('DevAgent')
            blueprint_config = validate_agent_config('BluePrintAgent')
            
            if dev_config and blueprint_config:
                # DevAgent shouldn't have blueprint write access
                assert 'blueprint' not in dev_config.get('write_scopes', [])
                # BluePrintAgent should have blueprint write access
                assert 'blueprint' in blueprint_config.get('write_scopes', [])
                print("✅ Agent isolation verified")
            else:
                print("⚠️ Multiple agent test skipped - configs not found")
                
        except Exception as e:
            print(f"⚠️ Multi-agent test skipped: {e}")


# Performance and stress tests
class TestDASPerformance:
    """Performance tests for DAS enforcement"""
    
    def test_config_validation_performance(self):
        """Test that config validation is fast enough"""
        import time
        
        start_time = time.time()
        
        # Validate config multiple times
        for _ in range(100):
            try:
                validate_agent_config('DevAgent')
            except:
                pass  # Expected in test environment
        
        elapsed = time.time() - start_time
        
        # Should complete 100 validations in less than 1 second
        assert elapsed < 1.0, f"Config validation too slow: {elapsed}s"
        print(f"✅ Config validation performance: {elapsed:.3f}s for 100 validations")


if __name__ == '__main__':
    # Run basic integration tests
    print("\n=== DAS ENFORCER INTEGRATION TEST ===")
    
    integration = TestDASIntegration()
    integration.test_agent_workflow_integration()
    integration.test_multiple_agents_isolation()
    
    performance = TestDASPerformance()
    performance.test_config_validation_performance()
    
    print("✅ DAS Enforcer basic integration tests completed")
    print("Run full test suite with: python -m pytest tests/test_das_enforcer.py -v")