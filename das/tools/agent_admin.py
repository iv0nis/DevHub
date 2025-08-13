#!/usr/bin/env python3
"""
DAS Agent Administration Tool
Comprehensive tool for managing DevHub agents and permissions.

Usage:
    python das/tools/agent_admin.py [command] [options]
    
Commands:
    list                    - List all agents
    permissions [agent]     - Show agent permissions
    matrix                  - Show permission matrix
    test [agent] [scope]    - Test agent access to scope
    audit [agent]           - Show agent activity
    reload                  - Reload agent configurations
    validate [agent]        - Detailed validation of agent config
"""
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from das.enforcer import (
        list_all_agents,
        get_agent_permissions_summary,
        validate_scope_access,
        get_permission_matrix,
        audit_agent_activity,
        reload_agent_configs,
        validate_agent_config,
        test_permission
    )
except ImportError as e:
    print(f"❌ Error importing DAS enforcer: {e}")
    sys.exit(1)

def cmd_list_agents(args):
    """List all available agents"""
    print("=== Available Agents ===")
    agents = list_all_agents()
    
    if not agents:
        print("No agents found")
        return
    
    for agent in agents:
        try:
            config = validate_agent_config(agent)
            enforcement = "ON" if config['enforcement_enabled'] else "OFF"
            mode = "strict" if config.get('strict_mode', False) else "warning"
            print(f"✅ {agent:20} | Enforcement: {enforcement:3} ({mode})")
        except Exception as e:
            print(f"❌ {agent:20} | Error: {e}")

def cmd_show_permissions(args):
    """Show permissions for specific agent or all agents"""
    if args.agent:
        agents = [args.agent]
    else:
        agents = list_all_agents()
    
    print("=== Agent Permissions ===")
    
    for agent in agents:
        try:
            config = validate_agent_config(agent)
            print(f"\n--- {agent} ---")
            print(f"Read scopes:  {', '.join(config['read_scopes'])}")
            print(f"Write scopes: {', '.join(config['write_scopes'])}")
            print(f"Mode:         {config['mode']}")
            print(f"Enforcement:  {'ON' if config['enforcement_enabled'] else 'OFF'}")
            print(f"Strict mode:  {'Yes' if config.get('strict_mode', False) else 'No'}")
            
        except Exception as e:
            print(f"\n--- {agent} ---")
            print(f"❌ Error: {e}")

def cmd_permission_matrix(args):
    """Display comprehensive permission matrix"""
    print("=== Permission Matrix ===")
    
    try:
        matrix = get_permission_matrix()
        agents = list(matrix.keys())
        scopes = set()
        for agent_scopes in matrix.values():
            scopes.update(agent_scopes.keys())
        scopes = sorted(list(scopes))
        
        # Header
        print(f"{'Agent':<20}", end='')
        for scope in scopes:
            print(f"{scope:<15}", end='')
        print()
        print("-" * (20 + len(scopes) * 15))
        
        # Rows
        for agent in agents:
            print(f"{agent:<20}", end='')
            for scope in scopes:
                perm = matrix[agent].get(scope, '--')
                color_perm = perm
                if perm == 'RW':
                    color_perm = f"✅{perm}"
                elif perm == 'R-':
                    color_perm = f"📖{perm}"
                elif perm == '--':
                    color_perm = f"❌{perm}"
                print(f"{color_perm:<15}", end='')
            print()
        
        print("\nLegend:")
        print("  RW = Read + Write")
        print("  R- = Read Only")
        print("  -W = Write Only")
        print("  -- = No Access")
        print("  ERR = Error")
        
    except Exception as e:
        print(f"❌ Error generating matrix: {e}")

