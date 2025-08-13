#!/usr/bin/env python3
"""
DAS Agent Configuration Synchronization Tool
Ensures all agent configurations follow the standard format and are properly validated.

Usage:
    python das/tools/sync_agent_configs.py [--validate-only] [--fix-issues]
"""
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def load_agent_config(agent_path: Path) -> Dict[str, Any]:
    """Load agent configuration from YAML file"""
    try:
        with open(agent_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading {agent_path}: {e}")
        return {}

def validate_agent_config(agent_name: str, config: Dict[str, Any]) -> List[str]:
    """Validate agent configuration against standard requirements"""
    issues = []
    
    # Check required top-level sections
    required_sections = ['pms_scopes', 'enforcement']
    for section in required_sections:
        if section not in config:
            issues.append(f"Missing required section: {section}")
    
    # Validate pms_scopes
    if 'pms_scopes' in config:
        pms_scopes = config['pms_scopes']
        
        # Check required fields
        required_pms_fields = ['read', 'write', 'mode']
        for field in required_pms_fields:
            if field not in pms_scopes:
                issues.append(f"Missing pms_scopes.{field}")
        
        # Validate read/write scopes are lists
        for scope_type in ['read', 'write']:
            if scope_type in pms_scopes:
                if not isinstance(pms_scopes[scope_type], list):
                    issues.append(f"pms_scopes.{scope_type} must be a list")
        
        # Validate mode
        valid_modes = ['update_single', 'update_dual']
        if 'mode' in pms_scopes and pms_scopes['mode'] not in valid_modes:
            issues.append(f"pms_scopes.mode must be one of: {valid_modes}")
    
    # Validate enforcement
    if 'enforcement' in config:
        enforcement = config['enforcement']
        
        required_enforcement_fields = ['enabled', 'strict_mode', 'log_violations']
        for field in required_enforcement_fields:
            if field not in enforcement:
                issues.append(f"Missing enforcement.{field}")
            elif not isinstance(enforcement[field], bool):
                issues.append(f"enforcement.{field} must be boolean")
    
    return issues

def get_agent_summary(agent_name: str, config: Dict[str, Any]) -> str:
    """Generate human-readable summary of agent configuration"""
    if not config:
        return f"{agent_name}: ❌ Failed to load configuration"
    
    pms_scopes = config.get('pms_scopes', {})
    enforcement = config.get('enforcement', {})
    
    read_scopes = pms_scopes.get('read', [])
    write_scopes = pms_scopes.get('write', [])
    mode = pms_scopes.get('mode', 'unknown')
    
    enabled = enforcement.get('enabled', False)
    strict = enforcement.get('strict_mode', False)
    
    summary = f"{agent_name}:\n"
    summary += f"  Read: {read_scopes}\n"
    summary += f"  Write: {write_scopes}\n"
    summary += f"  Mode: {mode}\n"
    summary += f"  Enforcement: {'ON' if enabled else 'OFF'} ({'strict' if strict else 'warning'} mode)"
    
    return summary

def test_das_integration(agent_name: str) -> bool:
    """Test if agent configuration works with DAS Enforcer"""
    try:
        from das.enforcer import validate_agent_config
        validate_agent_config(agent_name)
        return True
    except Exception as e:
        print(f"❌ DAS integration test failed for {agent_name}: {e}")
        return False

def main():
    """Main synchronization and validation logic"""
    print("=== DAS Agent Configuration Sync & Validation ===")
    
    # Find agent configuration files
    agents_dir = Path("agents")
    agent_files = list(agents_dir.glob("*.yaml"))
    
    if not agent_files:
        print("❌ No agent configuration files found in agents/")
        return 1
    
    print(f"Found {len(agent_files)} agent configurations")
    
    all_valid = True
    
    for agent_file in agent_files:
        agent_name = agent_file.stem
        print(f"\n--- {agent_name} ---")
        
        # Load configuration
        config = load_agent_config(agent_file)
        if not config:
            all_valid = False
            continue
        
        # Validate configuration
        issues = validate_agent_config(agent_name, config)
        
        if issues:
            print(f"❌ Validation issues:")
            for issue in issues:
                print(f"   - {issue}")
            all_valid = False
        else:
            print("✅ Configuration valid")
        
        # Test DAS integration
        if test_das_integration(agent_name):
            print("✅ DAS integration working")
        else:
            all_valid = False
        
        # Show summary
        print("\n" + get_agent_summary(agent_name, config))
    
    # Final summary
    print(f"\n=== SUMMARY ===")
    if all_valid:
        print("✅ All agent configurations are valid and working with DAS Enforcer")
        return 0
    else:
        print("❌ Some agent configurations have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())