# -*- coding: utf-8 -*-
"""DevHub Template Engine - TS-CLI-002 Implementation

Jinja2-based template system for automatic DevHub project generation.
Provides standardized project structure creation with customizable templates.

Usage:
    from core.templates import TemplateEngine, ProjectTemplate
    
    engine = TemplateEngine()
    
    # Create project from template
    project_data = {
        'project_name': 'MyProject',
        'description': 'My DevHub project'
    }
    
    engine.create_project('my-project', 'default', project_data)
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import yaml
import json
import logging
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, TemplateNotFound

logger = logging.getLogger("devhub.templates")

# ---------------------------------------------------------------------------
# Template Data Models
# ---------------------------------------------------------------------------

@dataclass
class ProjectMetadata:
    """Project metadata for template rendering"""
    project_name: str
    display_name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    email: str = ""
    license: str = "MIT"
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.project_name.replace('_', ' ').replace('-', ' ').title()

@dataclass
class TemplateContext:
    """Complete context for template rendering"""
    project: ProjectMetadata
    config: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Jinja2"""
        return {
            'project': {
                'name': self.project.project_name,
                'display_name': self.project.display_name,
                'description': self.project.description,
                'version': self.project.version,
                'author': self.project.author,
                'email': self.project.email,
                'license': self.project.license,
                'created_at': self.project.created_at,
                'created_at_iso': self.project.created_at.isoformat(),
                'year': self.project.created_at.year
            },
            'config': self.config,
            'custom': self.custom
        }

@dataclass
class ProjectTemplate:
    """Project template definition"""
    name: str
    display_name: str
    description: str
    template_dir: Path
    files: List[str] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    hooks: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_config(cls, template_dir: Path) -> 'ProjectTemplate':
        """Load template from template.yaml config"""
        config_file = template_dir / "template.yaml"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            return cls(
                name=config.get('name', template_dir.name),
                display_name=config.get('display_name', template_dir.name.title()),
                description=config.get('description', ''),
                template_dir=template_dir,
                files=config.get('files', []),
                directories=config.get('directories', []),
                hooks=config.get('hooks', {})
            )
        else:
            # Auto-discover template structure
            files = []
            directories = []
            
            for item in template_dir.rglob('*'):
                if item.is_file() and item.name != 'template.yaml':
                    files.append(str(item.relative_to(template_dir)))
                elif item.is_dir():
                    directories.append(str(item.relative_to(template_dir)))
            
            return cls(
                name=template_dir.name,
                display_name=template_dir.name.title(),
                description=f"Auto-discovered template: {template_dir.name}",
                template_dir=template_dir,
                files=files,
                directories=directories
            )

# ---------------------------------------------------------------------------
# Template Engine
# ---------------------------------------------------------------------------

