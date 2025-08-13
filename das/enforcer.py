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
import os
import fnmatch
import json
import traceback
import time
import uuid
from datetime import datetime, timezone

# Configure logging for violation tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("das.enforcer")

# ---------------------------------------------------------------------------
# Core Classes - TechSpec TS-DAS-001 Implementation
# ---------------------------------------------------------------------------

class DASError(Exception):
    """Base exception para DAS Enforcer operations"""
    pass

class PermissionError(DASError):
    """Agente no tiene permisos para operación solicitada"""
    def __init__(self, agent_name: str, scope: str, operation: str):
        self.agent_name = agent_name
        self.scope = scope
        self.operation = operation
        super().__init__(f"Permission denied: {agent_name} cannot {operation} {scope}")

class AgentNotFoundError(DASError):
    """Agente no configurado en el sistema"""
    pass

class EnforcementError(DASError):
    """Error general en enforcement de políticas"""
    pass

class DASEnforcer:
    """Technical enforcement system for DAS agent permissions"""
    
    def __init__(self, agents_dir: str = "agents", project_root: str = None):
        """Initialize enforcer with agent configurations directory"""
        self.agents_dir = Path(agents_dir)
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.permissions_cache = {}
        self.audit_log = []
        self._ensure_agents_dir()
        self._init_protected_paths()
        
        # Initialize TechSpec components
        self.permission_validator = PermissionValidator(self)
        self.filesystem_protector = FilesystemProtector(self)
        self.audit_logger = AuditLogger(self)
    
    def _ensure_agents_dir(self):
        """Validate agents directory exists"""
        if not self.agents_dir.exists():
            raise ValueError(f"Agents directory not found: {self.agents_dir}")
    
    def _init_protected_paths(self):
        """Initialize mapping between PMS scopes and filesystem paths"""
        self.protected_paths = {
            'blueprint': [
                'docs/02_blueprint/**/*',
                'docs/blueprint.yaml',
                'docs/blueprint.md'
            ],
            'project_charter': [
                'docs/01_ProjectCharter/**/*',
                'docs/ProjectCharter.md'
            ],
            'project_status': [
                'memory/project_status.md'
            ],
            'backlog_f*': [
                'docs/05_backlog/backlog_f*.yaml'
            ],
            'backlog_f0': [
                'docs/05_backlog/backlog_f0.yaml'
            ],
            'backlog_f1': [
                'docs/05_backlog/backlog_f1.yaml'
            ],
            'backlog_f2': [
                'docs/05_backlog/backlog_f2.yaml'
            ],
            'blueprint_changes': [
                'docs/blueprint_changes.csv'
            ],
            'techspecs': [
                'docs/03_TechSpecs/**/*.md'
            ]
        }
    
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
    
    def _path_matches_scope(self, file_path: str, scope_pattern: str) -> bool:
        """Check if file path is protected by scope pattern
        
        Args:
            file_path: Absolute or relative file path
            scope_pattern: PMS scope pattern (e.g., 'blueprint', 'backlog_f*')
            
        Returns:
            True if path is protected by this scope
        """
        # Convert absolute path to relative from project root
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            try:
                rel_path = path_obj.relative_to(self.project_root)
            except ValueError:
                # Path not under project root
                return False
        else:
            rel_path = path_obj
        
        # Get protected path patterns for this scope
        if scope_pattern not in self.protected_paths:
            # Handle wildcard scopes like 'backlog_f*'
            for scope_key in self.protected_paths:
                if self._scope_matches(scope_pattern, scope_key):
                    path_patterns = self.protected_paths[scope_key]
                    break
            else:
                return False
        else:
            path_patterns = self.protected_paths[scope_pattern]
        
        # Check if file path matches any protected pattern
        rel_path_str = str(rel_path).replace('\\', '/')  # Normalize separators
        for pattern in path_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True
        
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
    
    def validate_file_access(
        self, 
        agent_id: str, 
        operation: Literal['read', 'write'], 
        file_path: str
    ) -> bool:
        """Validate if agent has permission to access file path
        
        Args:
            agent_id: Agent requesting access
            operation: Type of operation ("read" or "write") 
            file_path: File path being accessed
            
        Returns:
            True if permission granted, False if denied
        """
        try:
            permissions = self.load_agent_permissions(agent_id)
        except ValueError:
            # Agent not found - deny by default
            return False
        
        # Skip enforcement if disabled for this agent
        if not permissions['enforcement_enabled']:
            return True
        
        # Check all scopes that could protect this file
        for scope_pattern in self.protected_paths.keys():
            if self._path_matches_scope(file_path, scope_pattern):
                # File is protected by this scope - check permissions
                if operation == "read":
                    allowed_scopes = permissions['read_scopes'] + permissions['write_scopes']
                elif operation == "write": 
                    allowed_scopes = permissions['write_scopes']
                else:
                    return False
                
                # Check if agent has permission for this scope
                for allowed_pattern in allowed_scopes:
                    if self._scope_matches(scope_pattern, allowed_pattern):
                        return True
                
                # File is protected but agent lacks permission
                return False
        
        # File is not in any protected path - allow access
        return True
    
    def log_violation(self, agent_id: str, operation: str, scope: str, message: str):
        """Log permission violation for audit trail"""
        logger.warning(f"PERMISSION_VIOLATION: {agent_id} tried {operation} on '{scope}' - {message}")


