# -*- coding: utf-8 -*-
"""Observer Pattern Implementation - TS-ARCH-001

Classical Observer pattern implementation for DevHub component monitoring.
Provides base classes for implementing component observers and subjects.

This complements the event system by providing direct observer relationships
between specific components that need tight coupling.

Usage:
    from core.observers import Observer, Subject, ComponentObserver
    
    # Create subject (observable component)  
    class TaskManager(Subject):
        def complete_task(self, task_id):
            self.notify_observers('task_completed', {'task_id': task_id})
    
    # Create observer
    class TaskObserver(Observer):
        def update(self, subject, event_type, data):
            if event_type == 'task_completed':
                print(f"Task {data['task_id']} completed!")
    
    # Wire them up
    task_manager = TaskManager()
    task_observer = TaskObserver()
    task_manager.attach_observer(task_observer)
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import weakref
from enum import Enum

logger = logging.getLogger("devhub.observers")

# ---------------------------------------------------------------------------
# Observer Pattern Base Classes
# ---------------------------------------------------------------------------

class Observer(ABC):
    """Abstract base class for observers in the Observer pattern"""
    
    def __init__(self, observer_id: Optional[str] = None):
        self.observer_id = observer_id or f"observer_{id(self)}"
        self.is_active = True
    
    @abstractmethod
    def update(self, subject: 'Subject', event_type: str, data: Dict[str, Any]) -> None:
        """Handle notification from subject
        
        Args:
            subject: The subject that generated the notification
            event_type: Type of event/change that occurred
            data: Event data payload
        """
        pass
    
    def activate(self) -> None:
        """Activate observer to receive notifications"""
        self.is_active = True
        logger.debug(f"Observer {self.observer_id} activated")
    
    def deactivate(self) -> None:
        """Deactivate observer to stop receiving notifications"""
        self.is_active = False
        logger.debug(f"Observer {self.observer_id} deactivated")

class Subject:
    """Subject class for the Observer pattern
    
    Maintains list of observers and notifies them of changes.
    Uses weak references to prevent memory leaks.
    """
    
    def __init__(self, subject_id: Optional[str] = None):
        self.subject_id = subject_id or f"subject_{id(self)}"
        self._observers: Set[Observer] = set()
        self._observer_refs: Set[weakref.ReferenceType] = set()
        self.notification_count = 0
        
        logger.debug(f"Subject {self.subject_id} created")
    
    def attach_observer(self, observer: Observer) -> None:
        """Attach an observer to this subject"""
        self._observers.add(observer)
        
        # Also keep weak reference for cleanup
        weak_ref = weakref.ref(observer, self._cleanup_observer)
        self._observer_refs.add(weak_ref)
        
        logger.debug(f"Observer {observer.observer_id} attached to subject {self.subject_id}")
    
    def detach_observer(self, observer: Observer) -> None:
        """Detach an observer from this subject"""
        self._observers.discard(observer)
        
        # Clean up weak references
        self._observer_refs = {ref for ref in self._observer_refs if ref() is not observer}
        
        logger.debug(f"Observer {observer.observer_id} detached from subject {self.subject_id}")
    
    def _cleanup_observer(self, weak_ref: weakref.ReferenceType) -> None:
        """Clean up dead weak reference"""
        self._observer_refs.discard(weak_ref)
    
    def notify_observers(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """Notify all attached observers of an event
        
        Args:
            event_type: Type of event that occurred
            data: Optional event data payload
        """
        if data is None:
            data = {}
        
        # Clean up any dead observers first
        active_observers = {obs for obs in self._observers if obs is not None}
        self._observers = active_observers
        
        if not active_observers:
            logger.debug(f"Subject {self.subject_id}: No active observers for event {event_type}")
            return
        
        self.notification_count += 1
        
        logger.debug(f"Subject {self.subject_id} notifying {len(active_observers)} "
                    f"observers of event {event_type}")
        
        # Notify all active observers
        for observer in active_observers.copy():  # Copy to avoid modification during iteration
            try:
                if observer.is_active:
                    observer.update(self, event_type, data)
            except Exception as e:
                logger.error(f"Error notifying observer {observer.observer_id}: {e}", 
                           exc_info=True)
                
                # Optionally detach failed observers
                # self.detach_observer(observer)
    
    def get_observer_count(self) -> int:
        """Get number of active observers"""
        return len([obs for obs in self._observers if obs.is_active])
    
    def get_observer_ids(self) -> List[str]:
        """Get list of active observer IDs"""
        return [obs.observer_id for obs in self._observers if obs.is_active]

# ---------------------------------------------------------------------------
# Specialized Component Observers
# ---------------------------------------------------------------------------

class ComponentState(Enum):
    """Component lifecycle states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class ComponentEvent:
    """Component event data"""
    component_id: str
    event_type: str
    old_state: Optional[ComponentState] = None
    new_state: Optional[ComponentState] = None
    timestamp: datetime = None
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.data is None:
            self.data = {}

