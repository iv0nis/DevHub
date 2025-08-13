# -*- coding: utf-8 -*-
"""DevHub Component Integration - TS-ARCH-001

Integration layer that connects Event System with existing DevHub components.
Provides event decorators and integration adapters for PMS, DAS, CLI, and Web.

Usage:
    from core.integration import EventIntegration, event_emitter
    
    # Initialize integration
    integration = EventIntegration()
    integration.setup_all_integrations()
    
    # Use decorator for automatic event emission
    @event_emitter(EventType.TASK_STARTED, source_component='devagent')
    def start_task(task_id):
        return {'task_id': task_id}
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Union
from functools import wraps
from core.event_system import (
    EventPublisher, SystemEvent, EventType, EventSubscriber,
    get_event_publisher, create_task_event, create_pms_event, create_das_event
)
from core.observers import ComponentObserver, TaskObserver, PMSObserver, DASObserver

logger = logging.getLogger("devhub.integration")

# ---------------------------------------------------------------------------
# Event Decorators for Component Integration
# ---------------------------------------------------------------------------

def event_emitter(event_type: EventType, source_component: str = None, 
                 extract_data: Callable = None, correlation_id_field: str = None):
    """Decorator to automatically emit events from function calls
    
    Args:
        event_type: Type of event to emit
        source_component: Source component name
        extract_data: Function to extract event data from function args/result
        correlation_id_field: Name of argument that contains correlation ID
    
    Usage:
        @event_emitter(EventType.TASK_STARTED, source_component='devagent')
        def execute_task(task_id, task_data):
            return {'task_id': task_id, 'result': 'success'}
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get correlation ID if specified
            correlation_id = None
            if correlation_id_field and correlation_id_field in kwargs:
                correlation_id = kwargs[correlation_id_field]
            
            # Execute original function
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Extract event data
                event_data = {}
                if extract_data:
                    event_data = extract_data(*args, result=result, **kwargs)
                elif isinstance(result, dict):
                    event_data = result
                
                # Emit success event
                publisher = get_event_publisher()
                event = SystemEvent(
                    event_type=event_type,
                    source_component=source_component or func.__module__,
                    data=event_data,
                    correlation_id=correlation_id
                )
                await publisher.publish(event)
                
                return result
                
            except Exception as e:
                # Emit error event
                publisher = get_event_publisher()
                error_event = SystemEvent(
                    event_type=EventType.SYSTEM_ERROR,
                    source_component=source_component or func.__module__,
                    data={
                        'function_name': func.__name__,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'args': str(args),
                        'kwargs': str(kwargs)
                    },
                    correlation_id=correlation_id
                )
                await publisher.publish(error_event)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, create async wrapper and run in event loop
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            except RuntimeError:
                # No event loop running, create new one
                return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def task_event_emitter(extract_task_id: Callable[[Any], str] = None):
    """Specialized decorator for task-related events
    
    Args:
        extract_task_id: Function to extract task_id from function arguments
    """
    def extract_data(*args, result=None, **kwargs):
        task_id = None
        if extract_task_id:
            task_id = extract_task_id(*args, **kwargs)
        elif 'task_id' in kwargs:
            task_id = kwargs['task_id']
        elif args and hasattr(args[0], 'task_id'):
            task_id = getattr(args[0], 'task_id')
        
        data = {'task_id': task_id} if task_id else {}
        if isinstance(result, dict):
            data.update(result)
        
        return data
    
    return event_emitter(
        EventType.TASK_STARTED,  # Will be overridden by specific task events
        source_component='devagent',
        extract_data=extract_data,
        correlation_id_field='correlation_id'
    )

# ---------------------------------------------------------------------------
# Component Integration Adapters
# ---------------------------------------------------------------------------

