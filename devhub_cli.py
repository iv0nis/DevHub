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
from typing import Optional
import argparse


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


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='DevHub Project Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create project command
    create_parser = subparsers.add_parser('create', help='Create a new project')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('--type', default='default', help='Project type (default: default)')
    create_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing project')
    
    # List projects command
    subparsers.add_parser('list', help='List all projects')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        success = create_project(args.name, args.type, args.overwrite)
        sys.exit(0 if success else 1)
    elif args.command == 'list':
        list_projects()
    else:
        parser.print_help()


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