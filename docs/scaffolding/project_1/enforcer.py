# -*- coding: utf-8 -*-
"""das_enforcer – DAS Permission Enforcement System

Implements technical enforcement of agent permissions as specified in das.md.
Provides secure wrapper around pms_core operations with agent-based access control.

Key features:
- Agent permission validation from YAML configs
- Safe wrappers for pms_core.load() and pms_core.save()
- Wildcard scope matching (e.g., "backlog_f*")
- Strict mode vs warning mode for violations
- Audit logging for security monitoring

Usage:
    from das.enforcer import agent_load, agent_save
    
    # Automatically validates permissions
    data = agent_load("dev_agent", "backlog_f1")  
    agent_save("dev_agent", "backlog_f1", updated_data)
"""
from __future__ import annotations

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Literal, Any, Optional

# Configure logging for violation tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("das.enforcer")

# ---------------------------------------------------------------------------
# Core Classes
# ---------------------------------------------------------------------------

class PermissionError(Exception):
    """Raised when agent attempts unauthorized operation"""
    pass

class DASEnforcer:
    """Technical enforcement system for DAS agent permissions"""
    
    def __init__(self, agents_dir: str = "das/agents"):
        """Initialize enforcer with agent configurations directory"""
        self.agents_dir = Path(agents_dir)
        self.permissions_cache = {}
        self._ensure_agents_dir()
    
    def _ensure_agents_dir(self):
        """Validate agents directory exists"""
        if not self.agents_dir.exists():
            raise ValueError(f"Agents directory not found: {self.agents_dir}")
    
    def load_agent_permissions(self, agent_id: str) -> Dict[str, Any]:
        """Load and cache agent permissions from YAML config
        
        Args:
            agent_id: Agent identifier (e.g., "dev_agent", "blueprint_agent")
            
        Returns:
            Dict with read_scopes, write_scopes, mode, enforcement settings
            
        Raises:
            ValueError: If agent config file not found
        """
        if agent_id not in self.permissions_cache:
            agent_file = self.agents_dir / f"{agent_id}.yaml"
            
            if not agent_file.exists():
                raise ValueError(f"Agent config not found: {agent_file}")
            
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {agent_file}: {e}")
            
            # Extract permission scopes with defaults
            pms_scopes = config.get('pms_scopes', {})
            enforcement = config.get('enforcement', {})
            
            self.permissions_cache[agent_id] = {
                'read_scopes': pms_scopes.get('read', []),
                'write_scopes': pms_scopes.get('write', []),
                'mode': pms_scopes.get('mode', 'update_single'),
                'enforcement_enabled': enforcement.get('enabled', True),
                'strict_mode': enforcement.get('strict_mode', True),
                'log_violations': enforcement.get('log_violations', True)
            }
        
        return self.permissions_cache[agent_id]
    
    def _scope_matches(self, scope: str, allowed_pattern: str) -> bool:
        """Check if scope matches allowed pattern (supports wildcards)
        
        Args:
            scope: Actual scope being accessed (e.g., "backlog_f1")
            allowed_pattern: Pattern from agent config (e.g., "backlog_f*")
            
        Returns:
            True if scope is allowed by pattern
        """
        if scope == allowed_pattern:
            return True
        
        # Wildcard matching: "backlog_f*" matches "backlog_f1", "backlog_f2", etc.
        if allowed_pattern.endswith('*'):
            prefix = allowed_pattern[:-1]
            return scope.startswith(prefix)
        
        return False
    
    def validate_agent_permissions(
        self, 
        agent_id: str, 
        operation: Literal['load', 'save'], 
        scope: str
    ) -> bool:
        """Validate if agent has permission for operation on scope
        
        Args:
            agent_id: Agent requesting access
            operation: Type of operation ("load" or "save")
            scope: PMS scope being accessed
            
        Returns:
            True if permission granted, False if denied
            
        Raises:
            ValueError: If agent not found or invalid operation
        """
        try:
            permissions = self.load_agent_permissions(agent_id)
        except ValueError:
            # Agent not found - deny by default
            return False
        
        # Skip enforcement if disabled for this agent
        if not permissions['enforcement_enabled']:
            return True
        
        # Determine allowed scopes based on operation
        if operation == "load":
            # Read permission allows loading scopes from both read and write lists
            allowed_scopes = permissions['read_scopes'] + permissions['write_scopes']
        elif operation == "save":
            # Write permission required for saving
            allowed_scopes = permissions['write_scopes']
        else:
            raise ValueError(f"Invalid operation: {operation}")
        
        # Check if scope matches any allowed pattern
        for allowed_pattern in allowed_scopes:
            if self._scope_matches(scope, allowed_pattern):
                return True
        
        return False
    
    def log_violation(self, agent_id: str, operation: str, scope: str, message: str):
        """Log permission violation for audit trail"""
        logger.warning(f"PERMISSION_VIOLATION: {agent_id} tried {operation} on '{scope}' - {message}")

# ---------------------------------------------------------------------------
# Global instance and public API
# ---------------------------------------------------------------------------

# Global enforcer instance (singleton pattern)
_enforcer = None

def get_enforcer() -> DASEnforcer:
    """Get or create global enforcer instance"""
    global _enforcer
    if _enforcer is None:
        _enforcer = DASEnforcer()
    return _enforcer