class EventIntegration:
    """Main integration coordinator for DevHub event system"""
    
    def __init__(self):
        self.publisher = get_event_publisher()
        self.observers = {}
        self.subscribers = {}
        self.integration_status = {}
        
        logger.info("EventIntegration initialized")
    
    def setup_all_integrations(self) -> None:
        """Setup integration with all DevHub components"""
        self.setup_pms_integration()
        self.setup_das_integration()
        self.setup_cli_integration()
        self.setup_task_integration()
        
        logger.info("All component integrations setup complete")
    
    def setup_pms_integration(self) -> None:
        """Setup integration with PMS (Persistent Memory System)"""
        try:
            # Create PMS observer
            pms_observer = PMSObserver("pms_integration_observer")
            self.observers['pms'] = pms_observer
            
            # Setup event subscribers for PMS events
            pms_subscriber = EventSubscriber("pms_integration_subscriber")
            
            # Subscribe to PMS events
            pms_subscriber.subscribe(EventType.PMS_DATA_LOADED, self._handle_pms_data_event)
            pms_subscriber.subscribe(EventType.PMS_DATA_SAVED, self._handle_pms_data_event)
            pms_subscriber.subscribe(EventType.PMS_SCHEMA_VALIDATED, self._handle_pms_schema_event)
            pms_subscriber.subscribe(EventType.PMS_TRANSACTION_STARTED, self._handle_pms_transaction_event)
            
            self.subscribers['pms'] = pms_subscriber
            self.publisher.subscribe(EventType.PMS_DATA_LOADED, self._handle_pms_data_event, pms_subscriber)
            self.publisher.subscribe(EventType.PMS_DATA_SAVED, self._handle_pms_data_event, pms_subscriber)
            self.publisher.subscribe(EventType.PMS_SCHEMA_VALIDATED, self._handle_pms_schema_event, pms_subscriber)
            self.publisher.subscribe(EventType.PMS_TRANSACTION_STARTED, self._handle_pms_transaction_event, pms_subscriber)
            
            self.integration_status['pms'] = 'active'
            logger.info("PMS integration setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup PMS integration: {e}")
            self.integration_status['pms'] = 'failed'
    
    def setup_das_integration(self) -> None:
        """Setup integration with DAS (DevAgent System)"""
        try:
            # Create DAS observer
            das_observer = DASObserver("das_integration_observer")
            self.observers['das'] = das_observer
            
            # Setup event subscribers for DAS events
            das_subscriber = EventSubscriber("das_integration_subscriber")
            
            # Subscribe to DAS events
            das_subscriber.subscribe(EventType.DAS_AGENT_STARTED, self._handle_das_agent_event)
            das_subscriber.subscribe(EventType.DAS_PERMISSION_VIOLATION, self._handle_das_violation_event)
            das_subscriber.subscribe(EventType.DAS_AUDIT_LOG_ENTRY, self._handle_das_audit_event)
            
            self.subscribers['das'] = das_subscriber
            self.publisher.subscribe(EventType.DAS_AGENT_STARTED, self._handle_das_agent_event, das_subscriber)
            self.publisher.subscribe(EventType.DAS_PERMISSION_VIOLATION, self._handle_das_violation_event, das_subscriber)
            self.publisher.subscribe(EventType.DAS_AUDIT_LOG_ENTRY, self._handle_das_audit_event, das_subscriber)
            
            self.integration_status['das'] = 'active'
            logger.info("DAS integration setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup DAS integration: {e}")
            self.integration_status['das'] = 'failed'
    
    def setup_cli_integration(self) -> None:
        """Setup integration with CLI component"""
        try:
            cli_subscriber = EventSubscriber("cli_integration_subscriber")
            
            # Subscribe to CLI events
            cli_subscriber.subscribe(EventType.CLI_COMMAND_EXECUTED, self._handle_cli_command_event)
            cli_subscriber.subscribe(EventType.CLI_PROJECT_VALIDATED, self._handle_cli_validation_event)
            cli_subscriber.subscribe(EventType.CLI_DOCUMENTS_SYNCED, self._handle_cli_sync_event)
            cli_subscriber.subscribe(EventType.CLI_BLUEPRINT_EVALUATED, self._handle_cli_blueprint_event)
            
            self.subscribers['cli'] = cli_subscriber
            self.publisher.subscribe(EventType.CLI_COMMAND_EXECUTED, self._handle_cli_command_event, cli_subscriber)
            self.publisher.subscribe(EventType.CLI_PROJECT_VALIDATED, self._handle_cli_validation_event, cli_subscriber)
            self.publisher.subscribe(EventType.CLI_DOCUMENTS_SYNCED, self._handle_cli_sync_event, cli_subscriber)
            self.publisher.subscribe(EventType.CLI_BLUEPRINT_EVALUATED, self._handle_cli_blueprint_event, cli_subscriber)
            
            self.integration_status['cli'] = 'active'
            logger.info("CLI integration setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup CLI integration: {e}")
            self.integration_status['cli'] = 'failed'
    
    def setup_task_integration(self) -> None:
        """Setup integration with task management"""
        try:
            # Create task observer
            task_observer = TaskObserver("task_integration_observer")
            self.observers['task'] = task_observer
            
            # Setup task event subscribers
            task_subscriber = EventSubscriber("task_integration_subscriber")
            
            # Subscribe to task lifecycle events
            task_subscriber.subscribe(EventType.TASK_STARTED, self._handle_task_lifecycle_event)
            task_subscriber.subscribe(EventType.TASK_COMPLETED, self._handle_task_lifecycle_event)
            task_subscriber.subscribe(EventType.TASK_FAILED, self._handle_task_lifecycle_event)
            task_subscriber.subscribe(EventType.TASK_UPDATED, self._handle_task_lifecycle_event)
            
            self.subscribers['task'] = task_subscriber
            self.publisher.subscribe(EventType.TASK_STARTED, self._handle_task_lifecycle_event, task_subscriber)
            self.publisher.subscribe(EventType.TASK_COMPLETED, self._handle_task_lifecycle_event, task_subscriber)
            self.publisher.subscribe(EventType.TASK_FAILED, self._handle_task_lifecycle_event, task_subscriber)
            self.publisher.subscribe(EventType.TASK_UPDATED, self._handle_task_lifecycle_event, task_subscriber)
            
            self.integration_status['task'] = 'active'
            logger.info("Task integration setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup task integration: {e}")
            self.integration_status['task'] = 'failed'
    
    # Event Handlers
    def _handle_pms_data_event(self, event: SystemEvent) -> None:
        """Handle PMS data events"""
        scope = event.data.get('scope')
        operation = event.data.get('operation', 'unknown')
        success = event.data.get('success', True)
        
        if success:
            logger.info(f"PMS {operation} successful for scope: {scope}")
        else:
            logger.error(f"PMS {operation} failed for scope: {scope}")
    
    def _handle_pms_schema_event(self, event: SystemEvent) -> None:
        """Handle PMS schema validation events"""
        scope = event.data.get('scope')
        valid = event.data.get('valid', True)
        
        if valid:
            logger.info(f"Schema validation passed for scope: {scope}")
        else:
            logger.warning(f"Schema validation failed for scope: {scope}")
    
    def _handle_pms_transaction_event(self, event: SystemEvent) -> None:
        """Handle PMS transaction events"""
        transaction_id = event.data.get('transaction_id')
        scopes = event.data.get('affected_scopes', [])
        
        logger.info(f"PMS transaction {transaction_id} affects scopes: {scopes}")
    
    def _handle_das_agent_event(self, event: SystemEvent) -> None:
        """Handle DAS agent events"""
        agent_name = event.data.get('agent_name')
        operation = event.data.get('operation', 'unknown')
        
        logger.info(f"DAS agent {agent_name} performed {operation}")
    
    def _handle_das_violation_event(self, event: SystemEvent) -> None:
        """Handle DAS permission violation events"""
        agent_name = event.data.get('agent_name')
        scope = event.data.get('scope')
        operation = event.data.get('operation')
        reason = event.data.get('reason', 'Unknown')
        
        logger.warning(f"DAS permission violation: {agent_name} -> {operation} on {scope} - {reason}")
    
    def _handle_das_audit_event(self, event: SystemEvent) -> None:
        """Handle DAS audit log events"""
        agent_name = event.data.get('agent_name')
        scope = event.data.get('scope')
        operation = event.data.get('operation')
        success = event.data.get('success', True)
        
        status = "succeeded" if success else "failed"
        logger.debug(f"DAS audit: {agent_name} {operation} on {scope} {status}")
    
    def _handle_cli_command_event(self, event: SystemEvent) -> None:
        """Handle CLI command execution events"""
        command = event.data.get('command')
        success = event.data.get('success', True)
        
        if success:
            logger.info(f"CLI command executed: {command}")
        else:
            logger.error(f"CLI command failed: {command}")
    
    def _handle_cli_validation_event(self, event: SystemEvent) -> None:
        """Handle CLI project validation events"""
        project_path = event.data.get('project_path')
        errors = event.data.get('errors', 0)
        warnings = event.data.get('warnings', 0)
        
        logger.info(f"Project validation complete: {project_path} - {errors} errors, {warnings} warnings")
    
    def _handle_cli_sync_event(self, event: SystemEvent) -> None:
        """Handle CLI document sync events"""
        synced_files = event.data.get('synced_files', 0)
        errors = event.data.get('errors', 0)
        
        logger.info(f"Document sync complete: {synced_files} files synced, {errors} errors")
    
    def _handle_cli_blueprint_event(self, event: SystemEvent) -> None:
        """Handle CLI blueprint evaluation events"""
        completeness = event.data.get('completeness_score', 0)
        consistency = event.data.get('consistency_score', 0)
        
        logger.info(f"Blueprint evaluation complete: completeness {completeness:.1%}, consistency {consistency:.1%}")
    
    def _handle_task_lifecycle_event(self, event: SystemEvent) -> None:
        """Handle task lifecycle events"""
        task_id = event.data.get('task_id')
        
        if event.event_type == EventType.TASK_STARTED:
            logger.info(f"Task started: {task_id}")
        elif event.event_type == EventType.TASK_COMPLETED:
            result = event.data.get('result', 'success')
            logger.info(f"Task completed: {task_id} - {result}")
        elif event.event_type == EventType.TASK_FAILED:
            error = event.data.get('error', 'Unknown error')
            logger.error(f"Task failed: {task_id} - {error}")
        elif event.event_type == EventType.TASK_UPDATED:
            status = event.data.get('status', 'unknown')
            logger.info(f"Task updated: {task_id} - {status}")
    
    def get_integration_status(self) -> Dict[str, str]:
        """Get status of all component integrations"""
        return self.integration_status.copy()
    
    def get_observer_stats(self) -> Dict[str, Any]:
        """Get statistics from all observers"""
        stats = {}
        for component, observer in self.observers.items():
            if hasattr(observer, 'get_task_stats'):
                stats[f"{component}_task_stats"] = observer.get_task_stats()
            if hasattr(observer, 'get_component_state'):
                stats[f"{component}_states"] = observer.get_all_component_states()
        return stats
    
    async def shutdown(self) -> None:
        """Shutdown all integrations"""
        # Unsubscribe all subscribers
        for component, subscriber in self.subscribers.items():
            self.publisher.unsubscribe(subscriber)
            logger.debug(f"Unsubscribed {component} integration")
        
        # Clear observers
        self.observers.clear()
        self.subscribers.clear()
        
        # Update status
        for component in self.integration_status:
            self.integration_status[component] = 'shutdown'
        
        logger.info("All integrations shutdown")

