#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DevHub Event System Demo - TS-ARCH-001

Demonstrates the complete event-driven architecture implementation.
Shows integration between EventPublisher, Observers, and DevHub components.

Usage:
    python examples/event_system_demo.py
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.event_system import (
    EventPublisher, SystemEvent, EventType, EventSubscriber,
    get_event_publisher, publish_event, create_task_event
)
from core.observers import TaskObserver, ComponentObserver, get_observer_registry
from core.integration import (
    EventIntegration, event_emitter, task_event_emitter,
    emit_task_event, emit_pms_event, emit_das_event
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("event_demo")

# ---------------------------------------------------------------------------
# Demo Component Classes
# ---------------------------------------------------------------------------

class DevAgentSimulator:
    """Simulates DevAgent with event emission"""
    
    def __init__(self):
        self.current_task_id = None
        self.correlation_id = None
    
    @event_emitter(EventType.TASK_STARTED, source_component='devagent')
    async def start_task(self, task_id: str, correlation_id: str = None) -> dict:
        """Start a task with automatic event emission"""
        self.current_task_id = task_id
        self.correlation_id = correlation_id
        
        logger.info(f"DevAgent starting task: {task_id}")
        
        # Simulate task work
        await asyncio.sleep(0.1)
        
        return {
            'task_id': task_id,
            'status': 'started',
            'correlation_id': correlation_id
        }
    
    @event_emitter(EventType.TASK_COMPLETED, source_component='devagent')
    async def complete_task(self, result: str = 'success') -> dict:
        """Complete current task with automatic event emission"""
        task_id = self.current_task_id
        correlation_id = self.correlation_id
        
        logger.info(f"DevAgent completing task: {task_id} with result: {result}")
        
        # Reset current task
        self.current_task_id = None
        self.correlation_id = None
        
        return {
            'task_id': task_id,
            'result': result,
            'correlation_id': correlation_id
        }
    
    async def simulate_task_workflow(self, task_id: str) -> None:
        """Simulate complete task workflow"""
        correlation_id = f"workflow-{task_id}"
        
        # Start task
        await self.start_task(task_id, correlation_id)
        
        # Emit PMS events during task execution
        await emit_pms_event(
            EventType.PMS_DATA_LOADED,
            scope='backlog_f1',
            operation='load',
            correlation_id=correlation_id
        )
        
        # Emit DAS events
        await emit_das_event(
            EventType.DAS_AGENT_PERMISSION_CHECKED,
            agent_name='DevAgent',
            scope='backlog_f1',
            operation='save',
            correlation_id=correlation_id
        )
        
        # Simulate work
        await asyncio.sleep(0.2)
        
        # Complete task
        await self.complete_task('implementation_complete')

class ProjectMonitor:
    """Monitors project events and maintains statistics"""
    
    def __init__(self):
        self.task_count = 0
        self.completed_tasks = []
        self.pms_operations = []
        self.das_operations = []
        
        # Subscribe to relevant events
        self.subscriber = EventSubscriber("project_monitor")
        publisher = get_event_publisher()
        
        # Subscribe to task events
        publisher.subscribe(EventType.TASK_STARTED, self.on_task_started, self.subscriber)
        publisher.subscribe(EventType.TASK_COMPLETED, self.on_task_completed, self.subscriber)
        
        # Subscribe to system events
        publisher.subscribe(EventType.PMS_DATA_LOADED, self.on_pms_event, self.subscriber)
        publisher.subscribe(EventType.DAS_AGENT_PERMISSION_CHECKED, self.on_das_event, self.subscriber)
        
        logger.info("ProjectMonitor initialized and subscribed to events")
    
    def on_task_started(self, event: SystemEvent) -> None:
        """Handle task started events"""
        task_id = event.data.get('task_id')
        self.task_count += 1
        logger.info(f"📋 Monitor: Task {task_id} started (total: {self.task_count})")
    
    def on_task_completed(self, event: SystemEvent) -> None:
        """Handle task completed events"""
        task_id = event.data.get('task_id')
        result = event.data.get('result', 'unknown')
        self.completed_tasks.append(task_id)
        logger.info(f"✅ Monitor: Task {task_id} completed with {result} (completed: {len(self.completed_tasks)})")
    
    def on_pms_event(self, event: SystemEvent) -> None:
        """Handle PMS events"""
        scope = event.data.get('scope')
        operation = event.data.get('operation')
        self.pms_operations.append(f"{operation}:{scope}")
        logger.info(f"💾 Monitor: PMS {operation} on {scope}")
    
    def on_das_event(self, event: SystemEvent) -> None:
        """Handle DAS events"""
        agent_name = event.data.get('agent_name')
        scope = event.data.get('scope')
        operation = event.data.get('operation')
        self.das_operations.append(f"{agent_name}:{operation}:{scope}")
        logger.info(f"🔐 Monitor: DAS {agent_name} {operation} on {scope}")
    
    def get_stats(self) -> dict:
        """Get monitoring statistics"""
        return {
            'total_tasks_started': self.task_count,
            'total_tasks_completed': len(self.completed_tasks),
            'total_pms_operations': len(self.pms_operations),
            'total_das_operations': len(self.das_operations),
            'completed_tasks': self.completed_tasks,
            'recent_pms_ops': self.pms_operations[-5:],
            'recent_das_ops': self.das_operations[-5:]
        }

# ---------------------------------------------------------------------------
# Demo Functions
# ---------------------------------------------------------------------------

async def demo_basic_events():
    """Demo basic event publishing and subscription"""
    logger.info("\n" + "="*60)
    logger.info("DEMO: Basic Event System")
    logger.info("="*60)
    
    publisher = get_event_publisher()
    received_events = []
    
    def event_handler(event: SystemEvent):
        received_events.append(event)
        logger.info(f"📨 Received: {event.event_type.value} from {event.source_component}")
    
    # Subscribe to events
    subscriber = publisher.subscribe(EventType.COMPONENT_STARTED, event_handler)
    publisher.subscribe(EventType.COMPONENT_STOPPED, event_handler, subscriber)
    
    # Publish events
    await publisher.publish(SystemEvent(
        event_type=EventType.COMPONENT_STARTED,
        source_component='demo',
        data={'component': 'event_system'}
    ))
    
    await publisher.publish(SystemEvent(
        event_type=EventType.COMPONENT_STOPPED,
        source_component='demo',
        data={'component': 'event_system'}
    ))
    
    logger.info(f"✅ Demo complete: {len(received_events)} events received")
    return received_events

async def demo_task_workflow():
    """Demo complete task workflow with events"""
    logger.info("\n" + "="*60)
    logger.info("DEMO: Task Workflow with Events")
    logger.info("="*60)
    
    # Create components
    devagent = DevAgentSimulator()
    monitor = ProjectMonitor()
    
    # Create task observer
    task_observer = TaskObserver("demo_task_observer")
    registry = get_observer_registry()
    registry.register_observer(task_observer)
    
    # Simulate multiple tasks
    tasks = ['TS-ARCH-001', 'TS-CLI-001', 'TS-PMS-001']
    
    for task_id in tasks:
        logger.info(f"\n🚀 Starting workflow for task: {task_id}")
        await devagent.simulate_task_workflow(task_id)
        await asyncio.sleep(0.1)  # Small delay between tasks
    
    # Get statistics
    monitor_stats = monitor.get_stats()
    task_stats = task_observer.get_task_stats()
    
    logger.info(f"\n📊 Monitor Stats: {monitor_stats}")
    logger.info(f"📊 Task Observer Stats: {task_stats}")
    
    return monitor_stats, task_stats

async def demo_event_integration():
    """Demo complete event integration system"""
    logger.info("\n" + "="*60)
    logger.info("DEMO: Event Integration System")
    logger.info("="*60)
    
    # Initialize integration
    integration = EventIntegration()
    integration.setup_all_integrations()
    
    # Get integration status
    status = integration.get_integration_status()
    logger.info(f"🔧 Integration Status: {status}")
    
    # Emit various system events
    await emit_task_event(EventType.TASK_STARTED, 'integration-demo-task', correlation_id='demo-123')
    
    await emit_pms_event(
        EventType.PMS_DATA_SAVED,
        scope='project_status',
        operation='save',
        correlation_id='demo-123'
    )
    
    await emit_das_event(
        EventType.DAS_AGENT_STARTED,
        agent_name='DevAgent',
        correlation_id='demo-123'
    )
    
    await emit_task_event(EventType.TASK_COMPLETED, 'integration-demo-task', 
                         result='success', correlation_id='demo-123')
    
    # Get observer stats
    observer_stats = integration.get_observer_stats()
    logger.info(f"📊 Observer Stats: {observer_stats}")
    
    return status, observer_stats

async def demo_error_handling():
    """Demo error handling in event system"""
    logger.info("\n" + "="*60)
    logger.info("DEMO: Error Handling")
    logger.info("="*60)
    
    publisher = get_event_publisher()
    error_events = []
    
    def error_handler(event: SystemEvent):
        error_events.append(event)
        logger.info(f"🚨 Error Event: {event.data.get('error_type', 'unknown')}")
    
    def failing_handler(event: SystemEvent):
        raise ValueError("Simulated handler error")
    
    def success_handler(event: SystemEvent):
        logger.info("✅ Success handler executed despite failing handler")
    
    # Subscribe handlers
    publisher.subscribe(EventType.SYSTEM_ERROR, error_handler)
    publisher.subscribe(EventType.TASK_FAILED, failing_handler)
    publisher.subscribe(EventType.TASK_FAILED, success_handler)
    
    # Publish event that will trigger error
    await publisher.publish(SystemEvent(
        event_type=EventType.TASK_FAILED,
        data={'task_id': 'failing-task'}
    ))
    
    # Wait a moment for error event to be published
    await asyncio.sleep(0.1)
    
    logger.info(f"📊 Error events captured: {len(error_events)}")
    
    return error_events

async def demo_event_correlation():
    """Demo event correlation tracking"""
    logger.info("\n" + "="*60)
    logger.info("DEMO: Event Correlation")
    logger.info("="*60)
    
    publisher = get_event_publisher()
    correlated_events = []
    
    def correlation_handler(event: SystemEvent):
        if event.correlation_id:
            correlated_events.append(event)
            logger.info(f"🔗 Correlated event: {event.event_type.value} [{event.correlation_id}]")
    
    # Subscribe to all events
    publisher.subscribe_global(correlation_handler)
    
    correlation_id = "demo-correlation-123"
    
    # Publish sequence of correlated events
    events_sequence = [
        (EventType.TASK_STARTED, {'task_id': 'corr-task'}),
        (EventType.PMS_DATA_LOADED, {'scope': 'backlog_f1'}),
        (EventType.DAS_AGENT_PERMISSION_CHECKED, {'agent_name': 'DevAgent', 'scope': 'backlog_f1'}),
        (EventType.PMS_DATA_SAVED, {'scope': 'backlog_f1'}),
        (EventType.TASK_COMPLETED, {'task_id': 'corr-task', 'result': 'success'})
    ]
    
    for event_type, data in events_sequence:
        await publisher.publish(SystemEvent(
            event_type=event_type,
            data=data,
            correlation_id=correlation_id
        ))
        await asyncio.sleep(0.05)
    
    logger.info(f"📊 Correlated events tracked: {len(correlated_events)}")
    
    return correlated_events

async def demo_performance():
    """Demo event system performance"""
    logger.info("\n" + "="*60)
    logger.info("DEMO: Performance Test")
    logger.info("="*60)
    
    publisher = get_event_publisher()
    processed_count = 0
    
    def perf_handler(event: SystemEvent):
        nonlocal processed_count
        processed_count += 1
    
    # Subscribe multiple handlers
    for i in range(10):
        publisher.subscribe(EventType.SYSTEM_HEALTH_CHECK, perf_handler)
    
    # Publish many events
    num_events = 100
    start_time = asyncio.get_event_loop().time()
    
    logger.info(f"🏃 Publishing {num_events} events...")
    
    for i in range(num_events):
        await publisher.publish(SystemEvent(
            event_type=EventType.SYSTEM_HEALTH_CHECK,
            data={'check_id': i}
        ))
    
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    stats = publisher.get_stats()
    
    logger.info(f"⚡ Performance Results:")
    logger.info(f"   Events published: {num_events}")
    logger.info(f"   Events processed: {processed_count}")
    logger.info(f"   Duration: {duration:.3f}s")
    logger.info(f"   Events/second: {num_events/duration:.1f}")
    logger.info(f"   Publisher stats: {stats}")
    
    return {
        'events_published': num_events,
        'events_processed': processed_count,
        'duration': duration,
        'events_per_second': num_events/duration,
        'stats': stats
    }

async def main():
    """Main demo runner"""
    logger.info("🚀 DevHub Event System Demo Starting")
    logger.info("=" * 80)
    
    results = {}
    
    try:
        # Run all demos
        results['basic_events'] = await demo_basic_events()
        results['task_workflow'] = await demo_task_workflow()
        results['integration'] = await demo_event_integration()
        results['error_handling'] = await demo_error_handling()
        results['correlation'] = await demo_event_correlation()
        results['performance'] = await demo_performance()
        
        logger.info("\n" + "="*80)
        logger.info("🎉 ALL DEMOS COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        
        # Summary
        logger.info(f"\n📊 DEMO SUMMARY:")
        logger.info(f"   Basic events: {len(results['basic_events'])} events processed")
        logger.info(f"   Task workflow: {results['task_workflow'][0]['total_tasks_completed']} tasks completed")
        logger.info(f"   Integration: {len(results['integration'][0])} components integrated")
        logger.info(f"   Error handling: {len(results['error_handling'])} error events captured")
        logger.info(f"   Correlation: {len(results['correlation'])} correlated events")
        logger.info(f"   Performance: {results['performance']['events_per_second']:.1f} events/sec")
        
        # Get final publisher stats
        publisher = get_event_publisher()
        final_stats = publisher.get_stats()
        logger.info(f"\n📈 Final Publisher Stats: {final_stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}", exc_info=True)
        return False
    
    finally:
        # Cleanup
        publisher = get_event_publisher()
        await publisher.shutdown()
        logger.info("🛑 Event system shutdown complete")

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)