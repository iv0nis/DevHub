# {{ project.display_name }}

{{ project.description }}

## Project Information

- **Project Name**: {{ project.name }}
- **Version**: {{ project.version }}
- **Author**: {{ project.author }}
- **Created**: {{ project.created_at.strftime('%Y-%m-%d') }}
- **DevHub Version**: {{ custom.devhub_version }}

## Architecture

This project follows the DevHub architecture with three main pillars:

### 1. PMS (Persistent Memory System)
- **Location**: `pms/`
- **Purpose**: Data persistence with integrity validation and transactions
- **Key Features**: SHA-1 validation, atomic operations, rollback support

### 2. DAS (DevAgent System) 
- **Location**: `das/` and `agents/`
- **Purpose**: Agent orchestration with permission enforcement
- **Key Features**: Permission validation, audit logging, agent lifecycle management

### 3. Core Components
- **Location**: `core/`
- **Purpose**: Event system, configuration management, templates
- **Key Features**: Event-driven architecture, multi-environment configs

## Directory Structure

```
{{ project.name }}/
├── docs/                   # Documentation
│   ├── 01_ProjectCharter/  # Project charter and vision
│   ├── 02_blueprint/       # Architecture blueprint
│   ├── 03_TechSpecs/      # Technical specifications
│   ├── 04_Roadmap/        # Project roadmap
│   └── 05_backlog/        # Task backlogs by phase
├── memory/                 # PMS data storage
├── pms/                    # PMS core system
├── das/                    # DAS enforcement system
├── agents/                 # Agent configurations
├── core/                   # Core components (events, config, templates)
├── tests/                  # Test suites
├── config/                 # Environment configurations
└── logs/                   # Application logs
```

## Getting Started

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Setup development environment
export DEVHUB_ENV=development
```

### 2. Verify Installation

```bash
# Test PMS system
python -c "import pms_core; print('✅ PMS operational')"

# Test DAS system 
python -c "from das.enforcer import validate_agent_config; print('✅ DAS operational:', validate_agent_config('DevAgent'))"

# Test configuration system
python -c "from core.config import get_config; print('✅ Config system:', get_config().environment.value)"
```

### 3. Development Workflow

```bash
# Activate DevAgent for task execution
python -c "from das.enforcer import agent_load; print('Current backlog:', agent_load('DevAgent', 'backlog_f0'))"

# Run validation
python -c "from core.config import validate_current_config; issues = validate_current_config(); print('✅ Config valid' if not issues else f'Issues: {issues}')"
```

## Configuration

The project supports multiple environments:

- **Development**: `config/development.yaml` (default)
- **Production**: `config/production.yaml` 
- **Testing**: `config/testing.yaml`

Switch environments:
```bash
export DEVHUB_ENV=production
```

## Agent System

DevAgent is pre-configured for task execution with the following permissions:

- **Read**: `memory_index`, `backlog_f*`, `blueprint`, `project_status`, `techspecs`
- **Write**: `backlog_f*`, `project_status`, `blueprint_changes`, `techspecs`
- **Enforcement**: Enabled with strict mode

## Event System

The project includes a complete event-driven architecture:

```python
from core.event_system import get_event_publisher, SystemEvent, EventType

publisher = get_event_publisher()
await publisher.publish(SystemEvent(
    event_type=EventType.PROJECT_CREATED,
    data={'project_name': '{{ project.name }}'}
))
```

## Contributing

1. Follow the DevHub development workflow
2. Use DevAgent for task execution
3. Maintain documentation in respective docs/ sections
4. Test changes before committing

## License

{{ project.license }}

---

Generated with [DevHub Template System](https://github.com/devhub) v{{ custom.devhub_version }}