class PermissionValidator:
    """Validación granular de permisos por agente y scope"""
    
    def __init__(self, enforcer: DASEnforcer):
        self.enforcer = enforcer
    
    def validate_read_permission(self, agent_name: str, scope: str) -> tuple[bool, str]:
        """Valida si agente puede leer scope específico"""
        try:
            agent_config = self.enforcer.load_agent_permissions(agent_name)
        except ValueError:
            return False, f"Agente '{agent_name}' no configurado"
        
        read_scopes = agent_config.get('read_scopes', [])
        write_scopes = agent_config.get('write_scopes', [])  # Write implies read
        allowed_scopes = read_scopes + write_scopes
        
        # Soporte para wildcards (backlog_f*)
        for allowed_scope in allowed_scopes:
            if self.enforcer._scope_matches(scope, allowed_scope):
                return True, f"Permiso {'wildcard' if '*' in allowed_scope else 'directo'} concedido"
        
        return False, f"Agente '{agent_name}' no tiene permiso read para '{scope}'"
    
    def validate_write_permission(self, agent_name: str, scope: str) -> tuple[bool, str]:
        """Valida si agente puede escribir scope específico"""
        try:
            agent_config = self.enforcer.load_agent_permissions(agent_name)
        except ValueError:
            return False, f"Agente '{agent_name}' no configurado"
        
        write_scopes = agent_config.get('write_scopes', [])
        
        # Validación similar a read con wildcards
        for allowed_scope in write_scopes:
            if self.enforcer._scope_matches(scope, allowed_scope):
                return True, f"Permiso write {'wildcard' if '*' in allowed_scope else 'directo'} concedido"
        
        return False, f"Agente '{agent_name}' no tiene permiso write para '{scope}'"
    
    def get_agent_permissions(self, agent_name: str) -> dict:
        """Retorna configuración completa de permisos para agente"""
        try:
            agent_config = self.enforcer.load_agent_permissions(agent_name)
            return {
                'read_scopes': agent_config.get('read_scopes', []),
                'write_scopes': agent_config.get('write_scopes', []),
                'mode': agent_config.get('mode', 'update_single'),
                'enforcement_enabled': agent_config.get('enforcement_enabled', False),
                'strict_mode': agent_config.get('strict_mode', False),
                'log_violations': agent_config.get('log_violations', True)
            }
        except ValueError:
            return {}


class FilesystemProtector:
    """Protección a nivel de filesystem usando patterns de paths"""
    
    def __init__(self, enforcer: DASEnforcer):
        self.enforcer = enforcer
    
    def validate_file_access(self, agent_name: str, file_path: str, operation: str) -> tuple[bool, str]:
        """Valida acceso a path específico del filesystem"""
        file_path_obj = Path(file_path)
        
        # Determinar scope basado en path
        scope = self._path_to_scope(file_path_obj)
        if not scope:
            return True, f"Path '{file_path}' no está protegido por DAS"
        
        # Validar permisos del agente para el scope
        if operation.lower() == 'read':
            return self.enforcer.permission_validator.validate_read_permission(agent_name, scope)
        elif operation.lower() == 'write':
            return self.enforcer.permission_validator.validate_write_permission(agent_name, scope)
        else:
            return False, f"Operación '{operation}' no reconocida"
    
    def _path_to_scope(self, file_path: Path) -> str | None:
        """Mapea path de archivo a scope correspondiente"""
        file_path_str = str(file_path).replace('\\', '/')
        
        # Check against protected paths patterns
        for scope, path_patterns in self.enforcer.protected_paths.items():
            for pattern in path_patterns:
                # Handle wildcard patterns
                if '**' in pattern:
                    base_pattern = pattern.replace('/**/*', '')
                    if file_path_str.startswith(base_pattern):
                        return scope
                elif '*' in pattern:
                    if fnmatch.fnmatch(file_path_str, pattern):
                        return scope
                elif file_path_str.endswith(pattern) or pattern in file_path_str:
                    return scope
        
        return None
    
    def is_protected_path(self, file_path: str) -> bool:
        """Verifica si path está bajo protección DAS"""
        return self._path_to_scope(Path(file_path)) is not None