class ComponentObserver(Observer):
    """Specialized observer for DevHub component lifecycle events"""
    
    def __init__(self, observer_id: Optional[str] = None):
        super().__init__(observer_id)
        self.component_states: Dict[str, ComponentState] = {}
        self.event_history: List[ComponentEvent] = []
        self.max_history = 100
    
    def update(self, subject: Subject, event_type: str, data: Dict[str, Any]) -> None:
        """Handle component lifecycle events"""
        component_id = data.get('component_id', subject.subject_id)
        
        # Create component event
        component_event = ComponentEvent(
            component_id=component_id,
            event_type=event_type,
            old_state=self.component_states.get(component_id),
            new_state=data.get('new_state'),
            data=data
        )
        
        # Update state tracking
        if component_event.new_state:
            self.component_states[component_id] = component_event.new_state
        
        # Add to history
        self.event_history.append(component_event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Handle specific events
        self.handle_component_event(component_event)
        
        logger.info(f"Component {component_id} event: {event_type}")
    
    def handle_component_event(self, event: ComponentEvent) -> None:
        """Override this method to handle specific component events"""
        # Default implementation - log component state changes
        if event.old_state != event.new_state and event.new_state:
            logger.info(f"Component {event.component_id} state: "
                       f"{event.old_state} -> {event.new_state}")
        
        # Handle error states
        if event.new_state == ComponentState.ERROR:
            self.handle_component_error(event)
    
    def handle_component_error(self, event: ComponentEvent) -> None:
        """Handle component error events"""
        logger.error(f"Component {event.component_id} entered error state: "
                    f"{event.data.get('error_message', 'Unknown error')}")
    
    def get_component_state(self, component_id: str) -> Optional[ComponentState]:
        """Get current state of a component"""
        return self.component_states.get(component_id)
    
    def get_component_history(self, component_id: str, limit: int = 10) -> List[ComponentEvent]:
        """Get event history for specific component"""
        component_events = [e for e in self.event_history if e.component_id == component_id]
        return component_events[-limit:] if component_events else []
    
    def get_all_component_states(self) -> Dict[str, ComponentState]:
        """Get current states of all tracked components"""
        return self.component_states.copy()

# ---------------------------------------------------------------------------
# DevHub-Specific Observers
# ---------------------------------------------------------------------------

class TaskObserver(ComponentObserver):
    """Observer specifically for DevHub task lifecycle"""
    
    def __init__(self, observer_id: str = "task_observer"):
        super().__init__(observer_id)
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.active_tasks: Set[str] = set()
    
    def handle_component_event(self, event: ComponentEvent) -> None:
        """Handle task-specific events"""
        super().handle_component_event(event)
        
        task_id = event.data.get('task_id')
        if not task_id:
            return
        
        if event.event_type == 'task_started':
            self.active_tasks.add(task_id)
            logger.info(f"Task started: {task_id}")
            
        elif event.event_type == 'task_completed':
            self.active_tasks.discard(task_id)
            self.completed_tasks.append(task_id)
            logger.info(f"Task completed: {task_id}")
            
        elif event.event_type == 'task_failed':
            self.active_tasks.discard(task_id)
            self.failed_tasks.append(task_id)
            logger.error(f"Task failed: {task_id} - {event.data.get('error', 'Unknown error')}")
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'total_tasks': len(self.completed_tasks) + len(self.failed_tasks),
            'success_rate': (len(self.completed_tasks) / 
                           max(1, len(self.completed_tasks) + len(self.failed_tasks)))
        }

class PMSObserver(ComponentObserver):
    """Observer for PMS (Persistent Memory System) events"""
    
    def __init__(self, observer_id: str = "pms_observer"):
        super().__init__(observer_id)
        self.data_operations: List[Dict[str, Any]] = []
        self.schema_violations: List[Dict[str, Any]] = []
        self.transaction_history: List[Dict[str, Any]] = []
    
    def handle_component_event(self, event: ComponentEvent) -> None:
        """Handle PMS-specific events"""
        super().handle_component_event(event)
        
        if event.event_type in ['data_loaded', 'data_saved']:
            self.data_operations.append({
                'timestamp': event.timestamp,
                'operation': event.event_type,
                'scope': event.data.get('scope'),
                'success': event.data.get('success', True)
            })
            
        elif event.event_type == 'schema_violation':
            self.schema_violations.append({
                'timestamp': event.timestamp,
                'scope': event.data.get('scope'),
                'violation': event.data.get('violation_details')
            })
            
        elif event.event_type.startswith('transaction_'):
            self.transaction_history.append({
                'timestamp': event.timestamp,
                'transaction_type': event.event_type,
                'transaction_id': event.data.get('transaction_id'),
                'scopes': event.data.get('affected_scopes', [])
            })

