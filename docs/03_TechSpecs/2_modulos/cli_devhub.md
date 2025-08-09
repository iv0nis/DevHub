# TS-CLI: DevHub Command Line Interface

## 1. Descripción del Módulo

### Información General
- **Nombre**: DevHub CLI (Command Line Interface)
- **ID**: TS-CLI-001
- **Responsabilidades**: Interface de línea de comandos para operaciones principales de DevHub
- **Relación con otros módulos**: Frontend para PMS Core y DAS Enforcer, entry point principal para usuarios

### Interfaces Principales
```python
class DevHubCLI:
    def create_project(name: str, template: str = "default") -> bool
    def validate_structure(project_path: str = ".") -> ValidationReport
    def sync_documents(project_path: str = ".") -> SyncReport  
    def evaluate_blueprint(project_path: str = ".") -> EvaluationReport
    def agent_run(agent_name: str, task: str, project_path: str = ".") -> ExecutionReport
    def status(project_path: str = ".") -> StatusReport
```

## 2. Diseño Detallado

### Arquitectura CLI
```
DevHub CLI Architecture:
┌─────────────────────────────────────────┐
│ CLI Parser Layer (Click/ArgParse)       │
├─────────────────────────────────────────┤
│ Command Handlers Layer                  │
├─────────────────────────────────────────┤  
│ Validation & Reporting Layer            │
├─────────────────────────────────────────┤
│ DAS/PMS Integration Layer               │
├─────────────────────────────────────────┤
│ Template Engine (Jinja2)                │
└─────────────────────────────────────────┘
```

### Estructura Principal
```python
#!/usr/bin/env python3
"""
DevHub CLI - Command Line Interface
Entry point: devhub_cli.py
"""

import click
import sys
from pathlib import Path
from typing import Optional

from pms.pms_core import PMSCore
from das.enforcer import DASEnforcer

@click.group()
@click.version_option(version="1.0.0")
@click.option('--project-path', default='.', help='Path to DevHub project')
@click.pass_context
def cli(ctx, project_path: str):
    """DevHub - Sistema de gestión de proyectos con agentes autónomos"""
    ctx.ensure_object(dict)
    ctx.obj['project_path'] = Path(project_path).resolve()
    
    # Validar que es un proyecto DevHub válido (excepto para create-project)
    if ctx.invoked_subcommand != 'create-project':
        if not _is_devhub_project(ctx.obj['project_path']):
            click.echo(f"Error: {project_path} no es un proyecto DevHub válido", err=True)
            sys.exit(1)

def _is_devhub_project(path: Path) -> bool:
    """Valida estructura básica de proyecto DevHub"""
    required_files = [
        'memory/memory_index.yaml',
        'das/enforcer.py', 
        'pms/pms_core.py'
    ]
    return all((path / file).exists() for file in required_files)
```

### Comandos Principales

