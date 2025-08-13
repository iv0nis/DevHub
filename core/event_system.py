# -*- coding: utf-8 -*-
"""DevHub Event System - TS-ARCH-001 Implementation

Event-driven communication system for DevHub components.
Provides publisher-subscriber pattern for loose coupling between
PMS, DAS, CLI, and Web components.

Key features:
- Async event processing 
- Type-safe event definitions
- Component lifecycle events
- Task execution events
- System state change events

Usage:
    from core.event_system import EventPublisher, SystemEvent, EventType
    
    publisher = EventPublisher()
    
    # Subscribe to events
    async def on_task_completed(event):
        print(f"Task {event.task_id} completed!")
    
    publisher.subscribe(EventType.TASK_COMPLETED, on_task_completed)
    
    # Publish events
    await publisher.publish(SystemEvent(
        event_type=EventType.TASK_COMPLETED,
        data={'task_id': 'TS-ARCH-001', 'result': 'success'}
    ))
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Callable, Any, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from pathlib import Path
import weakref

# Configure logging
logger = logging.getLogger("devhub.events")

# ---------------------------------------------------------------------------
# Event Type Definitions - TS-ARCH-001
# ---------------------------------------------------------------------------

class EventType(Enum):
    """System event types for DevHub architecture"""
    
    # Task lifecycle events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed" 
    TASK_FAILED = "task_failed"
    TASK_UPDATED = "task_updated"
    
    # Project lifecycle events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    
    # Component lifecycle events
    COMPONENT_STARTED = "component_started"
    COMPONENT_STOPPED = "component_stopped"
    COMPONENT_ERROR = "component_error"
    
    # PMS events
    PMS_DATA_LOADED = "pms_data_loaded"
    PMS_DATA_SAVED = "pms_data_saved"
    PMS_SCHEMA_VALIDATED = "pms_schema_validated"
    PMS_TRANSACTION_STARTED = "pms_transaction_started"
    PMS_TRANSACTION_COMMITTED = "pms_transaction_committed"
    PMS_TRANSACTION_ROLLED_BACK = "pms_transaction_rolled_back"
    
    # DAS events
    DAS_AGENT_STARTED = "das_agent_started"
    DAS_AGENT_PERMISSION_CHECKED = "das_agent_permission_checked"
    DAS_PERMISSION_VIOLATION = "das_permission_violation"
    DAS_AUDIT_LOG_ENTRY = "das_audit_log_entry"
    
    # CLI events
    CLI_COMMAND_EXECUTED = "cli_command_executed"
    CLI_PROJECT_VALIDATED = "cli_project_validated"
    CLI_DOCUMENTS_SYNCED = "cli_documents_synced"
    CLI_BLUEPRINT_EVALUATED = "cli_blueprint_evaluated"
    
    # Web dashboard events
    WEB_REQUEST_RECEIVED = "web_request_received"
    WEB_DATA_REFRESHED = "web_data_refreshed"
    WEB_USER_ACTION = "web_user_action"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_HEALTH_CHECK = "system_health_check"

@dataclass
class SystemEvent:
    """Base event class for DevHub system events"""
    
    event_type: EventType
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_component: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source_component': self.source_component,
            'data': self.data,
            'metadata': self.metadata,
            'correlation_id': self.correlation_id
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemEvent':
        """Create event from dictionary"""
        return cls(
            event_type=EventType(data['event_type']),
            event_id=data['event_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source_component=data.get('source_component'),
            data=data.get('data', {}),
            metadata=data.get('metadata', {}),
            correlation_id=data.get('correlation_id')
        )

# ---------------------------------------------------------------------------
# Event Subscriber Interface
# ---------------------------------------------------------------------------

EventHandler = Callable[[SystemEvent], Union[None, Any, asyncio.Future]]

class EventSubscriber:
    """Base class for event subscribers with subscription management"""
    
    def __init__(self, subscriber_id: Optional[str] = None):
        self.subscriber_id = subscriber_id or f"subscriber_{uuid.uuid4().hex[:8]}"
        self.subscriptions: Dict[EventType, List[EventHandler]] = {}
        self.is_active = True
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to specific event type"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)
        logger.debug(f"Subscriber {self.subscriber_id} subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler = None) -> None:
        """Unsubscribe from event type"""
        if event_type in self.subscriptions:
            if handler:
                if handler in self.subscriptions[event_type]:
                    self.subscriptions[event_type].remove(handler)
            else:
                # Remove all handlers for this event type
                self.subscriptions[event_type].clear()
        logger.debug(f"Subscriber {self.subscriber_id} unsubscribed from {event_type.value}")
    
    def get_handlers(self, event_type: EventType) -> List[EventHandler]:
        """Get handlers for specific event type"""
        return self.subscriptions.get(event_type, [])
    
    def activate(self):
        """Activate subscriber"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate subscriber"""
        self.is_active = False