class TemplateEngine:
    """Jinja2-based template engine for DevHub project generation"""
    
    def __init__(self, templates_dir: str = "docs/doc_templates"):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path.cwd()
        self.available_templates: Dict[str, ProjectTemplate] = {}
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._setup_custom_filters()
        
        # Discover available templates
        self._discover_templates()
        
        logger.info(f"TemplateEngine initialized with {len(self.available_templates)} templates")
    
    def _setup_custom_filters(self) -> None:
        """Setup custom Jinja2 filters"""
        
        def snake_case(value: str) -> str:
            """Convert to snake_case"""
            import re
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str(value))
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
        def kebab_case(value: str) -> str:
            """Convert to kebab-case"""
            return snake_case(value).replace('_', '-')
        
        def pascal_case(value: str) -> str:
            """Convert to PascalCase"""
            return ''.join(word.capitalize() for word in str(value).replace('-', '_').split('_'))
        
        def camel_case(value: str) -> str:
            """Convert to camelCase"""
            pascal = pascal_case(value)
            return pascal[0].lower() + pascal[1:] if pascal else ''
        
        def title_case(value: str) -> str:
            """Convert to Title Case"""
            return str(value).replace('_', ' ').replace('-', ' ').title()
        
        # Register filters
        self.jinja_env.filters['snake_case'] = snake_case
        self.jinja_env.filters['kebab_case'] = kebab_case
        self.jinja_env.filters['pascal_case'] = pascal_case
        self.jinja_env.filters['camel_case'] = camel_case
        self.jinja_env.filters['title_case'] = title_case
    
    def _discover_templates(self) -> None:
        """Discover available project templates"""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        # Look for template directories and individual template files
        for item in self.templates_dir.iterdir():
            if item.is_dir():
                # Directory-based template
                try:
                    template = ProjectTemplate.from_config(item)
                    self.available_templates[template.name] = template
                    logger.debug(f"Discovered template: {template.name}")
                except Exception as e:
                    logger.error(f"Failed to load template {item.name}: {e}")
            elif item.suffix in ['.md', '.yaml', '.yml', '.json']:
                # Single file template
                template_name = item.stem
                if template_name not in self.available_templates:
                    template = ProjectTemplate(
                        name=template_name,
                        display_name=template_name.title(),
                        description=f"Single file template: {item.name}",
                        template_dir=self.templates_dir,
                        files=[item.name]
                    )
                    self.available_templates[template_name] = template
    
    def list_templates(self) -> List[ProjectTemplate]:
        """Get list of available templates"""
        return list(self.available_templates.values())
    
    def get_template(self, template_name: str) -> Optional[ProjectTemplate]:
        """Get specific template by name"""
        return self.available_templates.get(template_name)
    
    def create_project(self, project_name: str, template_name: str = "default", 
                      context_data: Optional[Dict[str, Any]] = None,
                      output_dir: Optional[Path] = None) -> bool:
        """Create new project from template
        
        Args:
            project_name: Name of project to create
            template_name: Template to use
            context_data: Additional context data for rendering
            output_dir: Output directory (defaults to current)
        
        Returns:
            True if project created successfully
        """
        if template_name not in self.available_templates:
            logger.error(f"Template not found: {template_name}")
            return False
        
        template = self.available_templates[template_name]
        project_dir = (output_dir or self.output_dir) / project_name
        
        # Check if project already exists
        if project_dir.exists():
            logger.error(f"Project directory already exists: {project_dir}")
            return False
        
        # Create project metadata
        project_meta = ProjectMetadata(
            project_name=project_name,
            description=context_data.get('description', '') if context_data else '',
            author=context_data.get('author', '') if context_data else '',
            email=context_data.get('email', '') if context_data else ''
        )
        
        # Create template context
        context = TemplateContext(
            project=project_meta,
            config=context_data.get('config', {}) if context_data else {},
            custom=context_data.get('custom', {}) if context_data else {}
        )
        
        try:
            # Create project directory
            project_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created project directory: {project_dir}")
            
            # Create directories
            for directory in template.directories:
                dir_path = project_dir / self._render_path(directory, context)
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
            
            # Process template files
            for file_path in template.files:
                success = self._process_template_file(
                    template, file_path, project_dir, context
                )
                if not success:
                    logger.error(f"Failed to process template file: {file_path}")
                    return False
            
            # Run post-creation hooks
            self._run_hooks(template, project_dir, context)
            
            logger.info(f"Project '{project_name}' created successfully from template '{template_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create project '{project_name}': {e}")
            # Cleanup on failure
            if project_dir.exists():
                shutil.rmtree(project_dir)
            return False
    
    def _render_path(self, path: str, context: TemplateContext) -> str:
        """Render path template with context"""
        try:
            template = self.jinja_env.from_string(path)
            return template.render(**context.to_dict())
        except TemplateError as e:
            logger.error(f"Failed to render path '{path}': {e}")
            return path
    
    def _process_template_file(self, template: ProjectTemplate, file_path: str,
                              project_dir: Path, context: TemplateContext) -> bool:
        """Process individual template file"""
        try:
            # Render output file path
            output_path = project_dir / self._render_path(file_path, context)
            
            # Ensure parent directories exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load and render template
            template_file = template.template_dir / file_path
            
            if template_file.exists():
                # File-based template
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Render template content
                jinja_template = self.jinja_env.from_string(template_content)
                rendered_content = jinja_template.render(**context.to_dict())
                
                # Write rendered content
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(rendered_content)
                
                logger.debug(f"Processed template file: {file_path} -> {output_path}")
                return True
            else:
                logger.error(f"Template file not found: {template_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing template file '{file_path}': {e}")
            return False
    
    def _run_hooks(self, template: ProjectTemplate, project_dir: Path, 
                  context: TemplateContext) -> None:
        """Run post-creation hooks"""
        for hook_name, hook_command in template.hooks.items():
            try:
                logger.info(f"Running hook '{hook_name}': {hook_command}")
                
                # Render hook command with context
                rendered_command = self.jinja_env.from_string(hook_command).render(**context.to_dict())
                
                # Execute hook in project directory
                import subprocess
                result = subprocess.run(
                    rendered_command,
                    shell=True,
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    logger.info(f"Hook '{hook_name}' completed successfully")
                else:
                    logger.warning(f"Hook '{hook_name}' failed: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error running hook '{hook_name}': {e}")
    
    def render_template_string(self, template_string: str, 
                              context_data: Dict[str, Any]) -> str:
        """Render template string with context data"""
        try:
            template = self.jinja_env.from_string(template_string)
            return template.render(**context_data)
        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise
    
    def validate_template(self, template_name: str) -> List[str]:
        """Validate template and return list of issues"""
        issues = []
        
        if template_name not in self.available_templates:
            issues.append(f"Template not found: {template_name}")
            return issues
        
        template = self.available_templates[template_name]
        
        # Check template directory exists
        if not template.template_dir.exists():
            issues.append(f"Template directory not found: {template.template_dir}")
        
        # Check template files exist
        for file_path in template.files:
            full_path = template.template_dir / file_path
            if not full_path.exists():
                issues.append(f"Template file not found: {full_path}")
        
        # Validate template syntax
        for file_path in template.files:
            full_path = template.template_dir / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Try to parse template
                    self.jinja_env.from_string(content)
                    
                except TemplateError as e:
                    issues.append(f"Template syntax error in {file_path}: {e}")
                except Exception as e:
                    issues.append(f"Error reading template {file_path}: {e}")
        
        return issues

# ---------------------------------------------------------------------------
# DevHub-Specific Template Utilities
# ---------------------------------------------------------------------------

class DevHubTemplateEngine(TemplateEngine):
    """DevHub-specific template engine with predefined templates"""
    
    def __init__(self):
        super().__init__("docs/doc_templates")
        self._setup_devhub_templates()
    
    def _setup_devhub_templates(self) -> None:
        """Setup DevHub-specific template configurations"""
        
        # Default DevHub project template
        default_template = ProjectTemplate(
            name="default",
            display_name="Default DevHub Project",
            description="Standard DevHub project with PMS, DAS, and CLI components",
            template_dir=self.templates_dir,
            files=[
                "backlog_fN_template.yaml",
                "blueprint_template.md",
                "techspecs_template.yaml"
            ],
            directories=[
                "docs/01_ProjectCharter",
                "docs/02_blueprint", 
                "docs/03_TechSpecs",
                "docs/04_Roadmap",
                "docs/05_backlog",
                "memory",
                "pms",
                "das/agents",
                "tests"
            ],
            hooks={
                "git_init": "git init",
                "create_gitignore": "echo '__pycache__/\n*.pyc\n.pytest_cache/\nnode_modules/\n.env' > .gitignore"
            }
        )
        
        self.available_templates["default"] = default_template
        
        # Minimal template
        minimal_template = ProjectTemplate(
            name="minimal",
            display_name="Minimal DevHub Project", 
            description="Minimal DevHub project structure",
            template_dir=self.templates_dir,
            files=[
                "blueprint_template.md"
            ],
            directories=[
                "docs",
                "memory"
            ]
        )
        
        self.available_templates["minimal"] = minimal_template
    
    def create_devhub_project(self, project_name: str, template_name: str = "default",
                             project_description: str = "", author: str = "",
                             output_dir: Optional[Path] = None) -> bool:
        """Create DevHub project with standard context"""
        
        context_data = {
            'description': project_description,
            'author': author,
            'config': {
                'pms_enabled': True,
                'das_enabled': True,
                'cli_enabled': True,
                'web_enabled': False  # Optional web dashboard
            },
            'custom': {
                'devhub_version': '1.0.0',
                'python_version': '3.8+',
                'framework': 'DevHub'
            }
        }
        
        return self.create_project(project_name, template_name, context_data, output_dir)

# ---------------------------------------------------------------------------
# CLI Integration
# ---------------------------------------------------------------------------

def create_project_from_template(project_name: str, template_name: str = "default",
                                **kwargs) -> bool:
    """Convenience function for CLI integration"""
    engine = DevHubTemplateEngine()
    return engine.create_devhub_project(
        project_name=project_name,
        template_name=template_name,
        project_description=kwargs.get('description', ''),
        author=kwargs.get('author', ''),
        output_dir=kwargs.get('output_dir')
    )

def list_available_templates() -> List[ProjectTemplate]:
    """List all available project templates"""
    engine = DevHubTemplateEngine()
    return engine.list_templates()

def validate_template_by_name(template_name: str) -> List[str]:
    """Validate template and return issues"""
    engine = DevHubTemplateEngine()
    return engine.validate_template(template_name)

# ---------------------------------------------------------------------------
# Global Template Engine Instance
# ---------------------------------------------------------------------------

_global_template_engine: Optional[DevHubTemplateEngine] = None

def get_template_engine() -> DevHubTemplateEngine:
    """Get global template engine instance"""
    global _global_template_engine
    if _global_template_engine is None:
        _global_template_engine = DevHubTemplateEngine()
    return _global_template_engine