#### 2.1 Create Project Command
```python
@cli.command('create-project')
@click.argument('name')
@click.option('--template', default='default', help='Template to use')
@click.option('--force', is_flag=True, help='Overwrite existing directory')
@click.pass_context
def create_project(ctx, name: str, template: str, force: bool):
    """Crea un nuevo proyecto DevHub con estructura estándar"""
    
    project_path = Path(name)
    
    if project_path.exists() and not force:
        click.echo(f"Error: Directory '{name}' already exists. Use --force to overwrite.", err=True)
        return False
    
    try:
        creator = ProjectCreator()
        success = creator.create_project(name, template, force)
        
        if success:
            click.echo(f"✅ Proyecto '{name}' creado exitosamente")
            click.echo(f"📁 Ubicación: {project_path.resolve()}")
            click.echo(f"🚀 Para empezar: cd {name} && devhub status")
        else:
            click.echo(f"❌ Error creando proyecto '{name}'", err=True)
            return False
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        return False
    
    return True

class ProjectCreator:
    """Maneja creación de nuevos proyectos DevHub"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent / 'templates'
    
    def create_project(self, name: str, template: str, force: bool) -> bool:
        """Crea estructura completa de proyecto"""
        project_path = Path(name)
        
        if force and project_path.exists():
            shutil.rmtree(project_path)
        
        # Crear estructura de directorios
        self._create_directory_structure(project_path)
        
        # Copiar templates
        self._copy_templates(project_path, template)
        
        # Configurar proyecto específico
        self._configure_project(project_path, name)
        
        # Inicializar Git
        self._init_git(project_path)
        
        return True
    
    def _create_directory_structure(self, project_path: Path):
        """Crea estructura estándar de directorios"""
        directories = [
            'memory',
            'docs/01_ProjectCharter',
            'docs/02_blueprint',
            'docs/03_TechSpecs', 
            'docs/04_roadmap',
            'docs/05_backlog',
            'pms',
            'das/agent_templates',
            'agents'
        ]
        
        for dir_path in directories:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    def _copy_templates(self, project_path: Path, template: str):
        """Copia archivos template al nuevo proyecto"""
        template_path = self.templates_dir / template
        
        if not template_path.exists():
            raise ValueError(f"Template '{template}' not found")
        
        # Copiar archivos template usando Jinja2 para replacements
        from jinja2 import Environment, FileSystemLoader
        
        env = Environment(loader=FileSystemLoader(template_path))
        
        template_files = [
            'memory_index.yaml',
            'project_status.md',
            'pms_core.py',
            'enforcer.py',
            'blueprint.yaml'
        ]
        
        for template_file in template_files:
            if (template_path / template_file).exists():
                template = env.get_template(template_file)
                content = template.render(
                    project_name=project_path.name,
                    creation_date=datetime.now().isoformat(),
                    version="1.0"
                )
                
                target_path = self._get_target_path(project_path, template_file)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
```

#### 2.2 Validate Structure Command
```python
@cli.command('validate-structure') 
@click.pass_context
def validate_structure(ctx):
    """Valida integridad de estructura del proyecto"""
    
    project_path = ctx.obj['project_path']
    validator = StructureValidator(project_path)
    
    report = validator.validate()
    
    # Display results
    click.echo(f"🔍 Validando estructura del proyecto: {project_path.name}")
    click.echo()
    
    if report.is_valid:
        click.echo("✅ Estructura del proyecto válida")
    else:
        click.echo("❌ Estructura del proyecto tiene problemas:")
        
        for error in report.errors:
            click.echo(f"  ❌ {error}", err=True)
        
        for warning in report.warnings:
            click.echo(f"  ⚠️  {warning}")
    
    click.echo()
    click.echo(f"📊 Resumen:")
    click.echo(f"  • Archivos críticos: {report.critical_files_count}/{report.critical_files_expected}")
    click.echo(f"  • SHA-1 integrity: {report.integrity_status}")
    click.echo(f"  • Agent configs: {report.agent_configs_valid}")

class StructureValidator:
    """Validador completo de estructura de proyecto DevHub"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.pms = PMSCore(str(project_path))
        self.das = DASEnforcer(str(project_path))
    
    def validate(self) -> ValidationReport:
        """Ejecuta todas las validaciones"""
        report = ValidationReport()
        
        # Validar archivos críticos
        self._validate_critical_files(report)
        
        # Validar integridad SHA-1
        self._validate_integrity(report)
        
        # Validar configuraciones de agentes
        self._validate_agent_configs(report)
        
        # Validar estructura de documentos
        self._validate_document_structure(report)
        
        return report
    
    def _validate_critical_files(self, report: ValidationReport):
        """Valida presencia de archivos críticos"""
        critical_files = [
            'memory/memory_index.yaml',
            'memory/project_status.md',
            'pms/pms_core.py',
            'das/enforcer.py',
            'docs/blueprint.yaml'
        ]
        
        for file_path in critical_files:
            full_path = self.project_path / file_path
            if full_path.exists():
                report.critical_files_count += 1
            else:
                report.errors.append(f"Missing critical file: {file_path}")
        
        report.critical_files_expected = len(critical_files)
    
    def _validate_integrity(self, report: ValidationReport):
        """Valida integridad SHA-1 de archivos críticos"""
        try:
            # Usar PMS para validar integridad
            scopes = ['blueprint', 'project_status']
            
            for scope in scopes:
                is_valid, message = self.pms.validate_file_integrity(scope)
                if is_valid:
                    report.integrity_checks_passed += 1
                else:
                    report.warnings.append(f"Integrity issue in {scope}: {message}")
            
            report.integrity_status = f"{report.integrity_checks_passed}/{len(scopes)} passed"
            
        except Exception as e:
            report.errors.append(f"Integrity validation failed: {str(e)}")
```

