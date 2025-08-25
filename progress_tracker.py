#!/usr/bin/env python3
"""
Progress tracker and dashboard for SketchAgent operations
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class Task:
    id: str
    type: str  # 'single', 'batch', 'variation'
    concept: str
    palette: str
    style: str
    variations: int
    status: str  # 'queued', 'running', 'completed', 'error'
    progress: int  # 0-100
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    results: Optional[List] = None


class ProgressTracker:
    def __init__(self, data_dir="data/progress"):
        self.data_dir = data_dir
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
        self.ensure_directories()
        self.load_tasks()
    
    def ensure_directories(self):
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_tasks(self):
        """Save tasks to persistent storage"""
        tasks_data = {task_id: asdict(task) for task_id, task in self.tasks.items()}
        with open(f"{self.data_dir}/tasks.json", 'w') as f:
            json.dump(tasks_data, f, indent=2)
    
    def load_tasks(self):
        """Load tasks from persistent storage"""
        tasks_file = f"{self.data_dir}/tasks.json"
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                
                for task_id, task_dict in tasks_data.items():
                    self.tasks[task_id] = Task(**task_dict)
            except Exception as e:
                print(f"Warning: Could not load tasks: {e}")
    
    def create_task(self, task_id: str, task_type: str, concept: str, 
                   palette: str, style: str, variations: int = 1) -> Task:
        """Create a new task"""
        with self.lock:
            task = Task(
                id=task_id,
                type=task_type,
                concept=concept,
                palette=palette,
                style=style,
                variations=variations,
                status='queued',
                progress=0,
                created_at=datetime.now().isoformat()
            )
            self.tasks[task_id] = task
            self.save_tasks()
            return task
    
    def update_task(self, task_id: str, **updates):
        """Update task properties"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # Auto-set timestamps
                if updates.get('status') == 'running' and not task.started_at:
                    task.started_at = datetime.now().isoformat()
                elif updates.get('status') in ['completed', 'error'] and not task.completed_at:
                    task.completed_at = datetime.now().isoformat()
                
                self.save_tasks()
                return task
        return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    def get_recent_tasks(self, hours: int = 24) -> List[Task]:
        """Get tasks from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_tasks = []
        
        for task in self.tasks.values():
            task_time = datetime.fromisoformat(task.created_at.replace('Z', '+00:00').replace('+00:00', ''))
            if task_time >= cutoff:
                recent_tasks.append(task)
        
        return sorted(recent_tasks, key=lambda t: t.created_at, reverse=True)
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks with specific status"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        total = len(self.tasks)
        by_status = {}
        by_type = {}
        
        for task in self.tasks.values():
            by_status[task.status] = by_status.get(task.status, 0) + 1
            by_type[task.type] = by_type.get(task.type, 0) + 1
        
        # Calculate completion times
        completed_tasks = [t for t in self.tasks.values() if t.status == 'completed' and t.started_at and t.completed_at]
        avg_duration = None
        if completed_tasks:
            durations = []
            for task in completed_tasks:
                start = datetime.fromisoformat(task.started_at.replace('Z', '+00:00').replace('+00:00', ''))
                end = datetime.fromisoformat(task.completed_at.replace('Z', '+00:00').replace('+00:00', ''))
                durations.append((end - start).total_seconds())
            avg_duration = sum(durations) / len(durations)
        
        return {
            'total_tasks': total,
            'by_status': by_status,
            'by_type': by_type,
            'avg_completion_time': avg_duration,
            'success_rate': by_status.get('completed', 0) / total * 100 if total > 0 else 0
        }
    
    def cleanup_old_tasks(self, days: int = 30):
        """Remove tasks older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        with self.lock:
            task_ids_to_remove = []
            for task_id, task in self.tasks.items():
                task_time = datetime.fromisoformat(task.created_at.replace('Z', '+00:00').replace('+00:00', ''))
                if task_time < cutoff:
                    task_ids_to_remove.append(task_id)
            
            for task_id in task_ids_to_remove:
                del self.tasks[task_id]
                removed += 1
            
            if removed > 0:
                self.save_tasks()
        
        return removed


class DashboardData:
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        stats = self.tracker.get_statistics()
        recent_tasks = self.tracker.get_recent_tasks(24)
        active_tasks = self.tracker.get_tasks_by_status('running')
        
        # Activity timeline (last 7 days)
        timeline = []
        for i in range(7):
            day = datetime.now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_tasks = []
            for task in self.tracker.tasks.values():
                task_time = datetime.fromisoformat(task.created_at.replace('Z', '+00:00').replace('+00:00', ''))
                if day_start <= task_time < day_end:
                    day_tasks.append(task)
            
            timeline.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'total': len(day_tasks),
                'completed': len([t for t in day_tasks if t.status == 'completed']),
                'failed': len([t for t in day_tasks if t.status == 'error'])
            })
        
        # Popular concepts and styles
        concept_counts = {}
        style_counts = {}
        palette_counts = {}
        
        for task in self.tracker.tasks.values():
            concept_counts[task.concept] = concept_counts.get(task.concept, 0) + 1
            style_counts[task.style] = style_counts.get(task.style, 0) + 1
            palette_counts[task.palette] = palette_counts.get(task.palette, 0) + 1
        
        top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_palettes = sorted(palette_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'statistics': stats,
            'recent_tasks': [asdict(task) for task in recent_tasks[:10]],
            'active_tasks': [asdict(task) for task in active_tasks],
            'activity_timeline': list(reversed(timeline)),
            'popular': {
                'concepts': top_concepts,
                'styles': top_styles,
                'palettes': top_palettes
            }
        }


# Example usage and testing
if __name__ == '__main__':
    # Initialize tracker
    tracker = ProgressTracker()
    
    # Create some sample tasks
    import uuid
    
    sample_tasks = [
        ('single', 'cat', 'vibrant', 'sketch', 1),
        ('batch', 'animals', 'nature', 'watercolor', 5),
        ('variation', 'house', 'sunset', 'cartoon', 3),
    ]
    
    print("🎯 Creating sample tasks...")
    for task_type, concept, palette, style, variations in sample_tasks:
        task_id = str(uuid.uuid4())
        task = tracker.create_task(task_id, task_type, concept, palette, style, variations)
        print(f"  ✅ Created {task_type} task: {concept}")
        
        # Simulate some progress
        tracker.update_task(task_id, status='running', progress=25)
        time.sleep(0.1)
        tracker.update_task(task_id, progress=75)
        time.sleep(0.1)
        tracker.update_task(task_id, status='completed', progress=100)
    
    # Get statistics
    stats = tracker.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  By status: {stats['by_status']}")
    
    # Get dashboard data
    dashboard = DashboardData(tracker)
    data = dashboard.get_dashboard_data()
    
    print(f"\n🎛️ Dashboard data generated:")
    print(f"  Recent tasks: {len(data['recent_tasks'])}")
    print(f"  Active tasks: {len(data['active_tasks'])}")
    print(f"  Timeline entries: {len(data['activity_timeline'])}")
    
    print(f"\n🏆 Popular concepts: {', '.join([f'{c}({n})' for c, n in data['popular']['concepts']])}")
    print(f"🎨 Popular styles: {', '.join([f'{s}({n})' for s, n in data['popular']['styles']])}")
    print(f"🎭 Popular palettes: {', '.join([f'{p}({n})' for p, n in data['popular']['palettes']])}")
    
    print(f"\n💾 Data saved to: {tracker.data_dir}/tasks.json")