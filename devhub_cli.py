#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DevHub CLI - Project Management and Creation

Central CLI for managing DevHub projects with independent PMS and DAS systems.
Each project gets its own isolated PMS and DAS configuration.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any
import argparse
import click
import yaml
import json
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import subprocess
import threading
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

# Template system imports
from core.templates import DevHubTemplateEngine, list_available_templates, validate_template_by_name

# Agent execution system imports
from das.enforcer import validate_agent_config, agent_load


# ---------------------------------------------------------------------------
# Agent Execution System - TS-CLI-003 Implementation
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    """Result of agent task execution"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_id: str = ""
    task_id: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentRunner:
    """Execute tasks with specific agents under DAS enforcement"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.config = validate_agent_config(agent_id)
        if not self.config:
            raise ValueError(f"Invalid agent configuration: {agent_id}")
    
    def execute_task(self, task_id: str, timeout: int = 300) -> ExecutionResult:
        """Execute a specific task with the agent"""
        start_time = time.time()
        
        try:
            # Validate agent permissions for task execution
            if not self._can_execute_task(task_id):
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Agent {self.agent_id} lacks permissions for task {task_id}",
                    execution_time=0.0,
                    agent_id=self.agent_id,
                    task_id=task_id
                )
            
            # Load task details from backlog
            task_details = self._load_task_details(task_id)
            if not task_details:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Task {task_id} not found in backlog",
                    execution_time=time.time() - start_time,
                    agent_id=self.agent_id,
                    task_id=task_id
                )
            
            # Execute task with timeout
            output = self._execute_with_timeout(task_details, timeout)
            
            return ExecutionResult(
                success=True,
                output=output,
                execution_time=time.time() - start_time,
                agent_id=self.agent_id,
                task_id=task_id,
                metadata={"task_details": task_details}
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                agent_id=self.agent_id,
                task_id=task_id
            )
    
    def _can_execute_task(self, task_id: str) -> bool:
        """Check if agent has permissions to execute task"""
        # For MVP, check if agent can read backlogs
        return 'backlog_f*' in self.config.get('read_scopes', [])
    
    def _load_task_details(self, task_id: str) -> Optional[Dict]:
        """Load task details from backlog"""
        try:
            # Try all backlog phases
            for phase in ['f1', 'f2', 'f3']:
                try:
                    backlog = agent_load(self.agent_id, f'backlog_{phase}')
                    if task_id in backlog.get('historias', {}):
                        return backlog['historias'][task_id]
                except:
                    continue
            return None
        except Exception:
            return None
    
    def _execute_with_timeout(self, task_details: Dict, timeout: int) -> str:
        """Execute task with timeout management"""
        # For MVP, return task analysis
        description = task_details.get('description', 'No description')
        status = task_details.get('status', 'unknown')
        priority = task_details.get('priority', 'unknown')
        
        output = f"""Task Analysis:
- Description: {description}
- Status: {status}
- Priority: {priority}
- Agent: {self.agent_id}
- Permissions: {self.config.get('read_scopes', [])}

Note: Full task execution requires integration with specific agent implementations."""
        
        return output


@contextmanager
def execution_timeout(seconds: int):
    """Context manager for execution timeout"""
    def timeout_handler():
        raise TimeoutError(f"Execution timeout after {seconds} seconds")
    
    timer = threading.Timer(seconds, timeout_handler)
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


def get_devhub_root() -> Path:
    """Get DevHub root directory"""
    return Path(__file__).parent


def create_project(project_name: str, project_type: str = "default", overwrite: bool = False) -> bool:
    """Create a new project with independent PMS and DAS systems.
    
    Args:
        project_name: Name of the project directory to create
        project_type: Type of project template (default, webapp, api, etc.)
        overwrite: If True, overwrite existing project files
        
    Returns:
        True if project created successfully, False otherwise
    """
    devhub_root = get_devhub_root()
    project_path = devhub_root / project_name
    
    print(f"🚀 Creating project '{project_name}' at {project_path}")
    
    # Check if project already exists
    if project_path.exists() and not overwrite:
        print(f"❌ Error: Project '{project_name}' already exists")
        return False
    elif project_path.exists() and overwrite:
        print(f"⚠️  Overwriting existing project '{project_name}'")
    
    try:
        # 1. Create project directory
        project_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {project_path}")
        
        # 2. Copy and configure PMS system
        _setup_pms_system(devhub_root, project_path, project_name)
        
        # 3. Copy and configure DAS system  
        _setup_das_system(devhub_root, project_path, project_name)
        
        # 4. Run PMS bootstrap to create data structures
        _bootstrap_project_data(project_path, project_name)
        
        print(f"🎉 Project '{project_name}' created successfully!")
        print(f"📁 Location: {project_path}")
        print(f"🔧 Next steps:")
        print(f"   cd {project_name}")
        print(f"   python -c \"from das.enforcer import validate_agent_config; print(validate_agent_config('DevAgent'))\"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating project '{project_name}': {e}")
        # Cleanup on failure
        if project_path.exists():
            shutil.rmtree(project_path)
        return False