#### 2.3 Sync Documents Command  
```python
@cli.command('sync-documents')
@click.option('--dry-run', is_flag=True, help='Show what would be synced without making changes')
@click.pass_context
def sync_documents(ctx, dry_run: bool):
    """Sincroniza documentos del proyecto"""
    
    project_path = ctx.obj['project_path']
    syncer = DocumentSyncer(project_path)
    
    click.echo(f"🔄 Sincronizando documentos del proyecto: {project_path.name}")
    
    if dry_run:
        click.echo("🔍 Modo dry-run: mostrando cambios sin aplicar")
    
    try:
        report = syncer.sync_documents(dry_run=dry_run)
        
        if report.changes_made > 0:
            click.echo(f"✅ {report.changes_made} documentos sincronizados")
            
            for change in report.changes:
                action_icon = "📝" if change.action == "update" else "➕"
                click.echo(f"  {action_icon} {change.file}: {change.description}")
        else:
            click.echo("✅ Todos los documentos están sincronizados")
        
        if report.errors:
            click.echo("⚠️  Errores durante sincronización:")
            for error in report.errors:
                click.echo(f"  ❌ {error}", err=True)
                
    except Exception as e:
        click.echo(f"❌ Error en sincronización: {str(e)}", err=True)

class DocumentSyncer:
    """Maneja sincronización automática de documentos"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.pms = PMSCore(str(project_path))
    
    def sync_documents(self, dry_run: bool = False) -> SyncReport:
        """Ejecuta sincronización completa"""
        report = SyncReport()
        
        # Sincronizar blueprint modular → blueprint.yaml
        self._sync_blueprint_modular(report, dry_run)
        
        # Actualizar project_status con último estado
        self._sync_project_status(report, dry_run)
        
        # Validar consistencia entre documentos
        self._validate_document_consistency(report)
        
        return report
    
    def _sync_blueprint_modular(self, report: SyncReport, dry_run: bool):
        """Sincroniza estructura modular blueprint → YAML"""
        modular_dir = self.project_path / 'docs' / '02_blueprint'
        blueprint_yaml = self.project_path / 'docs' / 'blueprint.yaml'
        
        if not modular_dir.exists():
            report.warnings.append("Blueprint modular directory not found")
            return
        
        # Leer estructura modular
        modular_content = self._read_modular_blueprint(modular_dir)
        
        # Comparar con YAML actual
        current_yaml = self.pms.load('blueprint') if blueprint_yaml.exists() else {}
        
        if self._blueprint_needs_sync(modular_content, current_yaml):
            if not dry_run:
                # Actualizar blueprint.yaml
                updated_yaml = self._merge_blueprint_content(modular_content, current_yaml)
                self.pms.save('blueprint', updated_yaml)
            
            report.add_change('blueprint.yaml', 'update', 'Synchronized with modular structure')
```