# ---------------------------------------------------------------------------
# Event Publisher - Core Component
# ---------------------------------------------------------------------------

class EventPublisher:
    """Central event publisher for DevHub system
    
    Manages event subscriptions, publishing, and async processing.
    Provides thread-safe event handling with proper error isolation.
    """
    
    def __init__(self, max_concurrent_events: int = 100):
        self.subscribers: Dict[EventType, List[EventSubscriber]] = {}
        self.global_subscribers: List[EventSubscriber] = []
        self.event_history: List[SystemEvent] = []
        self.max_history = 1000
        self.max_concurrent_events = max_concurrent_events
        self._semaphore = asyncio.Semaphore(max_concurrent_events)
        self._shutdown = False
        
        # Event statistics
        self.stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'subscribers_count': 0
        }
        
        # Event persistence
        self.persist_events = False
        self.event_log_file: Optional[Path] = None
        
        logger.info(f"EventPublisher initialized with max_concurrent_events={max_concurrent_events}")
    
    def enable_persistence(self, log_file_path: str) -> None:
        """Enable event persistence to file"""
        self.event_log_file = Path(log_file_path)
        self.event_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.persist_events = True
        logger.info(f"Event persistence enabled: {self.event_log_file}")
    
    def subscribe(self, event_type: EventType, handler: EventHandler, 
                 subscriber: Optional[EventSubscriber] = None) -> EventSubscriber:
        """Subscribe to specific event type
        
        Args:
            event_type: Type of event to subscribe to
            handler: Event handler function (sync or async)
            subscriber: Optional subscriber instance (creates new if None)
            
        Returns:
            EventSubscriber instance for subscription management
        """
        if subscriber is None:
            subscriber = EventSubscriber()
        
        subscriber.subscribe(event_type, handler)
        
        # Add to publisher's subscriber registry
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        if subscriber not in self.subscribers[event_type]:
            self.subscribers[event_type].append(subscriber)
            self.stats['subscribers_count'] += 1
        
        logger.debug(f"Handler registered for {event_type.value} (subscriber: {subscriber.subscriber_id})")
        return subscriber
    
    def subscribe_global(self, handler: EventHandler,
                        subscriber: Optional[EventSubscriber] = None) -> EventSubscriber:
        """Subscribe to all events (global subscriber)
        
        Args:
            handler: Event handler function
            subscriber: Optional subscriber instance
            
        Returns:
            EventSubscriber instance
        """
        if subscriber is None:
            subscriber = EventSubscriber()
        
        # Add handler for all event types
        for event_type in EventType:
            subscriber.subscribe(event_type, handler)
        
        if subscriber not in self.global_subscribers:
            self.global_subscribers.append(subscriber)
            self.stats['subscribers_count'] += 1
        
        logger.debug(f"Global subscriber registered: {subscriber.subscriber_id}")
        return subscriber
    
    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        """Unsubscribe subscriber from all events"""
        # Remove from specific event subscriptions
        for event_type, subscribers_list in self.subscribers.items():
            if subscriber in subscribers_list:
                subscribers_list.remove(subscriber)
        
        # Remove from global subscribers
        if subscriber in self.global_subscribers:
            self.global_subscribers.remove(subscriber)
        
        self.stats['subscribers_count'] = max(0, self.stats['subscribers_count'] - 1)
        logger.debug(f"Subscriber unsubscribed: {subscriber.subscriber_id}")
    
    async def publish(self, event: SystemEvent) -> None:
        """Publish event to all subscribers
        
        Args:
            event: SystemEvent to publish
        """
        if self._shutdown:
            logger.warning("EventPublisher is shut down, ignoring event publication")
            return
        
        self.stats['events_published'] += 1
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Persist event if enabled
        if self.persist_events and self.event_log_file:
            await self._persist_event(event)
        
        # Get all relevant subscribers
        relevant_subscribers = []
        
        # Event-specific subscribers
        if event.event_type in self.subscribers:
            relevant_subscribers.extend(self.subscribers[event.event_type])
        
        # Global subscribers
        relevant_subscribers.extend(self.global_subscribers)
        
        if not relevant_subscribers:
            logger.debug(f"No subscribers for event {event.event_type.value}")
            return
        
        # Process event with concurrency control
        async with self._semaphore:
            await self._process_event(event, relevant_subscribers)
        
        logger.debug(f"Event {event.event_type.value} published to {len(relevant_subscribers)} subscribers")
    
    async def _process_event(self, event: SystemEvent, subscribers: List[EventSubscriber]) -> None:
        """Process event for all subscribers with error isolation"""
        tasks = []
        
        for subscriber in subscribers:
            if not subscriber.is_active:
                continue
            
            handlers = subscriber.get_handlers(event.event_type)
            for handler in handlers:
                task = asyncio.create_task(self._handle_event_safely(event, handler, subscriber))
                tasks.append(task)
        
        if tasks:
            # Wait for all handlers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            for result in results:
                if isinstance(result, Exception):
                    self.stats['events_failed'] += 1
                else:
                    self.stats['events_processed'] += 1
    
    async def _handle_event_safely(self, event: SystemEvent, handler: EventHandler, 
                                  subscriber: EventSubscriber) -> None:
        """Handle individual event with error isolation"""
        try:
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handler in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, event)
                
        except Exception as e:
            logger.error(f"Error in event handler {handler.__name__} from subscriber "
                        f"{subscriber.subscriber_id}: {e}", exc_info=True)
            
            # Publish error event
            error_event = SystemEvent(
                event_type=EventType.SYSTEM_ERROR,
                source_component="event_publisher",
                data={
                    'error_type': 'handler_error',
                    'original_event_id': event.event_id,
                    'original_event_type': event.event_type.value,
                    'subscriber_id': subscriber.subscriber_id,
                    'handler_name': handler.__name__,
                    'error_message': str(e)
                }
            )
            
            # Avoid infinite recursion by not publishing error events for error handlers
            if event.event_type != EventType.SYSTEM_ERROR:
                await self.publish(error_event)
    
    async def _persist_event(self, event: SystemEvent) -> None:
        """Persist event to log file"""
        try:
            with open(self.event_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{event.to_json()}\n")
        except Exception as e:
            logger.error(f"Failed to persist event: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event publisher statistics"""
        return {
            **self.stats,
            'event_history_size': len(self.event_history),
            'active_subscribers': sum(
                len(subscribers) for subscribers in self.subscribers.values()
            ) + len(self.global_subscribers),
            'event_types_with_subscribers': len(self.subscribers.keys())
        }
    
    def get_recent_events(self, limit: int = 10, 
                         event_type: Optional[EventType] = None) -> List[SystemEvent]:
        """Get recent events from history
        
        Args:
            limit: Maximum number of events to return
            event_type: Optional filter by event type
            
        Returns:
            List of recent SystemEvent instances
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:] if events else []
    
    async def shutdown(self) -> None:
        """Gracefully shutdown event publisher"""
        self._shutdown = True
        
        # Wait for ongoing events to complete
        await asyncio.sleep(0.1)  # Small delay to allow current events to finish
        
        # Clear all subscriptions
        self.subscribers.clear()
        self.global_subscribers.clear()
        self.stats['subscribers_count'] = 0
        
        logger.info("EventPublisher shut down")

# ---------------------------------------------------------------------------
# Global Event Publisher Instance
# ---------------------------------------------------------------------------

# Global instance for convenience
_global_publisher: Optional[EventPublisher] = None

def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _global_publisher
    if _global_publisher is None:
        _global_publisher = EventPublisher()
    return _global_publisher

def set_event_publisher(publisher: EventPublisher) -> None:
    """Set global event publisher instance"""
    global _global_publisher
    _global_publisher = publisher

# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

async def publish_event(event_type: EventType, data: Dict[str, Any] = None,
                       source_component: str = None, correlation_id: str = None) -> None:
    """Convenience function to publish event"""
    event = SystemEvent(
        event_type=event_type,
        data=data or {},
        source_component=source_component,
        correlation_id=correlation_id
    )
    publisher = get_event_publisher()
    await publisher.publish(event)

def subscribe_to_event(event_type: EventType, handler: EventHandler) -> EventSubscriber:
    """Convenience function to subscribe to event"""
    publisher = get_event_publisher()
    return publisher.subscribe(event_type, handler)

# ---------------------------------------------------------------------------
# Event Factory Functions
# ---------------------------------------------------------------------------

def create_task_event(event_type: EventType, task_id: str, 
                     result: str = None, error: str = None,
                     source_component: str = "devhub") -> SystemEvent:
    """Create task lifecycle event"""
    data = {'task_id': task_id}
    if result:
        data['result'] = result
    if error:
        data['error'] = error
        
    return SystemEvent(
        event_type=event_type,
        source_component=source_component,
        data=data
    )

def create_pms_event(event_type: EventType, scope: str, 
                    operation: str = None, success: bool = True,
                    source_component: str = "pms") -> SystemEvent:
    """Create PMS system event"""
    return SystemEvent(
        event_type=event_type,
        source_component=source_component,
        data={
            'scope': scope,
            'operation': operation,
            'success': success
        }
    )

def create_das_event(event_type: EventType, agent_name: str,
                    scope: str = None, operation: str = None,
                    success: bool = True, source_component: str = "das") -> SystemEvent:
    """Create DAS system event"""
    data = {'agent_name': agent_name, 'success': success}
    if scope:
        data['scope'] = scope
    if operation:
        data['operation'] = operation
        
    return SystemEvent(
        event_type=event_type,
        source_component=source_component,
        data=data
    )