class AuditLogger:
    """Sistema de auditoría completo para compliance y debugging"""
    
    def __init__(self, enforcer: DASEnforcer):
        self.enforcer = enforcer
        self.log_file = enforcer.project_root / 'memory' / 'das_audit.log'
        self.session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_access_attempt(self, agent_name: str, scope: str, operation: str, 
                          success: bool, details: str = "") -> None:
        """Log completo de intento de acceso"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'session_id': self.session_id,
            'agent_name': agent_name,
            'scope': scope,
            'operation': operation,
            'success': success,
            'details': details,
            'stack_trace': traceback.format_stack() if not success else None
        }
        
        # Append al log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{json.dumps(log_entry)}\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
        
        # Mantener en memoria para queries rápidas
        self.enforcer.audit_log.append(log_entry)
        
        # Limpiar log en memoria si crece mucho
        if len(self.enforcer.audit_log) > 1000:
            self.enforcer.audit_log = self.enforcer.audit_log[-500:]
    
    def get_violation_summary(self) -> dict:
        """Resumen de violaciones para alertas"""
        violations = [entry for entry in self.enforcer.audit_log if not entry['success']]
        
        return {
            'total_violations': len(violations),
            'agents_with_violations': list(set(v['agent_name'] for v in violations)),
            'most_violated_scopes': self._count_violations_by_scope(violations),
            'recent_violations': violations[-10:] if violations else []
        }
    
    def _count_violations_by_scope(self, violations: list) -> dict:
        """Cuenta violaciones por scope para identificar problemas"""
        from collections import Counter
        scope_counts = Counter(v['scope'] for v in violations)
        return dict(scope_counts.most_common(5))

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
        
        # Log via audit system
        enforcer.audit_logger.log_access_attempt(agent_id, scope, operation, False, violation_msg)
        
        if log_violations:
            enforcer.log_violation(agent_id, operation, scope, violation_msg)
        
        if strict_mode:
            raise PermissionError(agent_id, scope, operation)
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
            result = pms_core.load(scope=scope)
            # Log successful operation
            enforcer.audit_logger.log_access_attempt(agent_id, scope, operation, True, "Load successful")
            return result
        
        elif operation == "save":
            if payload is None:
                raise ValueError("Payload required for save operations")
            
            # Use agent's default mode if not specified
            if mode is None:
                agent_config = enforcer.load_agent_permissions(agent_id)
                mode = agent_config.get('mode', 'update_single')
            
            result = pms_core.save(scope=scope, payload=payload, mode=mode)
            # Log successful operation
            enforcer.audit_logger.log_access_attempt(agent_id, scope, operation, True, f"Save successful (mode: {mode})")
            return result
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
            
    except ImportError as e:
        # Log the error
        enforcer.audit_logger.log_access_attempt(agent_id, scope, operation, False, f"Import error: {e}")
        raise RuntimeError(f"Failed to import pms_core: {e}")
    except Exception as e:
        # Log any other errors during operation
        enforcer.audit_logger.log_access_attempt(agent_id, scope, operation, False, f"Operation failed: {e}")
        raise

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
# Advanced Permission Management - TS-DAS-002 Implementation
# ---------------------------------------------------------------------------

def reload_agent_configs() -> None:
    """Force reload of all agent configurations"""
    enforcer = get_enforcer()
    enforcer.permissions_cache.clear()
    logger.info("Agent configurations cache cleared - will reload on next access")

def list_all_agents() -> List[str]:
    """List all available agent configurations"""
    enforcer = get_enforcer()
    agent_files = list(enforcer.agents_dir.glob("*.yaml"))
    return [agent_file.stem for agent_file in agent_files]

def get_agent_permissions_summary() -> Dict[str, Dict[str, Any]]:
    """Get comprehensive summary of all agent permissions"""
    summary = {}
    
    for agent_name in list_all_agents():
        try:
            permissions = validate_agent_config(agent_name)
            summary[agent_name] = permissions
        except Exception as e:
            summary[agent_name] = {"error": str(e)}
    
    return summary

def validate_scope_access(agent_name: str, scope: str, operation: str) -> Dict[str, Any]:
    """Detailed validation of scope access with explanation"""
    enforcer = get_enforcer()
    
    try:
        # Get agent permissions
        permissions = enforcer.load_agent_permissions(agent_name)
        
        # Determine allowed scopes
        if operation == "load":
            allowed_scopes = permissions['read_scopes'] + permissions['write_scopes']
        elif operation == "save":
            allowed_scopes = permissions['write_scopes']
        else:
            return {
                "allowed": False,
                "reason": f"Invalid operation: {operation}",
                "details": {}
            }
        
        # Check exact match first
        if scope in allowed_scopes:
            return {
                "allowed": True,
                "reason": "Direct scope match",
                "match_type": "exact",
                "matched_pattern": scope,
                "details": {
                    "agent": agent_name,
                    "scope": scope,
                    "operation": operation,
                    "enforcement_enabled": permissions['enforcement_enabled']
                }
            }
        
        # Check wildcard matches
        for pattern in allowed_scopes:
            if pattern.endswith('*') and enforcer._scope_matches(scope, pattern):
                return {
                    "allowed": True,
                    "reason": "Wildcard pattern match",
                    "match_type": "wildcard",
                    "matched_pattern": pattern,
                    "details": {
                        "agent": agent_name,
                        "scope": scope,
                        "operation": operation,
                        "enforcement_enabled": permissions['enforcement_enabled']
                    }
                }
        
        return {
            "allowed": False,
            "reason": f"No matching scope found for '{scope}'",
            "details": {
                "agent": agent_name,
                "scope": scope,
                "operation": operation,
                "allowed_scopes": allowed_scopes,
                "enforcement_enabled": permissions['enforcement_enabled']
            }
        }
        
    except ValueError as e:
        return {
            "allowed": False,
            "reason": f"Agent not found: {e}",
            "details": {}
        }

def audit_agent_activity(agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent activity for specific agent from audit log"""
    enforcer = get_enforcer()
    
    agent_activities = [
        entry for entry in enforcer.audit_log 
        if entry['agent_name'] == agent_name
    ]
    
    # Sort by timestamp (most recent first) and limit
    agent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return agent_activities[:limit]