#### 2.4 Evaluate Blueprint Command
```python
@cli.command('evaluate-blueprint')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed breakdown')
@click.pass_context  
def evaluate_blueprint(ctx, verbose: bool):
    """Evalúa completitud del blueprint vs Charter"""
    
    project_path = ctx.obj['project_path']
    
    try:
        evaluator = BlueprintEvaluator(project_path)
        score, breakdown = evaluator.evaluate()
        
        # Display results
        percentage = int(score * 100)
        status_icon = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
        
        click.echo(f"📊 Blueprint Completeness: {status_icon} {percentage}%")
        
        if verbose:
            click.echo()
            click.echo("📋 Detailed breakdown:")
            
            for check, value in breakdown.items():
                check_percentage = int(value * 100)
                check_icon = "✅" if value >= 0.8 else "⚠️" if value >= 0.4 else "❌"
                click.echo(f"  {check_icon} {check.replace('_', ' ').title()}: {check_percentage}%")
        
        # Recommendations
        click.echo()
        if score >= 0.8:
            click.echo("🎯 Ready for TechSpecs development")
        elif score >= 0.6:
            click.echo("📈 Good progress. Focus on low-scoring areas.")
        else:
            click.echo("⚡ Significant work needed before proceeding to TechSpecs")
            
    except Exception as e:
        click.echo(f"❌ Error evaluating blueprint: {str(e)}", err=True)
```

#### 2.5 Agent Run Command
```python
@cli.command('agent-run')
@click.argument('agent_name')
@click.argument('task') 
@click.option('--timeout', default=300, help='Timeout in seconds')
@click.pass_context
def agent_run(ctx, agent_name: str, task: str, timeout: int):
    """Ejecuta tarea específica con agente"""
    
    project_path = ctx.obj['project_path']
    
    click.echo(f"🤖 Ejecutando {agent_name}: {task}")
    
    try:
        runner = AgentRunner(project_path)
        result = runner.execute_task(agent_name, task, timeout)
        
        if result.success:
            click.echo(f"✅ Tarea completada exitosamente")
            
            if result.files_modified:
                click.echo("📝 Archivos modificados:")
                for file_path in result.files_modified:
                    click.echo(f"  • {file_path}")
        else:
            click.echo(f"❌ Tarea falló: {result.error}")
            
        # Show execution metrics
        click.echo(f"⏱️  Tiempo de ejecución: {result.duration:.2f}s")
        
    except Exception as e:
        click.echo(f"❌ Error ejecutando agente: {str(e)}", err=True)

class AgentRunner:
    """Executor de tareas para agentes DevHub"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.das = DASEnforcer(str(project_path))
    
    def execute_task(self, agent_name: str, task: str, timeout: int) -> ExecutionResult:
        """Ejecuta tarea específica con timeout"""
        
        start_time = time.time()
        result = ExecutionResult()
        
        try:
            # Validar que agente existe
            if agent_name not in self.das.agent_configs:
                raise AgentNotFoundError(f"Agent '{agent_name}' not configured")
            
            # Mapear task a método específico
            task_method = self._get_task_method(agent_name, task)
            
            if not task_method:
                raise ValueError(f"Task '{task}' not supported for agent '{agent_name}'")
            
            # Ejecutar con timeout
            with timeout_context(timeout):
                result = task_method()
            
            result.success = True
            
        except Exception as e:
            result.success = False
            result.error = str(e)
        finally:
            result.duration = time.time() - start_time
        
        return result
    
    def _get_task_method(self, agent_name: str, task: str):
        """Mapea combinación agent+task a método ejecutable"""
        task_map = {
            ('BlueprintAgent', 'evaluate'): self._blueprint_evaluate,
            ('BlueprintAgent', 'sync'): self._blueprint_sync,
            ('DevAgent', 'next-task'): self._dev_agent_next_task,
            ('DevAgent', 'update-status'): self._dev_agent_update_status,
        }
        
        return task_map.get((agent_name, task))
```

## 3. Reporting y Output