def _setup_pms_system(devhub_root: Path, project_path: Path, project_name: str) -> None:
    """Copy and configure PMS system for the project"""
    
    # Copy pms_core.py to project root
    source_pms = devhub_root / "pms" / "pms_core.py"
    target_pms = project_path / "pms_core.py"
    
    if not source_pms.exists():
        raise FileNotFoundError(f"Source PMS core not found: {source_pms}")
    
    # Read source and modify PROJECT_ROOT constant
    with open(source_pms, 'r', encoding='utf-8') as f:
        pms_content = f.read()
    
    # Replace PROJECT_ROOT to use current directory instead of environment variable
    modified_content = pms_content.replace(
        'PROJECT_ROOT = Path(os.getenv("PMS_PROJECT_ROOT", Path.cwd()))',
        'PROJECT_ROOT = Path(__file__).parent'
    )
    
    # Write configured PMS to project
    with open(target_pms, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"✅ Configured PMS system: {target_pms}")
    
    # Copy templates directory
    source_templates = devhub_root / "pms" / "templates"
    target_templates = project_path / "templates"
    
    if source_templates.exists():
        if target_templates.exists():
            shutil.rmtree(target_templates)
        shutil.copytree(source_templates, target_templates)
        print(f"✅ Copied PMS templates: {target_templates}")


def _setup_das_system(devhub_root: Path, project_path: Path, project_name: str) -> None:
    """Copy and configure DAS system for the project"""
    
    # Create das directory in project
    das_dir = project_path / "das"
    das_dir.mkdir(exist_ok=True)
    
    # Copy and configure enforcer.py for local project context
    source_enforcer = devhub_root / "das" / "enforcer.py" 
    target_enforcer = das_dir / "enforcer.py"
    
    if not source_enforcer.exists():
        raise FileNotFoundError(f"Source DAS enforcer not found: {source_enforcer}")
    
    # Read and modify enforcer.py for local project context
    with open(source_enforcer, 'r', encoding='utf-8') as f:
        enforcer_content = f.read()
    
    # Replace import path to use local pms_core instead of parent directory
    modified_enforcer = enforcer_content.replace(
        'project_root = os.path.dirname(os.path.dirname(__file__))',
        '# Local project context - use current project directory\n        project_root = os.path.dirname(__file__)  # Project root is parent of das/'
    ).replace(
        'sys.path.insert(0, project_root)',
        '# Insert project root (parent of das/) into Python path\n        sys.path.insert(0, project_root)'
    )
    
    # Write configured enforcer to project
    with open(target_enforcer, 'w', encoding='utf-8') as f:
        f.write(modified_enforcer)
    
    print(f"✅ Configured DAS enforcer for local project: {target_enforcer}")
    
    # Copy and configure agents directory
    source_agents = devhub_root / "das" / "agents"
    target_agents = das_dir / "agents"
    
    if source_agents.exists():
        if target_agents.exists():
            shutil.rmtree(target_agents)
        shutil.copytree(source_agents, target_agents)
        
        # Configure DevAgent.yaml with project context
        devagent_config = target_agents / "DevAgent.yaml"
        if devagent_config.exists():
            _configure_devagent_for_project(devagent_config, project_name, project_path)
        
        print(f"✅ Configured DAS agents for project: {target_agents}")
    else:
        # Create minimal agents directory
        target_agents.mkdir(exist_ok=True)
        print(f"✅ Created DAS agents directory: {target_agents}")


def _bootstrap_project_data(project_path: Path, project_name: str) -> None:
    """Run PMS bootstrap to create initial project data"""
    
    # Change to project directory to run bootstrap
    original_cwd = Path.cwd()
    os.chdir(project_path)
    
    try:
        # Import and run bootstrap from the local pms_core
        sys.path.insert(0, str(project_path))
        import pms_core
        
        # Run bootstrap
        success = pms_core.bootstrap_pms(project_name)
        if not success:
            raise RuntimeError("PMS bootstrap failed")
            
        print(f"✅ Bootstrapped PMS data structures")
        
    finally:
        # Restore original directory and clean up path
        os.chdir(original_cwd)
        if str(project_path) in sys.path:
            sys.path.remove(str(project_path))


def list_projects() -> None:
    """List all projects in DevHub"""
    devhub_root = get_devhub_root()
    
    print("📋 DevHub Projects:")
    print("=" * 50)
    
    found_projects = False
    for item in devhub_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it's a DevHub project (has pms_core.py and das/)
            if (item / "pms_core.py").exists() and (item / "das").exists():
                print(f"🚀 {item.name}")
                found_projects = True
    
    if not found_projects:
        print("No projects found. Create one with: python devhub_cli.py create <project_name>")


# ---------------------------------------------------------------------------
# TS-CLI-001 Implementation: Core CLI Commands
# ---------------------------------------------------------------------------

class ValidationResult(Enum):
    """Validation result status"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class StructureValidation:
    """Structure validation result"""
    status: ValidationResult
    message: str
    component: str
    details: Optional[Dict] = None

class ProjectCreator:
    """Enhanced project creation with template support"""
    
    def __init__(self):
        self.devhub_root = get_devhub_root()
    
    def create_project(self, name: str, project_type: str = "default", overwrite: bool = False) -> bool:
        """Create new DevHub project with proper structure"""
        return create_project(name, project_type, overwrite)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available project templates"""
        templates_dir = self.devhub_root / "docs" / "doc_templates"
        if not templates_dir.exists():
            return ["default"]
        
        templates = []
        for item in templates_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                templates.append(item.name)
        
        return templates if templates else ["default"]