def get_permission_matrix() -> Dict[str, Dict[str, str]]:
    """Generate permission matrix for all agents and scopes"""
    agents = list_all_agents()
    
    # Get all unique scopes from memory_index
    try:
        import pms_core
        memory_index = pms_core._load_memory_index()
        scopes = list(memory_index.get('scopes', {}).keys())
    except:
        # Fallback to common scopes
        scopes = ['blueprint', 'project_status', 'backlog_f1', 'backlog_f2', 'techspecs', 'blueprint_changes']
    
    matrix = {}
    
    for agent in agents:
        matrix[agent] = {}
        for scope in scopes:
            try:
                # Check read permission
                can_read = test_permission(agent, 'load', scope)
                can_write = test_permission(agent, 'save', scope)
                
                if can_read and can_write:
                    matrix[agent][scope] = 'RW'
                elif can_read:
                    matrix[agent][scope] = 'R-'
                elif can_write:
                    matrix[agent][scope] = '-W'  # Unlikely but possible
                else:
                    matrix[agent][scope] = '--'
                    
            except Exception:
                matrix[agent][scope] = 'ERR'
    
    return matrix

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

def validate_file_access(agent_id: str, operation: str, file_path: str) -> bool:
    """Validate if agent can access file path
    
    Args:
        agent_id: Agent requesting access
        operation: "read" or "write"
        file_path: File path to validate
        
    Returns:
        True if access allowed, False if denied
        
    Raises:
        PermissionError: If access denied in strict mode
    """
    enforcer = get_enforcer()
    has_permission = enforcer.validate_file_access(agent_id, operation, file_path)
    
    if not has_permission:
        try:
            agent_config = enforcer.load_agent_permissions(agent_id)
            strict_mode = agent_config.get('strict_mode', True)
            log_violations = agent_config.get('log_violations', True)
        except ValueError:
            strict_mode = True
            log_violations = True
        
        violation_msg = f"Agent '{agent_id}' denied {operation} access to file '{file_path}'"
        
        if log_violations:
            enforcer.log_violation(agent_id, operation, file_path, violation_msg)
        
        if strict_mode:
            raise PermissionError(violation_msg)
    
    return has_permission

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