### Report Classes
```python
@dataclass
class ValidationReport:
    """Reporte de validación de estructura"""
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    critical_files_count: int = 0
    critical_files_expected: int = 0
    integrity_status: str = ""
    agent_configs_valid: bool = True

@dataclass  
class SyncReport:
    """Reporte de sincronización de documentos"""
    changes_made: int = 0
    changes: list[SyncChange] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_change(self, file: str, action: str, description: str):
        change = SyncChange(file=file, action=action, description=description)
        self.changes.append(change)
        self.changes_made += 1

@dataclass
class ExecutionResult:
    """Resultado de ejecución de agente"""
    success: bool = False
    error: str = ""
    duration: float = 0.0
    files_modified: list[str] = field(default_factory=list)
    output: str = ""
```

## 4. Templates y Configuración

### Project Templates Structure
```
templates/
├── default/
│   ├── memory_index.yaml.j2
│   ├── project_status.md.j2
│   ├── pms_core.py.j2
│   ├── enforcer.py.j2
│   └── blueprint.yaml.j2
├── enterprise/
│   └── ... (enhanced templates)
└── minimal/
    └── ... (minimal setup)
```

### Template Variables
```python
# Variables disponibles en templates Jinja2
template_vars = {
    'project_name': 'ProjectName',
    'creation_date': '2025-08-09T12:00:00Z',
    'version': '1.0',
    'author': 'DevHub CLI',
    'python_version': '3.8+',
    'dependencies': ['pyyaml', 'click', 'pathlib']
}
```

## 5. Testing

### CLI Testing Strategy
```python
import pytest
from click.testing import CliRunner
from devhub_cli import cli

class TestDevHubCLI:
    """Test suite para DevHub CLI"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_create_project_success(self):
        """Test creación exitosa de proyecto"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create-project', 'test-project'])
            
            assert result.exit_code == 0
            assert "✅ Proyecto 'test-project' creado exitosamente" in result.output
            assert Path('test-project').exists()
    
    def test_validate_structure_valid_project(self):
        """Test validación de proyecto válido"""
        with self.runner.isolated_filesystem():
            # Setup valid project
            self._create_valid_project_structure()
            
            result = self.runner.invoke(cli, ['validate-structure'])
            
            assert result.exit_code == 0
            assert "✅ Estructura del proyecto válida" in result.output
    
    def test_evaluate_blueprint_with_verbose(self):
        """Test evaluación de blueprint con output verbose"""
        with self.runner.isolated_filesystem():
            self._create_valid_project_structure()
            
            result = self.runner.invoke(cli, ['evaluate-blueprint', '--verbose'])
            
            assert result.exit_code == 0
            assert "📊 Blueprint Completeness:" in result.output
            assert "📋 Detailed breakdown:" in result.output
```

## 6. Error Handling

### CLI Error Handling
```python
class CLIError(Exception):
    """Base exception para CLI operations"""
    pass

def handle_cli_errors(func):
    """Decorator para manejo consistente de errores CLI"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            click.echo("\n⏹️  Operation cancelled by user", err=True)
            sys.exit(130)
        except CLIError as e:
            click.echo(f"❌ {str(e)}", err=True)  
            sys.exit(1)
        except Exception as e:
            click.echo(f"💥 Unexpected error: {str(e)}", err=True)
            sys.exit(1)
    return wrapper

# Apply to all command functions
@handle_cli_errors
def create_project(ctx, name: str, template: str, force: bool):
    # Implementation...
```

## 7. Performance

### CLI Performance Optimization
- **Lazy Loading**: Commands carga módulos solo cuando necesario
- **Caching**: Config y validaciones cached between commands
- **Streaming Output**: Large operations show progress
- **Parallel Operations**: I/O operations parallelized donde posible

### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Monitor CLI command performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        if duration > 5.0:  # Log slow commands
            click.echo(f"⏰ Command took {duration:.2f}s", err=True)
        
        return result
    return wrapper
```