def safe_pms_call(
    agent_id: str, 
    operation: Literal['load', 'save'], 
    scope: str, 
    payload: Any = None, 
    mode: Optional[str] = None
) -> Any:
    """Safe wrapper for pms_core operations with permission enforcement
    
    This is the main API that all agents should use instead of calling
    pms_core.load() and pms_core.save() directly.
    
    Args:
        agent_id: Identifier of requesting agent
        operation: "load" or "save"
        scope: PMS scope to access
        payload: Data to save (required for save operations)
        mode: Override default save mode (optional)
        
    Returns:
        Result from pms_core operation
        
    Raises:
        PermissionError: If agent lacks required permissions
        ValueError: If operation parameters invalid
    """
    enforcer = get_enforcer()
    
    # Validate permissions
    has_permission = enforcer.validate_agent_permissions(agent_id, operation, scope)
    
    if not has_permission:
        # Get agent config for enforcement settings
        try:
            agent_config = enforcer.load_agent_permissions(agent_id)
            log_violations = agent_config.get('log_violations', True)
            strict_mode = agent_config.get('strict_mode', True)
        except ValueError:
            # Agent not found - use strict defaults
            log_violations = True
            strict_mode = True
        
        violation_msg = f"Agent '{agent_id}' denied {operation} access to scope '{scope}'"
        
        if log_violations:
            enforcer.log_violation(agent_id, operation, scope, violation_msg)
        
        if strict_mode:
            raise PermissionError(violation_msg)
        else:
            logger.warning(f"PERMISSION_WARNING: {violation_msg} (continuing in non-strict mode)")
    
    # Permission granted - execute PMS-Core operation
    try:
        # Import here to avoid circular dependencies
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(__file__))
        sys.path.insert(0, project_root)
        import pms_core
        
        if operation == "load":
            return pms_core.load(scope=scope)
        
        elif operation == "save":
            if payload is None:
                raise ValueError("Payload required for save operations")
            
            # Use agent's default mode if not specified
            if mode is None:
                agent_config = enforcer.load_agent_permissions(agent_id)
                mode = agent_config.get('mode', 'update_single')
            
            return pms_core.save(scope=scope, payload=payload, mode=mode)
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
            
    except ImportError as e:
        raise RuntimeError(f"Failed to import pms_core: {e}")

# ---------------------------------------------------------------------------
# Convenience functions for agents
# ---------------------------------------------------------------------------

def agent_load(agent_id: str, scope: str) -> Any:
    """Convenience wrapper for loading data with permission validation
    
    Args:
        agent_id: Requesting agent identifier
        scope: PMS scope to load
        
    Returns:
        Loaded data from PMS
        
    Raises:
        PermissionError: If agent lacks read permission for scope
    """
    return safe_pms_call(agent_id, "load", scope)

def agent_save(
    agent_id: str, 
    scope: str, 
    payload: Any, 
    mode: Optional[str] = None
) -> Any:
    """Convenience wrapper for saving data with permission validation
    
    Args:
        agent_id: Requesting agent identifier
        scope: PMS scope to save to
        payload: Data to save
        mode: Override agent's default save mode (optional)
        
    Returns:
        Result from PMS save operation
        
    Raises:
        PermissionError: If agent lacks write permission for scope
    """
    return safe_pms_call(agent_id, "save", scope, payload, mode)

# ---------------------------------------------------------------------------
# Development and testing utilities
# ---------------------------------------------------------------------------

def validate_agent_config(agent_id: str) -> Dict[str, Any]:
    """Validate agent configuration and return parsed permissions
    
    Useful for debugging and testing agent setups.
    
    Args:
        agent_id: Agent to validate
        
    Returns:
        Parsed permissions dictionary
        
    Raises:
        ValueError: If agent config invalid
    """
    enforcer = get_enforcer()
    return enforcer.load_agent_permissions(agent_id)

def list_agent_permissions(agent_id: str) -> str:
    """Get human-readable summary of agent permissions
    
    Args:
        agent_id: Agent to examine
        
    Returns:
        Formatted permission summary
    """
    try:
        perms = validate_agent_config(agent_id)
        
        summary = f"Agent: {agent_id}\n"
        summary += f"Read scopes: {perms['read_scopes']}\n"
        summary += f"Write scopes: {perms['write_scopes']}\n"
        summary += f"Default mode: {perms['mode']}\n"
        summary += f"Enforcement: {'enabled' if perms['enforcement_enabled'] else 'disabled'}\n"
        summary += f"Strict mode: {'yes' if perms['strict_mode'] else 'no'}"
        
        return summary
        
    except ValueError as e:
        return f"Error loading agent {agent_id}: {e}"

def test_permission(agent_id: str, operation: str, scope: str) -> bool:
    """Test if agent would have permission for operation without executing it
    
    Args:
        agent_id: Agent to test
        operation: "load" or "save" 
        scope: Target scope
        
    Returns:
        True if permission would be granted
    """
    enforcer = get_enforcer()
    return enforcer.validate_agent_permissions(agent_id, operation, scope)

# ---------------------------------------------------------------------------
# Module testing - run with: python -m das.enforcer
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("DAS Enforcer - Permission Testing")
    print("=" * 40)
    
    # Test agent validation
    test_agents = ["dev_agent", "blueprint_agent", "qa_agent"]
    
    for agent in test_agents:
        print(f"\nTesting agent: {agent}")
        try:
            permissions = validate_agent_config(agent)
            print(f"✅ Config valid: {permissions}")
        except ValueError as e:
            print(f"❌ Config error: {e}")
    
    # Test permission scenarios
    test_cases = [
        ("dev_agent", "load", "blueprint"),
        ("dev_agent", "save", "blueprint"),
        ("dev_agent", "save", "backlog_f1"),
        ("blueprint_agent", "save", "blueprint"),
    ]
    
    print(f"\nPermission tests:")
    for agent_id, operation, scope in test_cases:
        allowed = test_permission(agent_id, operation, scope)
        status = "✅ ALLOWED" if allowed else "❌ DENIED"
        print(f"{status}: {agent_id} {operation} {scope}")