class DASObserver(ComponentObserver):
    """Observer for DAS (DevAgent System) events"""
    
    def __init__(self, observer_id: str = "das_observer"):
        super().__init__(observer_id)
        self.permission_checks: List[Dict[str, Any]] = []
        self.violations: List[Dict[str, Any]] = []
        self.agent_activities: Dict[str, List[Dict[str, Any]]] = {}
    
    def handle_component_event(self, event: ComponentEvent) -> None:
        """Handle DAS-specific events"""
        super().handle_component_event(event)
        
        if event.event_type == 'permission_checked':
            self.permission_checks.append({
                'timestamp': event.timestamp,
                'agent_name': event.data.get('agent_name'),
                'scope': event.data.get('scope'),
                'operation': event.data.get('operation'),
                'granted': event.data.get('granted', False)
            })
            
        elif event.event_type == 'permission_violation':
            self.violations.append({
                'timestamp': event.timestamp,
                'agent_name': event.data.get('agent_name'),
                'scope': event.data.get('scope'),
                'operation': event.data.get('operation'),
                'violation_reason': event.data.get('reason')
            })
            
        # Track agent activities
        agent_name = event.data.get('agent_name')
        if agent_name:
            if agent_name not in self.agent_activities:
                self.agent_activities[agent_name] = []
            
            self.agent_activities[agent_name].append({
                'timestamp': event.timestamp,
                'event_type': event.event_type,
                'data': event.data
            })

# ---------------------------------------------------------------------------
# Observer Registry and Management
# ---------------------------------------------------------------------------

class ObserverRegistry:
    """Global registry for managing observers and subjects"""
    
    def __init__(self):
        self.observers: Dict[str, Observer] = {}
        self.subjects: Dict[str, Subject] = {}
        self.observer_subjects: Dict[str, List[str]] = {}  # observer_id -> [subject_ids]
    
    def register_observer(self, observer: Observer) -> None:
        """Register an observer in the global registry"""
        self.observers[observer.observer_id] = observer
        self.observer_subjects[observer.observer_id] = []
        logger.debug(f"Observer registered: {observer.observer_id}")
    
    def register_subject(self, subject: Subject) -> None:
        """Register a subject in the global registry"""
        self.subjects[subject.subject_id] = subject
        logger.debug(f"Subject registered: {subject.subject_id}")
    
    def attach_observer_to_subject(self, observer_id: str, subject_id: str) -> bool:
        """Attach observer to subject by ID"""
        if observer_id not in self.observers or subject_id not in self.subjects:
            return False
        
        observer = self.observers[observer_id]
        subject = self.subjects[subject_id]
        
        subject.attach_observer(observer)
        self.observer_subjects[observer_id].append(subject_id)
        
        return True
    
    def detach_observer_from_subject(self, observer_id: str, subject_id: str) -> bool:
        """Detach observer from subject by ID"""
        if observer_id not in self.observers or subject_id not in self.subjects:
            return False
        
        observer = self.observers[observer_id]
        subject = self.subjects[subject_id]
        
        subject.detach_observer(observer)
        if subject_id in self.observer_subjects[observer_id]:
            self.observer_subjects[observer_id].remove(subject_id)
        
        return True
    
    def get_observer_stats(self) -> Dict[str, Any]:
        """Get observer registry statistics"""
        return {
            'total_observers': len(self.observers),
            'total_subjects': len(self.subjects),
            'active_observers': len([obs for obs in self.observers.values() if obs.is_active]),
            'observer_subject_relationships': sum(len(subjects) for subjects in self.observer_subjects.values())
        }

# ---------------------------------------------------------------------------
# Global Registry Instance
# ---------------------------------------------------------------------------

_global_registry: Optional[ObserverRegistry] = None

def get_observer_registry() -> ObserverRegistry:
    """Get global observer registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ObserverRegistry()
    return _global_registry

# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def create_task_observer() -> TaskObserver:
    """Create and register a task observer"""
    observer = TaskObserver()
    registry = get_observer_registry()
    registry.register_observer(observer)
    return observer

def create_pms_observer() -> PMSObserver:
    """Create and register a PMS observer"""
    observer = PMSObserver()
    registry = get_observer_registry()
    registry.register_observer(observer)
    return observer

def create_das_observer() -> DASObserver:
    """Create and register a DAS observer"""
    observer = DASObserver()
    registry = get_observer_registry()
    registry.register_observer(observer)
    return observer