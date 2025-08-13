# -*- coding: utf-8 -*-
"""Tests for DevHub Event System - TS-ARCH-001

Comprehensive tests for event-driven communication system.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from core.event_system import (
    EventPublisher, SystemEvent, EventSubscriber, EventType,
    get_event_publisher, publish_event, subscribe_to_event,
    create_task_event, create_pms_event, create_das_event
)

# ---------------------------------------------------------------------------
# Event System Tests
# ---------------------------------------------------------------------------

class TestSystemEvent:
    """Test SystemEvent class"""
    
    def test_event_creation(self):
        """Test basic event creation"""
        event = SystemEvent(
            event_type=EventType.TASK_COMPLETED,
            source_component="test",
            data={'task_id': 'test-123'}
        )
        
        assert event.event_type == EventType.TASK_COMPLETED
        assert event.source_component == "test"
        assert event.data['task_id'] == 'test-123'
        assert event.event_id is not None
        assert isinstance(event.timestamp, datetime)
    
    def test_event_serialization(self):
        """Test event to_dict and to_json"""
        event = SystemEvent(
            event_type=EventType.TASK_STARTED,
            data={'task_id': 'test-456'}
        )
        
        event_dict = event.to_dict()
        assert event_dict['event_type'] == EventType.TASK_STARTED.value
        assert event_dict['data']['task_id'] == 'test-456'
        
        event_json = event.to_json()
        assert isinstance(event_json, str)
        assert '"task_id": "test-456"' in event_json
    
    def test_event_from_dict(self):
        """Test creating event from dictionary"""
        event_data = {
            'event_type': EventType.PMS_DATA_LOADED.value,
            'event_id': 'test-event-123',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_component': 'pms',
            'data': {'scope': 'project_status'},
            'metadata': {'version': '1.0'},
            'correlation_id': 'corr-123'
        }
        
        event = SystemEvent.from_dict(event_data)
        assert event.event_type == EventType.PMS_DATA_LOADED
        assert event.event_id == 'test-event-123'
        assert event.source_component == 'pms'
        assert event.data['scope'] == 'project_status'

class TestEventSubscriber:
    """Test EventSubscriber class"""
    
    def test_subscriber_creation(self):
        """Test subscriber creation and subscription"""
        subscriber = EventSubscriber("test-sub")
        assert subscriber.subscriber_id == "test-sub"
        assert subscriber.is_active is True
        
        handler = Mock()
        subscriber.subscribe(EventType.TASK_COMPLETED, handler)
        
        handlers = subscriber.get_handlers(EventType.TASK_COMPLETED)
        assert handler in handlers
    
    def test_subscriber_unsubscribe(self):
        """Test unsubscribing from events"""
        subscriber = EventSubscriber()
        handler = Mock()
        
        subscriber.subscribe(EventType.TASK_FAILED, handler)
        assert handler in subscriber.get_handlers(EventType.TASK_FAILED)
        
        subscriber.unsubscribe(EventType.TASK_FAILED, handler)
        assert handler not in subscriber.get_handlers(EventType.TASK_FAILED)
    
    def test_subscriber_activation(self):
        """Test subscriber activation/deactivation"""
        subscriber = EventSubscriber()
        assert subscriber.is_active is True
        
        subscriber.deactivate()
        assert subscriber.is_active is False
        
        subscriber.activate()
        assert subscriber.is_active is True

class TestEventPublisher:
    """Test EventPublisher class"""
    
    @pytest.fixture
    def publisher(self):
        """Create fresh event publisher for each test"""
        return EventPublisher(max_concurrent_events=10)
    
    def test_publisher_creation(self, publisher):
        """Test publisher creation and initialization"""
        assert publisher.max_concurrent_events == 10
        assert publisher.stats['events_published'] == 0
        assert publisher.stats['subscribers_count'] == 0
    
    def test_subscribe_to_event(self, publisher):
        """Test subscribing to specific event type"""
        handler = Mock()
        subscriber = publisher.subscribe(EventType.TASK_COMPLETED, handler)
        
        assert subscriber.subscriber_id is not None
        assert EventType.TASK_COMPLETED in publisher.subscribers
        assert subscriber in publisher.subscribers[EventType.TASK_COMPLETED]
        assert publisher.stats['subscribers_count'] == 1
    
    def test_global_subscription(self, publisher):
        """Test global event subscription"""
        handler = Mock()
        subscriber = publisher.subscribe_global(handler)
        
        assert subscriber in publisher.global_subscribers
        # Should have handler for all event types
        assert len(subscriber.subscriptions) == len(EventType)
    
    @pytest.mark.asyncio
    async def test_publish_event(self, publisher):
        """Test publishing event to subscribers"""
        handler_calls = []
        
        def handler(event):
            handler_calls.append(event)
        
        publisher.subscribe(EventType.TASK_COMPLETED, handler)
        
        event = SystemEvent(
            event_type=EventType.TASK_COMPLETED,
            data={'task_id': 'test-task'}
        )
        
        await publisher.publish(event)
        
        assert len(handler_calls) == 1
        assert handler_calls[0].event_type == EventType.TASK_COMPLETED
        assert handler_calls[0].data['task_id'] == 'test-task'
        assert publisher.stats['events_published'] == 1
        assert publisher.stats['events_processed'] == 1
    
    @pytest.mark.asyncio
    async def test_async_handler(self, publisher):
        """Test async event handler"""
        handler_calls = []
        
        async def async_handler(event):
            handler_calls.append(event)
        
        publisher.subscribe(EventType.PMS_DATA_SAVED, async_handler)
        
        event = SystemEvent(
            event_type=EventType.PMS_DATA_SAVED,
            data={'scope': 'blueprint'}
        )
        
        await publisher.publish(event)
        
        assert len(handler_calls) == 1
        assert handler_calls[0].data['scope'] == 'blueprint'
    
    @pytest.mark.asyncio
    async def test_error_handling(self, publisher):
        """Test error handling in event handlers"""
        def failing_handler(event):
            raise ValueError("Test error")
        
        def success_handler(event):
            success_handler.called = True
        success_handler.called = False
        
        publisher.subscribe(EventType.SYSTEM_ERROR, failing_handler)
        publisher.subscribe(EventType.SYSTEM_ERROR, success_handler)
        
        event = SystemEvent(event_type=EventType.SYSTEM_ERROR)
        await publisher.publish(event)
        
        # Success handler should still be called despite failing handler
        assert success_handler.called is True
        assert publisher.stats['events_failed'] >= 1
    
    @pytest.mark.asyncio
    async def test_event_history(self, publisher):
        """Test event history tracking"""
        event1 = SystemEvent(event_type=EventType.TASK_STARTED)
        event2 = SystemEvent(event_type=EventType.TASK_COMPLETED)
        
        await publisher.publish(event1)
        await publisher.publish(event2)
        
        recent_events = publisher.get_recent_events(limit=2)
        assert len(recent_events) == 2
        assert recent_events[0].event_type == EventType.TASK_STARTED
        assert recent_events[1].event_type == EventType.TASK_COMPLETED
    
    @pytest.mark.asyncio
    async def test_filtered_event_history(self, publisher):
        """Test filtered event history"""
        await publisher.publish(SystemEvent(event_type=EventType.TASK_STARTED))
        await publisher.publish(SystemEvent(event_type=EventType.TASK_COMPLETED))
        await publisher.publish(SystemEvent(event_type=EventType.TASK_FAILED))
        
        completed_events = publisher.get_recent_events(
            event_type=EventType.TASK_COMPLETED
        )
        assert len(completed_events) == 1
        assert completed_events[0].event_type == EventType.TASK_COMPLETED
    
    def test_publisher_stats(self, publisher):
        """Test publisher statistics"""
        handler = Mock()
        publisher.subscribe(EventType.TASK_COMPLETED, handler)
        publisher.subscribe(EventType.TASK_FAILED, handler)
        
        stats = publisher.get_stats()
        assert stats['subscribers_count'] == 1  # Same subscriber for both events
        assert stats['event_types_with_subscribers'] == 2
        assert stats['active_subscribers'] == 2  # 2 event type subscriptions
    
    @pytest.mark.asyncio
    async def test_publisher_shutdown(self, publisher):
        """Test graceful publisher shutdown"""
        handler = Mock()
        subscriber = publisher.subscribe(EventType.TASK_COMPLETED, handler)
        
        await publisher.shutdown()
        
        assert publisher._shutdown is True
        assert len(publisher.subscribers) == 0
        assert len(publisher.global_subscribers) == 0
        assert publisher.stats['subscribers_count'] == 0

# ---------------------------------------------------------------------------
# Convenience Function Tests
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_publish_event_convenience(self):
        """Test convenience publish_event function"""
        handler_calls = []
        
        def handler(event):
            handler_calls.append(event)
        
        # Use global publisher
        publisher = get_event_publisher()
        publisher.subscribe(EventType.COMPONENT_STARTED, handler)
        
        await publish_event(
            EventType.COMPONENT_STARTED,
            data={'component': 'test'},
            source_component='test_suite'
        )
        
        assert len(handler_calls) == 1
        assert handler_calls[0].data['component'] == 'test'
        assert handler_calls[0].source_component == 'test_suite'
    
    def test_subscribe_convenience(self):
        """Test convenience subscribe_to_event function"""
        handler = Mock()
        subscriber = subscribe_to_event(EventType.TASK_UPDATED, handler)
        
        assert subscriber is not None
        assert handler in subscriber.get_handlers(EventType.TASK_UPDATED)

# ---------------------------------------------------------------------------
# Event Factory Tests
# ---------------------------------------------------------------------------

class TestEventFactories:
    """Test event factory functions"""
    
    def test_create_task_event(self):
        """Test task event creation"""
        event = create_task_event(
            EventType.TASK_COMPLETED,
            task_id='TS-TEST-001',
            result='success'
        )
        
        assert event.event_type == EventType.TASK_COMPLETED
        assert event.data['task_id'] == 'TS-TEST-001'
        assert event.data['result'] == 'success'
        assert event.source_component == 'devhub'
    
    def test_create_pms_event(self):
        """Test PMS event creation"""
        event = create_pms_event(
            EventType.PMS_DATA_LOADED,
            scope='project_status',
            operation='load'
        )
        
        assert event.event_type == EventType.PMS_DATA_LOADED
        assert event.data['scope'] == 'project_status'
        assert event.data['operation'] == 'load'
        assert event.data['success'] is True
        assert event.source_component == 'pms'
    
    def test_create_das_event(self):
        """Test DAS event creation"""
        event = create_das_event(
            EventType.DAS_AGENT_STARTED,
            agent_name='DevAgent',
            scope='backlog_f1',
            operation='save'
        )
        
        assert event.event_type == EventType.DAS_AGENT_STARTED
        assert event.data['agent_name'] == 'DevAgent'
        assert event.data['scope'] == 'backlog_f1'
        assert event.data['operation'] == 'save'
        assert event.source_component == 'das'

# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

class TestEventSystemIntegration:
    """Integration tests for complete event system"""
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self):
        """Test multiple subscribers receiving same event"""
        publisher = EventPublisher()
        handler_calls = []
        
        def handler1(event):
            handler_calls.append(('handler1', event))
        
        def handler2(event):
            handler_calls.append(('handler2', event))
        
        publisher.subscribe(EventType.PROJECT_UPDATED, handler1)
        publisher.subscribe(EventType.PROJECT_UPDATED, handler2)
        
        event = SystemEvent(
            event_type=EventType.PROJECT_UPDATED,
            data={'project_id': 'test-project'}
        )
        
        await publisher.publish(event)
        
        assert len(handler_calls) == 2
        assert ('handler1', event) in handler_calls
        assert ('handler2', event) in handler_calls
    
    @pytest.mark.asyncio
    async def test_global_and_specific_subscribers(self):
        """Test global and event-specific subscribers"""
        publisher = EventPublisher()
        calls = {'global': 0, 'specific': 0}
        
        def global_handler(event):
            calls['global'] += 1
        
        def specific_handler(event):
            calls['specific'] += 1
        
        publisher.subscribe_global(global_handler)
        publisher.subscribe(EventType.TASK_STARTED, specific_handler)
        
        # Publish event that specific handler subscribes to
        await publisher.publish(SystemEvent(event_type=EventType.TASK_STARTED))
        
        # Both handlers should be called
        assert calls['global'] == 1
        assert calls['specific'] == 1
        
        # Publish event that only global handler subscribes to
        await publisher.publish(SystemEvent(event_type=EventType.WEB_REQUEST_RECEIVED))
        
        # Only global handler should be called
        assert calls['global'] == 2
        assert calls['specific'] == 1
    
    @pytest.mark.asyncio
    async def test_event_correlation(self):
        """Test event correlation tracking"""
        publisher = EventPublisher()
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        publisher.subscribe_global(handler)
        
        correlation_id = 'task-workflow-123'
        
        # Publish related events with same correlation ID
        await publisher.publish(SystemEvent(
            event_type=EventType.TASK_STARTED,
            correlation_id=correlation_id,
            data={'task_id': 'TS-001'}
        ))
        
        await publisher.publish(SystemEvent(
            event_type=EventType.PMS_DATA_LOADED,
            correlation_id=correlation_id,
            data={'scope': 'backlog_f1'}
        ))
        
        await publisher.publish(SystemEvent(
            event_type=EventType.TASK_COMPLETED,
            correlation_id=correlation_id,
            data={'task_id': 'TS-001'}
        ))
        
        # All events should have same correlation ID
        assert len(received_events) == 3
        for event in received_events:
            assert event.correlation_id == correlation_id

if __name__ == '__main__':
    # Run basic smoke test
    async def smoke_test():
        publisher = EventPublisher()
        
        def handler(event):
            print(f"Received event: {event.event_type.value}")
        
        publisher.subscribe(EventType.TASK_COMPLETED, handler)
        
        event = SystemEvent(
            event_type=EventType.TASK_COMPLETED,
            data={'task_id': 'smoke-test'}
        )
        
        await publisher.publish(event)
        print("✅ Event system smoke test passed!")
    
    asyncio.run(smoke_test())