class StructureValidator:
    """Validates DevHub project structure integrity"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
    
    def validate_project_structure(self) -> List[StructureValidation]:
        """Comprehensive project structure validation"""
        validations = []
        
        # Core files validation
        validations.extend(self._validate_core_files())
        
        # Memory system validation
        validations.extend(self._validate_memory_system())
        
        # Agent system validation
        validations.extend(self._validate_agent_system())
        
        # Documentation structure validation
        validations.extend(self._validate_docs_structure())
        
        return validations
    
    def _validate_core_files(self) -> List[StructureValidation]:
        """Validate core system files"""
        validations = []
        required_files = [
            ("pms/pms_core.py", "PMS Core system"),
            ("das/enforcer.py", "DAS Enforcement system"),
            ("agents", "Agent configurations directory")
        ]
        
        for file_path, description in required_files:
            full_path = self.project_path / file_path
            if not full_path.exists():
                validations.append(StructureValidation(
                    ValidationResult.ERROR,
                    f"Missing required file: {file_path}",
                    "core_files",
                    {"path": str(full_path), "description": description}
                ))
            else:
                validations.append(StructureValidation(
                    ValidationResult.VALID,
                    f"Found {description}",
                    "core_files",
                    {"path": str(full_path)}
                ))
        
        return validations
    
    def _validate_memory_system(self) -> List[StructureValidation]:
        """Validate PMS memory system structure"""
        validations = []
        
        # Check memory index
        memory_index = self.project_path / "memory" / "memory_index.yaml"
        if not memory_index.exists():
            validations.append(StructureValidation(
                ValidationResult.ERROR,
                "Missing memory index configuration",
                "memory_system",
                {"expected_path": str(memory_index)}
            ))
        else:
            # Validate memory index content
            try:
                with open(memory_index, 'r', encoding='utf-8') as f:
                    index_data = yaml.safe_load(f)
                
                if 'scopes' not in index_data:
                    validations.append(StructureValidation(
                        ValidationResult.ERROR,
                        "Memory index missing 'scopes' section",
                        "memory_system"
                    ))
                elif 'schemas' not in index_data:
                    validations.append(StructureValidation(
                        ValidationResult.WARNING,
                        "Memory index missing 'schemas' section",
                        "memory_system"
                    ))
                else:
                    validations.append(StructureValidation(
                        ValidationResult.VALID,
                        f"Memory index valid with {len(index_data['scopes'])} scopes",
                        "memory_system"
                    ))
            except yaml.YAMLError as e:
                validations.append(StructureValidation(
                    ValidationResult.ERROR,
                    f"Invalid YAML in memory index: {e}",
                    "memory_system"
                ))
        
        return validations
    
    def _validate_agent_system(self) -> List[StructureValidation]:
        """Validate DAS agent system structure"""
        validations = []
        
        agents_dir = self.project_path / "agents"
        if not agents_dir.exists():
            validations.append(StructureValidation(
                ValidationResult.ERROR,
                "Missing agents directory",
                "agent_system",
                {"expected_path": str(agents_dir)}
            ))
            return validations
        
        # Check for essential agents
        essential_agents = ["DevAgent.yaml", "BlueprintAgent.yaml"]
        found_agents = []
        
        for agent_file in agents_dir.glob("*.yaml"):
            found_agents.append(agent_file.name)
            
            # Validate agent configuration structure
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_config = yaml.safe_load(f)
                
                required_sections = ['agent_info', 'pms_scopes', 'enforcement']
                missing_sections = []
                
                for section in required_sections:
                    if section not in agent_config:
                        missing_sections.append(section)
                
                if missing_sections:
                    validations.append(StructureValidation(
                        ValidationResult.WARNING,
                        f"Agent {agent_file.name} missing sections: {', '.join(missing_sections)}",
                        "agent_system"
                    ))
                else:
                    validations.append(StructureValidation(
                        ValidationResult.VALID,
                        f"Agent {agent_file.name} configuration valid",
                        "agent_system"
                    ))
                    
            except yaml.YAMLError as e:
                validations.append(StructureValidation(
                    ValidationResult.ERROR,
                    f"Invalid YAML in agent {agent_file.name}: {e}",
                    "agent_system"
                ))
        
        # Check for essential agents
        for essential in essential_agents:
            if essential not in found_agents:
                validations.append(StructureValidation(
                    ValidationResult.WARNING,
                    f"Missing essential agent: {essential}",
                    "agent_system"
                ))
        
        return validations
    
    def _validate_docs_structure(self) -> List[StructureValidation]:
        """Validate documentation structure"""
        validations = []
        
        docs_dir = self.project_path / "docs"
        if not docs_dir.exists():
            validations.append(StructureValidation(
                ValidationResult.WARNING,
                "Missing docs directory",
                "documentation"
            ))
            return validations
        
        # Expected documentation sections
        expected_sections = [
            "01_ProjectCharter",
            "02_blueprint", 
            "03_TechSpecs",
            "04_Roadmap",
            "05_backlog"
        ]
        
        for section in expected_sections:
            section_path = docs_dir / section
            if section_path.exists():
                validations.append(StructureValidation(
                    ValidationResult.VALID,
                    f"Found documentation section: {section}",
                    "documentation"
                ))
            else:
                validations.append(StructureValidation(
                    ValidationResult.WARNING,
                    f"Missing documentation section: {section}",
                    "documentation"
                ))
        
        return validations

class DocumentSyncer:
    """Synchronizes documents across project components"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
    
    def sync_documents(self, dry_run: bool = False) -> Dict[str, Any]:
        """Sync documents and return sync report"""
        sync_report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "operations": [],
            "errors": [],
            "summary": {}
        }
        
        try:
            # Import PMS core for this project
            sys.path.insert(0, str(self.project_path))
            import pms_core
            
            # Get memory index to understand scope mappings
            memory_index = pms_core._load_memory_index()
            scopes = memory_index.get('scopes', {})
            
            # Sync each scope
            for scope_name, scope_config in scopes.items():
                try:
                    result = self._sync_scope(scope_name, scope_config, dry_run)
                    sync_report["operations"].extend(result["operations"])
                    sync_report["errors"].extend(result["errors"])
                except Exception as e:
                    sync_report["errors"].append({
                        "scope": scope_name,
                        "error": str(e),
                        "type": "sync_error"
                    })
            
            # Generate summary
            sync_report["summary"] = {
                "total_operations": len(sync_report["operations"]),
                "successful_operations": len([op for op in sync_report["operations"] if op["status"] == "success"]),
                "failed_operations": len([op for op in sync_report["operations"] if op["status"] == "failed"]),
                "total_errors": len(sync_report["errors"])
            }
            
        except ImportError as e:
            sync_report["errors"].append({
                "error": f"Failed to import PMS core: {e}",
                "type": "import_error"
            })
        finally:
            # Clean up path
            if str(self.project_path) in sys.path:
                sys.path.remove(str(self.project_path))
        
        return sync_report
    
    def _sync_scope(self, scope_name: str, scope_config: Dict, dry_run: bool) -> Dict[str, List]:
        """Sync individual scope"""
        operations = []
        errors = []
        
        scope_path = Path(scope_config.get('path', ''))
        if not scope_path.exists():
            errors.append({
                "scope": scope_name,
                "error": f"Scope file not found: {scope_path}",
                "type": "file_not_found"
            })
            return {"operations": operations, "errors": errors}
        
        # For now, just validate the file can be read
        try:
            if scope_config.get('type') == 'yaml':
                with open(scope_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            elif scope_config.get('type') == 'markdown':
                with open(scope_path, 'r', encoding='utf-8') as f:
                    f.read()
            
            operations.append({
                "scope": scope_name,
                "operation": "validate",
                "status": "success",
                "message": f"Validated {scope_config.get('type', 'unknown')} file"
            })
            
        except Exception as e:
            operations.append({
                "scope": scope_name,
                "operation": "validate",
                "status": "failed",
                "message": f"Validation failed: {e}"
            })
        
        return {"operations": operations, "errors": errors}

class BlueprintEvaluator:
    """Evaluates blueprint completeness and consistency"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
    
    def evaluate_blueprint(self) -> Dict[str, Any]:
        """Comprehensive blueprint evaluation"""
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "project_path": str(self.project_path),
            "metrics": {},
            "completeness": {},
            "consistency": {},
            "recommendations": []
        }
        
        try:
            # Import PMS core and load blueprint
            sys.path.insert(0, str(self.project_path))
            import pms_core
            
            blueprint_data = pms_core.load('blueprint')
            
            # Evaluate completeness
            evaluation["completeness"] = self._evaluate_completeness(blueprint_data)
            
            # Evaluate consistency with backlog
            evaluation["consistency"] = self._evaluate_consistency(blueprint_data)
            
            # Calculate overall metrics
            evaluation["metrics"] = self._calculate_metrics(evaluation)
            
            # Generate recommendations
            evaluation["recommendations"] = self._generate_recommendations(evaluation)
            
        except ImportError as e:
            evaluation["error"] = f"Failed to import PMS core: {e}"
        except Exception as e:
            evaluation["error"] = f"Blueprint evaluation failed: {e}"
        finally:
            if str(self.project_path) in sys.path:
                sys.path.remove(str(self.project_path))
        
        return evaluation
    
    def _evaluate_completeness(self, blueprint_data: Any) -> Dict[str, Any]:
        """Evaluate blueprint completeness"""
        if isinstance(blueprint_data, str):
            # Markdown blueprint
            sections = self._parse_markdown_sections(blueprint_data)
            
            expected_sections = [
                "Arquitectura", "Componentes", "Base de datos",
                "APIs y servicios", "Decisiones arquitectónicas"
            ]
            
            found_sections = list(sections.keys())
            missing_sections = [s for s in expected_sections if not any(s.lower() in found.lower() for found in found_sections)]
            
            completeness_score = (len(expected_sections) - len(missing_sections)) / len(expected_sections)
            
            return {
                "type": "markdown",
                "score": completeness_score,
                "expected_sections": expected_sections,
                "found_sections": found_sections,
                "missing_sections": missing_sections,
                "total_content_length": len(blueprint_data)
            }
        
        elif isinstance(blueprint_data, dict):
            # YAML blueprint
            expected_keys = ["arquitectura", "componentes", "decisiones_arquitectonicas"]
            found_keys = list(blueprint_data.keys())
            missing_keys = [k for k in expected_keys if k not in found_keys]
            
            completeness_score = (len(expected_keys) - len(missing_keys)) / len(expected_keys)
            
            return {
                "type": "yaml",
                "score": completeness_score,
                "expected_keys": expected_keys,
                "found_keys": found_keys,
                "missing_keys": missing_keys
            }
        
        return {"error": "Unknown blueprint format"}
    
    def _parse_markdown_sections(self, markdown_content: str) -> Dict[str, str]:
        """Parse markdown content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in markdown_content.split('\n'):
            if line.startswith('#'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = line.lstrip('#').strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _evaluate_consistency(self, blueprint_data: Any) -> Dict[str, Any]:
        """Evaluate consistency between blueprint and backlog"""
        consistency_report = {
            "backlog_alignment": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            import pms_core
            
            # Load backlogs for comparison
            backlog_files = list((self.project_path / "docs" / "05_backlog").glob("backlog_f*.yaml"))
            
            total_tasks = 0
            blueprint_aligned_tasks = 0
            
            for backlog_file in backlog_files:
                try:
                    backlog_data = pms_core.load(f"backlog_{backlog_file.stem.split('_')[-1]}")
                    
                    for task_id, task in backlog_data.get('historias', {}).items():
                        total_tasks += 1
                        
                        # Simple heuristic: task description should reference blueprint concepts
                        task_desc = task.get('description', '').lower()
                        blueprint_text = str(blueprint_data).lower()
                        
                        # Check for component/architecture mentions
                        if any(comp in task_desc for comp in ['pms', 'das', 'cli', 'web', 'api']):
                            blueprint_aligned_tasks += 1
                
                except Exception as e:
                    consistency_report["issues"].append(f"Failed to load {backlog_file}: {e}")
            
            if total_tasks > 0:
                consistency_report["backlog_alignment"] = blueprint_aligned_tasks / total_tasks
            
            if consistency_report["backlog_alignment"] < 0.8:
                consistency_report["recommendations"].append(
                    "Consider reviewing backlog tasks to ensure better alignment with blueprint architecture"
                )
        
        except Exception as e:
            consistency_report["issues"].append(f"Consistency check failed: {e}")
        
        return consistency_report
    
    def _calculate_metrics(self, evaluation: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall metrics"""
        completeness_score = evaluation.get("completeness", {}).get("score", 0.0)
        consistency_score = evaluation.get("consistency", {}).get("backlog_alignment", 0.0)
        
        overall_score = (completeness_score + consistency_score) / 2
        
        return {
            "completeness_score": completeness_score,
            "consistency_score": consistency_score,
            "overall_score": overall_score
        }
    
    def _generate_recommendations(self, evaluation: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        completeness = evaluation.get("completeness", {})
        if completeness.get("score", 0) < 0.8:
            missing = completeness.get("missing_sections", []) or completeness.get("missing_keys", [])
            if missing:
                recommendations.append(f"Add missing blueprint sections: {', '.join(missing)}")
        
        consistency = evaluation.get("consistency", {})
        if consistency.get("backlog_alignment", 0) < 0.7:
            recommendations.append("Improve alignment between blueprint architecture and backlog tasks")
        
        recommendations.extend(consistency.get("recommendations", []))
        
        if not recommendations:
            recommendations.append("Blueprint appears well-structured and consistent")
        
        return recommendations

# ---------------------------------------------------------------------------
# Click CLI Interface - TS-CLI-001 Implementation
# ---------------------------------------------------------------------------

@click.group()
@click.version_option()
def cli():
    """DevHub CLI - Project Management and Development Tools"""
    pass

@cli.command()
@click.argument('project_name')
@click.option('--type', 'project_type', default='default', help='Project type template')
@click.option('--overwrite', is_flag=True, help='Overwrite existing project')
def create_project_cmd(project_name: str, project_type: str, overwrite: bool):
    """Create a new DevHub project"""
    creator = ProjectCreator()
    
    click.echo(f"🚀 Creating project: {project_name}")
    click.echo(f"📋 Project type: {project_type}")
    
    if overwrite:
        click.echo("⚠️  Overwrite mode enabled")
    
    success = creator.create_project(project_name, project_type, overwrite)
    
    if success:
        click.echo("✅ Project created successfully!")
        click.echo(f"📁 Next: cd {project_name}")
    else:
        click.echo("❌ Project creation failed")
        sys.exit(1)

@cli.command()
@click.option('--project-path', type=click.Path(exists=True), help='Project path to validate')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
def validate_structure(project_path: str, output_format: str):
    """Validate DevHub project structure"""
    path = Path(project_path) if project_path else Path.cwd()
    
    click.echo(f"🔍 Validating project structure: {path}")
    
    validator = StructureValidator(path)
    validations = validator.validate_project_structure()
    
    if output_format == 'json':
        result = {
            "project_path": str(path),
            "timestamp": datetime.now().isoformat(),
            "validations": [{
                "status": v.status.value,
                "message": v.message,
                "component": v.component,
                "details": v.details
            } for v in validations]
        }
        click.echo(json.dumps(result, indent=2))
    else:
        # Table format
        click.echo("\n" + "=" * 80)
        click.echo("PROJECT STRUCTURE VALIDATION REPORT")
        click.echo("=" * 80)
        
        by_component = {}
        for v in validations:
            if v.component not in by_component:
                by_component[v.component] = []
            by_component[v.component].append(v)
        
        for component, component_validations in by_component.items():
            click.echo(f"\n📦 {component.upper().replace('_', ' ')}:")
            
            for v in component_validations:
                if v.status == ValidationResult.VALID:
                    icon = "✅"
                elif v.status == ValidationResult.WARNING:
                    icon = "⚠️ "
                else:
                    icon = "❌"
                
                click.echo(f"  {icon} {v.message}")
        
        # Summary
        errors = [v for v in validations if v.status == ValidationResult.ERROR]
        warnings = [v for v in validations if v.status == ValidationResult.WARNING]
        valid = [v for v in validations if v.status == ValidationResult.VALID]
        
        click.echo(f"\n📊 SUMMARY:")
        click.echo(f"  ✅ Valid: {len(valid)}")
        click.echo(f"  ⚠️  Warnings: {len(warnings)}")
        click.echo(f"  ❌ Errors: {len(errors)}")
        
        if errors:
            click.echo("\n❌ Critical issues found - project may not function correctly")
        elif warnings:
            click.echo("\n⚠️  Minor issues found - project should function but improvements recommended")
        else:
            click.echo("\n✅ Project structure is valid")

@cli.command()
@click.option('--project-path', type=click.Path(exists=True), help='Project path to sync')
@click.option('--dry-run', is_flag=True, help='Preview changes without executing')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary')
def sync_documents(project_path: str, dry_run: bool, output_format: str):
    """Synchronize project documents"""
    path = Path(project_path) if project_path else Path.cwd()
    
    click.echo(f"🔄 Synchronizing documents: {path}")
    if dry_run:
        click.echo("🔍 DRY RUN - No changes will be made")
    
    syncer = DocumentSyncer(path)
    report = syncer.sync_documents(dry_run)
    
    if output_format == 'json':
        click.echo(json.dumps(report, indent=2))
    elif output_format == 'detailed':
        click.echo(f"\n📋 SYNC REPORT - {report['timestamp']}")
        click.echo("=" * 60)
        
        for operation in report['operations']:
            status_icon = "✅" if operation['status'] == 'success' else "❌"
            click.echo(f"{status_icon} {operation['scope']}: {operation['message']}")
        
        if report['errors']:
            click.echo("\n❌ ERRORS:")
            for error in report['errors']:
                click.echo(f"  • {error['error']}")
        
        click.echo(f"\n📊 Summary: {report['summary']}")
    else:
        # Summary format
        summary = report['summary']
        click.echo(f"\n📊 Sync completed:")
        click.echo(f"  ✅ Successful: {summary.get('successful_operations', 0)}")
        click.echo(f"  ❌ Failed: {summary.get('failed_operations', 0)}")
        click.echo(f"  🚨 Errors: {summary.get('total_errors', 0)}")
        
        if summary.get('total_errors', 0) > 0:
            click.echo("\nUse --format detailed to see error details")

@cli.command()
@click.option('--project-path', type=click.Path(exists=True), help='Project path to evaluate')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary')
def evaluate_blueprint(project_path: str, output_format: str):
    """Evaluate blueprint completeness and consistency"""
    path = Path(project_path) if project_path else Path.cwd()
    
    click.echo(f"📋 Evaluating blueprint: {path}")
    
    evaluator = BlueprintEvaluator(path)
    evaluation = evaluator.evaluate_blueprint()
    
    if 'error' in evaluation:
        click.echo(f"❌ Evaluation failed: {evaluation['error']}")
        sys.exit(1)
    
    if output_format == 'json':
        click.echo(json.dumps(evaluation, indent=2))
    elif output_format == 'detailed':
        click.echo(f"\n📋 BLUEPRINT EVALUATION - {evaluation['timestamp']}")
        click.echo("=" * 70)
        
        # Metrics
        metrics = evaluation['metrics']
        click.echo(f"\n📊 METRICS:")
        click.echo(f"  Completeness: {metrics['completeness_score']:.1%}")
        click.echo(f"  Consistency:  {metrics['consistency_score']:.1%}")
        click.echo(f"  Overall:      {metrics['overall_score']:.1%}")
        
        # Completeness details
        completeness = evaluation['completeness']
        click.echo(f"\n✅ COMPLETENESS ({completeness['score']:.1%}):")
        if 'missing_sections' in completeness:
            missing = completeness['missing_sections']
            if missing:
                click.echo(f"  Missing sections: {', '.join(missing)}")
            else:
                click.echo(f"  All expected sections present")
        
        # Recommendations
        if evaluation['recommendations']:
            click.echo(f"\n💡 RECOMMENDATIONS:")
            for rec in evaluation['recommendations']:
                click.echo(f"  • {rec}")
    else:
        # Summary format
        metrics = evaluation['metrics']
        overall_score = metrics['overall_score']
        
        if overall_score >= 0.8:
            status = "✅ Excellent"
        elif overall_score >= 0.6:
            status = "⚠️  Good"
        else:
            status = "❌ Needs Improvement"
        
        click.echo(f"\n📊 Blueprint Status: {status} ({overall_score:.1%})")

# ---------------------------------------------------------------------------
# Template System Commands - TS-CLI-002 Integration
# ---------------------------------------------------------------------------

@cli.command('create-from-template')
@click.argument('project_name')
@click.option('--template', default='default', help='Template name to use')
@click.option('--description', help='Project description')
@click.option('--author', help='Project author')
@click.option('--output-dir', type=click.Path(), help='Output directory (default: current)')
@click.option('--list-templates', is_flag=True, help='List available templates and exit')
def create_from_template(project_name: str, template: str, description: str, 
                        author: str, output_dir: str, list_templates: bool):
    """Create new DevHub project from template"""
    
    if list_templates:
        click.echo("📋 Available Templates:")
        templates = list_available_templates()
        for tmpl in templates:
            click.echo(f"  • {tmpl.name}: {tmpl.description}")
        return
    
    # Validate template
    issues = validate_template_by_name(template)
    if issues:
        click.echo(f"❌ Template '{template}' has issues:")
        for issue in issues:
            click.echo(f"  • {issue}")
        sys.exit(1)
    
    click.echo(f"🚀 Creating project '{project_name}' from template '{template}'")
    
    # Create template engine
    engine = DevHubTemplateEngine()
    
    # Prepare context data
    context_data = {}
    if description:
        context_data['description'] = description
    if author:
        context_data['author'] = author
    
    # Create project
    success = engine.create_devhub_project(
        project_name=project_name,
        template_name=template,
        project_description=description or f"DevHub project: {project_name}",
        author=author or "DevHub User",
        output_dir=Path(output_dir) if output_dir else None
    )
    
    if success:
        click.echo("✅ Project created successfully!")
        click.echo(f"📁 Location: {output_dir or '.'}/{project_name}")
        click.echo("\n📋 Next steps:")
        click.echo("  1. cd into project directory")
        click.echo("  2. Review and customize configuration files")
        click.echo("  3. Run 'python devhub_cli.py validate-structure' to verify setup")
    else:
        click.echo("❌ Failed to create project from template")
        sys.exit(1)

@cli.command('list-templates')
def list_templates_cmd():
    """List all available project templates"""
    click.echo("📋 Available DevHub Templates:")
    click.echo("=" * 50)
    
    templates = list_available_templates()
    
    if not templates:
        click.echo("No templates found in docs/doc_templates/")
        return
    
    for tmpl in templates:
        click.echo(f"\n📄 {tmpl.name}")
        click.echo(f"   Description: {tmpl.description}")
        if tmpl.files:
            click.echo(f"   Files: {len(tmpl.files)} template files")
        if tmpl.directories:
            click.echo(f"   Directories: {len(tmpl.directories)} directories")
        
        # Validate template
        issues = validate_template_by_name(tmpl.name)
        if issues:
            click.echo(f"   ⚠️  Issues: {len(issues)} validation issues")
        else:
            click.echo(f"   ✅ Status: Valid")

@cli.command('validate-template')
@click.argument('template_name')
def validate_template_cmd(template_name: str):
    """Validate a specific template"""
    click.echo(f"🔍 Validating template: {template_name}")
    
    issues = validate_template_by_name(template_name)
    
    if not issues:
        click.echo("✅ Template is valid and ready to use")
    else:
        click.echo(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            click.echo(f"  • {issue}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Agent Execution Commands - TS-CLI-003 CLI Integration
# ---------------------------------------------------------------------------

@cli.command('agent-run')
@click.argument('agent_id')
@click.argument('task_id')
@click.option('--timeout', default=300, type=int, help='Execution timeout in seconds')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--report', is_flag=True, help='Generate detailed execution report')
def agent_run(agent_id: str, task_id: str, timeout: int, format: str, report: bool):
    """Execute a specific task with an agent"""
    
    click.echo(f"🚀 Executing task '{task_id}' with agent '{agent_id}'")
    click.echo(f"⏱️  Timeout: {timeout} seconds")
    
    try:
        # Create agent runner
        runner = AgentRunner(agent_id)
        
        # Execute task
        result = runner.execute_task(task_id, timeout)
        
        # Format output
        if format == 'json':
            output_data = {
                'success': result.success,
                'agent_id': result.agent_id,
                'task_id': result.task_id,
                'execution_time': result.execution_time,
                'output': result.output,
                'error': result.error,
                'metadata': result.metadata
            }
            click.echo(json.dumps(output_data, indent=2))
        else:
            # Text format
            status_icon = "✅" if result.success else "❌"
            click.echo(f"\n{status_icon} Execution Result:")
            click.echo(f"   Agent: {result.agent_id}")
            click.echo(f"   Task: {result.task_id}")
            click.echo(f"   Duration: {result.execution_time:.2f}s")
            
            if result.success:
                click.echo(f"   Status: SUCCESS")
                click.echo(f"\n📋 Output:")
                click.echo(result.output)
            else:
                click.echo(f"   Status: FAILED")
                click.echo(f"   Error: {result.error}")
        
        # Generate report if requested
        if report:
            _generate_execution_report(result)
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except Exception as e:
        click.echo(f"❌ Failed to execute task: {e}")
        sys.exit(1)

@cli.command('list-agents')
def list_agents():
    """List all available agents and their capabilities"""
    click.echo("📋 Available DevHub Agents:")
    click.echo("=" * 50)
    
    try:
        # Load memory index to get agent configurations
        with open('memory/memory_index.yaml', 'r') as f:
            memory_index = yaml.safe_load(f)
        
        agents = memory_index.get('agents', {})
        
        for agent_key, agent_path in agents.items():
            try:
                # Map agent keys to proper agent IDs
                agent_mappings = {
                    'ai_project_manager': 'AiProjectManager',
                    'blueprint_agent': 'BluePrintAgent', 
                    'dev_agent': 'DevAgent',
                    'prompt_agent': 'PromptAgent'
                }
                
                agent_id = agent_mappings.get(agent_key, agent_key)
                config = validate_agent_config(agent_id)
                
                if config:
                    click.echo(f"\n🤖 {agent_id}")
                    click.echo(f"   Config: {agent_path}")
                    click.echo(f"   Read Scopes: {', '.join(config.get('read_scopes', []))}")
                    click.echo(f"   Write Scopes: {', '.join(config.get('write_scopes', []))}")
                    click.echo(f"   Mode: {config.get('mode', 'unknown')}")
                    
                    enforcement_status = "✅ Enabled" if config.get('enforcement_enabled') else "⚠️ Disabled"
                    click.echo(f"   Enforcement: {enforcement_status}")
                else:
                    click.echo(f"\n❌ {agent_key} (invalid configuration)")
                    
            except Exception as e:
                click.echo(f"\n❌ {agent_key} (error: {e})")
                
    except Exception as e:
        click.echo(f"❌ Failed to load agent configurations: {e}")

def _generate_execution_report(result: ExecutionResult) -> None:
    """Generate detailed execution report"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f"execution_report_{result.agent_id}_{result.task_id}_{timestamp}.md"
    
    report_content = f"""# Agent Execution Report

## Summary
- **Agent ID:** {result.agent_id}
- **Task ID:** {result.task_id}
- **Execution Time:** {result.execution_time:.2f} seconds
- **Status:** {"SUCCESS" if result.success else "FAILED"}
- **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Output
```
{result.output}
```

## Error Details
{result.error if result.error else "No errors reported"}

## Metadata
```json
{json.dumps(result.metadata, indent=2) if result.metadata else "No metadata available"}
```

---
*Generated by DevHub CLI agent-run command*
"""
    
    try:
        with open(report_file, 'w') as f:
            f.write(report_content)
        click.echo(f"📝 Execution report saved: {report_file}")
    except Exception as e:
        click.echo(f"⚠️  Failed to save report: {e}")

@cli.command()
def list_projects():
    """List all DevHub projects"""
    list_projects()

# Legacy argparse support for backward compatibility
def main():
    """Main entry point - delegates to Click CLI"""
    cli()


def _configure_devagent_for_project(devagent_config: Path, project_name: str, project_path: Path) -> None:
    """Configure DevAgent.yaml with project-specific context"""
    
    with open(devagent_config, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add project context to agent_info section
    project_context_addition = f"""
  project_name: "{project_name}"
  project_path: "{project_path.absolute()}"
  context: "Trabajando exclusivamente en el proyecto {project_name}"""
    
    # Add project context after the purpose line
    modified_content = content.replace(
        'purpose: "Ejecutor autónomo de tareas de desarrollo siguiendo blueprint y backlog"',
        f'purpose: "Ejecutor autónomo de tareas de desarrollo siguiendo blueprint y backlog"{project_context_addition}'
    )
    
    # Update responsibilities to be project-specific
    modified_content = modified_content.replace(
        '- "Leer configuración del sistema PMS"',
        f'- "Leer configuración del sistema PMS LOCAL del proyecto {project_name}"'
    ).replace(
        '- "Interpretar blueprint para contexto del proyecto"',
        f'- "Interpretar blueprint para contexto del proyecto {project_name}"'
    ).replace(
        '- "Seleccionar y ejecutar tareas del backlog"',
        f'- "Seleccionar y ejecutar tareas del backlog LOCAL del proyecto"'
    ).replace(
        '- "Registrar progreso y actualizar estado del proyecto"',
        f'- "Registrar progreso y actualizar estado del proyecto LOCAL"'
    ).replace(
        '- "Mantener ciclo de desarrollo continuo"',
        f'- "Mantener ciclo de desarrollo continuo DENTRO del proyecto {project_name}"'
    )
    
    # Add project-specific restrictions
    project_restrictions = f"""
  
  project_context:
    working_directory: "{project_path.absolute()}"
    project_name: "{project_name}"
    rule: "DevAgent trabaja EXCLUSIVAMENTE dentro del directorio del proyecto {project_name}"
    enforcement:
      - "NUNCA acceder a directorios padre del proyecto"
      - "NUNCA usar rutas absolutas fuera del proyecto"
      - "SIEMPRE usar PMS y DAS locales del proyecto"
      - "Todos los archivos están DENTRO del contexto del proyecto"
      - "Violaciones de contexto del proyecto generan PermissionError"""
    
    # Add project context before restrictions section
    if 'restrictions:' in modified_content:
        modified_content = modified_content.replace(
            'restrictions:',
            f'restrictions:{project_restrictions}\n\n  file_restrictions:'
        )
    
    # Write the enhanced configuration
    with open(devagent_config, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"✅ Configured DevAgent for project '{project_name}' context")


if __name__ == "__main__":
    main()