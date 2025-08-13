# -*- coding: utf-8 -*-
"""DevHub Configuration Management System - TS-CONFIG-001

Multi-environment configuration management with type safety and validation.
Supports development, production, and testing environments with proper
environment-specific settings and secure handling of sensitive data.

Usage:
    from core.config import ConfigManager, get_config, DevHubConfig
    
    # Get configuration for current environment
    config = get_config()
    
    # Access environment-specific settings
    db_url = config.database.url
    api_key = config.security.api_key
    
    # Switch environments programmatically
    config_manager = ConfigManager()
    prod_config = config_manager.get_config('production')
"""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
from datetime import datetime

logger = logging.getLogger("devhub.config")

# ---------------------------------------------------------------------------
# Environment and Configuration Types
# ---------------------------------------------------------------------------

class Environment(Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    STAGING = "staging"

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str = "sqlite:///devhub.db"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    timeout: int = 30
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters"""
        return {
            'url': self.url,
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'echo': self.echo,
            'connect_timeout': self.timeout
        }

@dataclass
class SecurityConfig:
    """Security and authentication settings"""
    secret_key: str = "dev-secret-key-change-in-production"
    api_key: Optional[str] = None
    jwt_expiry_hours: int = 24
    password_min_length: int = 8
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30
    enable_cors: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    
    def is_secure(self) -> bool:
        """Check if security configuration is production-ready"""
        return (
            self.secret_key != "dev-secret-key-change-in-production" and
            len(self.secret_key) >= 32 and
            self.api_key is not None
        )

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False
    
    def get_log_level(self) -> int:
        """Get numeric log level"""
        return getattr(logging, self.level.upper(), logging.INFO)

@dataclass
class PMSConfig:
    """PMS (Persistent Memory System) configuration"""
    project_root: str = "."
    memory_dir: str = "memory"
    backup_dir: str = "backups"
    max_backups: int = 10
    enable_integrity_checks: bool = True
    enable_transactions: bool = True
    auto_commit: bool = False
    validation_on_load: bool = True
    
    def get_memory_path(self) -> Path:
        """Get full path to memory directory"""
        return Path(self.project_root) / self.memory_dir
    
    def get_backup_path(self) -> Path:
        """Get full path to backup directory"""
        return Path(self.project_root) / self.backup_dir

@dataclass
class DASConfig:
    """DAS (DevAgent System) configuration"""
    agents_dir: str = "agents"
    audit_log_file: str = "memory/das_audit.log"
    enable_enforcement: bool = True
    enable_audit_logging: bool = True
    max_concurrent_agents: int = 10
    agent_timeout_seconds: int = 300
    permission_cache_ttl_minutes: int = 60
    
    def get_agents_path(self) -> Path:
        """Get full path to agents directory"""
        return Path(self.agents_dir)
    
    def get_audit_log_path(self) -> Path:
        """Get full path to audit log file"""
        return Path(self.audit_log_file)

@dataclass
class EventConfig:
    """Event System configuration"""
    max_concurrent_events: int = 100
    event_history_size: int = 1000
    enable_persistence: bool = False
    event_log_file: Optional[str] = None
    subscriber_timeout_seconds: int = 30
    enable_global_error_handler: bool = True
    
    def get_event_log_path(self) -> Optional[Path]:
        """Get event log file path if persistence enabled"""
        return Path(self.event_log_file) if self.event_log_file else None

@dataclass
class WebConfig:
    """Web dashboard configuration"""
    host: str = "localhost"
    port: int = 3000
    debug: bool = False
    enable_hot_reload: bool = False
    api_base_url: str = "/api"
    static_files_dir: str = "static"
    template_dir: str = "templates"
    
    def get_server_url(self) -> str:
        """Get complete server URL"""
        return f"http://{self.host}:{self.port}"

@dataclass
class CLIConfig:
    """CLI tool configuration"""
    default_project_type: str = "default"
    template_dir: str = "docs/doc_templates"
    enable_colors: bool = True
    confirm_destructive_actions: bool = True
    max_validation_errors: int = 50
    default_output_format: str = "table"

# ---------------------------------------------------------------------------
# Main Configuration Class
# ---------------------------------------------------------------------------

@dataclass
class DevHubConfig:
    """Main DevHub configuration container"""
    
    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    pms: PMSConfig = field(default_factory=PMSConfig)
    das: DASConfig = field(default_factory=DASConfig)
    events: EventConfig = field(default_factory=EventConfig)
    web: WebConfig = field(default_factory=WebConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)
    
    # Meta configuration
    config_version: str = "1.0.0"
    loaded_at: datetime = field(default_factory=datetime.now)
    loaded_from: Optional[str] = None
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment == Environment.TESTING
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Security validations
        if self.is_production() and not self.security.is_secure():
            issues.append("Production environment requires secure secret_key and api_key")
        
        # Database validations
        if not self.database.url:
            issues.append("Database URL is required")
        
        # PMS validations
        pms_path = self.pms.get_memory_path()
        if not pms_path.parent.exists():
            issues.append(f"PMS project root directory does not exist: {self.pms.project_root}")
        
        # DAS validations
        agents_path = self.das.get_agents_path()
        if not agents_path.exists():
            issues.append(f"DAS agents directory does not exist: {agents_path}")
        
        # Logging validations
        if self.logging.enable_file and not self.logging.file_path:
            issues.append("File logging enabled but no file path specified")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'environment': self.environment.value,
            'database': self.database.__dict__,
            'security': {k: v for k, v in self.security.__dict__.items() 
                        if not k.startswith('secret')},  # Exclude secrets
            'logging': self.logging.__dict__,
            'pms': self.pms.__dict__,
            'das': self.das.__dict__,
            'events': self.events.__dict__,
            'web': self.web.__dict__,
            'cli': self.cli.__dict__,
            'config_version': self.config_version,
            'loaded_at': self.loaded_at.isoformat(),
            'loaded_from': self.loaded_from
        }

# ---------------------------------------------------------------------------
# Configuration Manager
# ---------------------------------------------------------------------------

class ConfigManager:
    """Manages multi-environment configuration loading and validation"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, DevHubConfig] = {}
        self.current_environment = self._detect_environment()
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default config files if they don't exist
        self._ensure_default_configs()
        
        logger.info(f"ConfigManager initialized for environment: {self.current_environment}")
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env_var = os.getenv('DEVHUB_ENV', os.getenv('ENV', 'development'))
        
        try:
            return Environment(env_var.lower())
        except ValueError:
            logger.warning(f"Unknown environment '{env_var}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _ensure_default_configs(self) -> None:
        """Create default configuration files for all environments"""
        for env in Environment:
            config_file = self.config_dir / f"{env.value}.yaml"
            if not config_file.exists():
                default_config = self._create_default_config(env)
                self._save_config_file(config_file, default_config)
                logger.info(f"Created default config: {config_file}")
    
    def _create_default_config(self, environment: Environment) -> DevHubConfig:
        """Create default configuration for specific environment"""
        config = DevHubConfig(environment=environment)
        
        # Environment-specific customizations
        if environment == Environment.PRODUCTION:
            config.database.url = os.getenv('DATABASE_URL', 'postgresql://localhost/devhub_prod')
            config.database.echo = False
            config.security.secret_key = os.getenv('SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')
            config.security.api_key = os.getenv('API_KEY')
            config.logging.level = "WARNING"
            config.logging.enable_file = True
            config.logging.file_path = "logs/devhub_prod.log"
            config.web.debug = False
            config.web.host = "0.0.0.0"
            config.das.enable_enforcement = True
            
        elif environment == Environment.TESTING:
            config.database.url = "sqlite:///:memory:"
            config.database.echo = False
            config.logging.level = "ERROR"
            config.logging.enable_console = False
            config.das.enable_audit_logging = False
            config.events.enable_persistence = False
            config.cli.confirm_destructive_actions = False
            
        elif environment == Environment.STAGING:
            config.database.url = os.getenv('DATABASE_URL', 'postgresql://localhost/devhub_staging')
            config.logging.level = "INFO"
            config.logging.enable_file = True
            config.logging.file_path = "logs/devhub_staging.log"
            config.web.debug = False
            config.das.enable_enforcement = True
            
        # Development environment keeps defaults
        
        return config
    
    def _save_config_file(self, config_file: Path, config: DevHubConfig) -> None:
        """Save configuration to YAML file"""
        config_dict = config.to_dict()
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.error(f"Failed to save config file {config_file}: {e}")
            raise
    
    def load_config(self, environment: Optional[Union[str, Environment]] = None) -> DevHubConfig:
        """Load configuration for specified environment"""
        if environment is None:
            environment = self.current_environment
        elif isinstance(environment, str):
            environment = Environment(environment.lower())
        
        env_key = environment.value
        
        # Check cache first
        if env_key in self.config_cache:
            return self.config_cache[env_key]
        
        # Load from file
        config_file = self.config_dir / f"{env_key}.yaml"
        
        if config_file.exists():
            config = self._load_config_file(config_file, environment)
        else:
            logger.warning(f"Config file not found: {config_file}, using defaults")
            config = self._create_default_config(environment)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config)
        
        # Validate configuration
        issues = config.validate()
        if issues:
            logger.warning(f"Configuration validation issues: {issues}")
        
        # Cache and return
        self.config_cache[env_key] = config
        logger.info(f"Loaded configuration for environment: {environment.value}")
        
        return config
    
    def _load_config_file(self, config_file: Path, environment: Environment) -> DevHubConfig:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            # Create config object from dictionary
            config = self._dict_to_config(config_dict, environment)
            config.loaded_from = str(config_file)
            config.loaded_at = datetime.now()
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
            # Return default config as fallback
            return self._create_default_config(environment)
    
    def _dict_to_config(self, config_dict: Dict[str, Any], environment: Environment) -> DevHubConfig:
        """Convert dictionary to DevHubConfig object"""
        # Extract nested configurations
        database_config = DatabaseConfig(**config_dict.get('database', {}))
        security_config = SecurityConfig(**config_dict.get('security', {}))
        logging_config = LoggingConfig(**config_dict.get('logging', {}))
        pms_config = PMSConfig(**config_dict.get('pms', {}))
        das_config = DASConfig(**config_dict.get('das', {}))
        events_config = EventConfig(**config_dict.get('events', {}))
        web_config = WebConfig(**config_dict.get('web', {}))
        cli_config = CLIConfig(**config_dict.get('cli', {}))
        
        return DevHubConfig(
            environment=environment,
            database=database_config,
            security=security_config,
            logging=logging_config,
            pms=pms_config,
            das=das_config,
            events=events_config,
            web=web_config,
            cli=cli_config,
            config_version=config_dict.get('config_version', '1.0.0')
        )
    
    def _apply_env_overrides(self, config: DevHubConfig) -> DevHubConfig:
        """Apply environment variable overrides to configuration"""
        # Database overrides
        if os.getenv('DATABASE_URL'):
            config.database.url = os.getenv('DATABASE_URL')
        
        # Security overrides
        if os.getenv('SECRET_KEY'):
            config.security.secret_key = os.getenv('SECRET_KEY')
        if os.getenv('API_KEY'):
            config.security.api_key = os.getenv('API_KEY')
        
        # Web overrides
        if os.getenv('WEB_HOST'):
            config.web.host = os.getenv('WEB_HOST')
        if os.getenv('WEB_PORT'):
            try:
                config.web.port = int(os.getenv('WEB_PORT'))
            except ValueError:
                logger.warning("Invalid WEB_PORT environment variable")
        
        # Logging overrides
        if os.getenv('LOG_LEVEL'):
            config.logging.level = os.getenv('LOG_LEVEL').upper()
        
        return config
    
    def get_config(self, environment: Optional[Union[str, Environment]] = None) -> DevHubConfig:
        """Get configuration for environment (alias for load_config)"""
        return self.load_config(environment)
    
    def reload_config(self, environment: Optional[Union[str, Environment]] = None) -> DevHubConfig:
        """Reload configuration from file, clearing cache"""
        if environment is None:
            environment = self.current_environment
        elif isinstance(environment, str):
            environment = Environment(environment.lower())
        
        # Clear cache entry
        env_key = environment.value
        if env_key in self.config_cache:
            del self.config_cache[env_key]
        
        return self.load_config(environment)
    
    def list_environments(self) -> List[str]:
        """List all available environment configurations"""
        config_files = list(self.config_dir.glob("*.yaml"))
        return [f.stem for f in config_files]
    
    def export_config(self, environment: Optional[Union[str, Environment]] = None, 
                     include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        config = self.load_config(environment)
        config_dict = config.to_dict()
        
        if not include_secrets:
            # Remove sensitive information
            if 'security' in config_dict:
                security = config_dict['security']
                for key in list(security.keys()):
                    if 'secret' in key.lower() or 'key' in key.lower():
                        security[key] = "[REDACTED]"
        
        return config_dict

# ---------------------------------------------------------------------------
# Global Configuration Instance
# ---------------------------------------------------------------------------

_global_config_manager: Optional[ConfigManager] = None
_global_config: Optional[DevHubConfig] = None

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager

def get_config(environment: Optional[Union[str, Environment]] = None) -> DevHubConfig:
    """Get DevHub configuration for current or specified environment"""
    global _global_config
    
    config_manager = get_config_manager()
    
    # If no environment specified and we have a global config, return it
    if environment is None and _global_config is not None:
        return _global_config
    
    # Load configuration
    config = config_manager.load_config(environment)
    
    # Cache as global config if loading current environment
    if environment is None or environment == config_manager.current_environment:
        _global_config = config
    
    return config

def set_environment(environment: Union[str, Environment]) -> DevHubConfig:
    """Set current environment and return updated configuration"""
    global _global_config, _global_config_manager
    
    if isinstance(environment, str):
        environment = Environment(environment.lower())
    
    # Update environment in config manager
    config_manager = get_config_manager()
    config_manager.current_environment = environment
    
    # Clear global config to force reload
    _global_config = None
    
    # Load and return new configuration
    return get_config()

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def validate_current_config() -> List[str]:
    """Validate current configuration and return issues"""
    config = get_config()
    return config.validate()

def is_production() -> bool:
    """Check if running in production environment"""
    return get_config().is_production()

def is_development() -> bool:
    """Check if running in development environment"""
    return get_config().is_development()

def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_config().is_testing()

def get_database_config() -> DatabaseConfig:
    """Get database configuration for current environment"""
    return get_config().database

def get_security_config() -> SecurityConfig:
    """Get security configuration for current environment"""
    return get_config().security

def setup_logging() -> None:
    """Setup logging based on current configuration"""
    config = get_config().logging
    
    # Configure logging level
    logging.getLogger().setLevel(config.get_log_level())
    
    # Setup formatters
    formatter = logging.Formatter(config.format)
    
    # Console handler
    if config.enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
    
    # File handler
    if config.enable_file and config.file_path:
        from logging.handlers import RotatingFileHandler
        
        # Ensure log directory exists
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    logger.info(f"Logging configured for {get_config().environment.value} environment")