# ---------------------------------------------------------------------------
# Global Integration Instance
# ---------------------------------------------------------------------------

_global_integration: Optional[EventIntegration] = None

def get_event_integration() -> EventIntegration:
    """Get global event integration instance"""
    global _global_integration
    if _global_integration is None:
        _global_integration = EventIntegration()
        _global_integration.setup_all_integrations()
    return _global_integration

def setup_devhub_events() -> EventIntegration:
    """Setup DevHub event system integration"""
    integration = get_event_integration()
    logger.info("DevHub event system integration setup complete")
    return integration

# ---------------------------------------------------------------------------
# Convenience Functions for Component Integration
# ---------------------------------------------------------------------------

async def emit_task_event(event_type: EventType, task_id: str, 
                         result: str = None, error: str = None,
                         correlation_id: str = None) -> None:
    """Emit task lifecycle event"""
    event = create_task_event(event_type, task_id, result, error, "devagent")
    if correlation_id:
        event.correlation_id = correlation_id
    
    publisher = get_event_publisher()
    await publisher.publish(event)

async def emit_pms_event(event_type: EventType, scope: str, 
                        operation: str = None, success: bool = True,
                        correlation_id: str = None) -> None:
    """Emit PMS system event"""
    event = create_pms_event(event_type, scope, operation, success)
    if correlation_id:
        event.correlation_id = correlation_id
    
    publisher = get_event_publisher()
    await publisher.publish(event)

async def emit_das_event(event_type: EventType, agent_name: str,
                        scope: str = None, operation: str = None,
                        success: bool = True, correlation_id: str = None) -> None:
    """Emit DAS system event"""
    event = create_das_event(event_type, agent_name, scope, operation, success)
    if correlation_id:
        event.correlation_id = correlation_id
    
    publisher = get_event_publisher()
    await publisher.publish(event)