def cmd_test_access(args):
    """Test agent access to specific scope"""
    if not args.agent or not args.scope:
        print("❌ Usage: test [agent] [scope]")
        return
    
    print(f"=== Testing {args.agent} access to {args.scope} ===")
    
    operations = ['load', 'save']
    
    for operation in operations:
        try:
            result = validate_scope_access(args.agent, args.scope, operation)
            
            if result['allowed']:
                print(f"✅ {operation.upper()}: Allowed")
                print(f"   Reason: {result['reason']}")
                if 'matched_pattern' in result:
                    print(f"   Pattern: {result['matched_pattern']}")
            else:
                print(f"❌ {operation.upper()}: Denied")
                print(f"   Reason: {result['reason']}")
                
        except Exception as e:
            print(f"❌ {operation.upper()}: Error - {e}")

def cmd_audit_activity(args):
    """Show recent activity for agent"""
    if not args.agent:
        print("❌ Usage: audit [agent]")
        return
    
    print(f"=== Recent Activity for {args.agent} ===")
    
    try:
        activities = audit_agent_activity(args.agent, limit=args.limit or 10)
        
        if not activities:
            print("No recent activity found")
            return
        
        for activity in activities:
            timestamp = activity['timestamp'][:19]  # Remove microseconds
            scope = activity['scope']
            operation = activity['operation']
            success = '✅' if activity['success'] else '❌'
            details = activity.get('details', '')
            
            print(f"{success} {timestamp} | {operation:4} {scope:15} | {details}")
            
    except Exception as e:
        print(f"❌ Error retrieving audit data: {e}")

def cmd_reload_configs(args):
    """Reload all agent configurations"""
    print("=== Reloading Agent Configurations ===")
    
    try:
        reload_agent_configs()
        print("✅ Agent configurations reloaded successfully")
        
        # Verify by listing agents
        agents = list_all_agents()
        print(f"✅ {len(agents)} agent configurations available")
        
    except Exception as e:
        print(f"❌ Error reloading configurations: {e}")

def cmd_validate_agent(args):
    """Detailed validation of specific agent"""
    if not args.agent:
        print("❌ Usage: validate [agent]")
        return
    
    print(f"=== Validating {args.agent} ===")
    
    try:
        config = validate_agent_config(args.agent)
        
        print("✅ Configuration is valid")
        print(f"   Read scopes: {len(config['read_scopes'])} defined")
        print(f"   Write scopes: {len(config['write_scopes'])} defined")
        print(f"   Enforcement: {'Enabled' if config['enforcement_enabled'] else 'Disabled'}")
        
        # Test basic functionality
        print("\n--- Testing Basic Operations ---")
        test_scopes = ['project_status', 'blueprint', 'backlog_f1']
        
        for scope in test_scopes:
            can_read = test_permission(args.agent, 'load', scope)
            can_write = test_permission(args.agent, 'save', scope)
            
            read_status = '✅' if can_read else '❌'
            write_status = '✅' if can_write else '❌'
            
            print(f"   {scope:15} | Read: {read_status} Write: {write_status}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="DAS Agent Administration Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all agents')
    
    # Permissions command
    perms_parser = subparsers.add_parser('permissions', help='Show agent permissions')
    perms_parser.add_argument('agent', nargs='?', help='Specific agent name')
    
    # Matrix command
    subparsers.add_parser('matrix', help='Show permission matrix')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test agent access to scope')
    test_parser.add_argument('agent', help='Agent name')
    test_parser.add_argument('scope', help='Scope to test')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Show agent activity')
    audit_parser.add_argument('agent', help='Agent name')
    audit_parser.add_argument('--limit', type=int, default=10, help='Number of entries to show')
    
    # Reload command
    subparsers.add_parser('reload', help='Reload agent configurations')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Detailed validation of agent config')
    validate_parser.add_argument('agent', help='Agent name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    command_handlers = {
        'list': cmd_list_agents,
        'permissions': cmd_show_permissions,
        'matrix': cmd_permission_matrix,
        'test': cmd_test_access,
        'audit': cmd_audit_activity,
        'reload': cmd_reload_configs,
        'validate': cmd_validate_agent
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        try:
            handler(args)
            return 0
        except KeyboardInterrupt:
            print("\n⚠️ Operation cancelled")
            return 1
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return 1
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())