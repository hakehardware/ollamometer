"""
In-memory progress tracker for model pulling and benchmarking
"""

import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProgressState:
    """State of an ongoing operation"""
    operation: str  # 'pull' or 'benchmark'
    status: str  # 'running', 'complete', 'error', 'cancelled'
    current_item: str  # Current model or test being processed
    message: str = ""
    progress: float = 0.0  # 0.0 to 1.0
    completed: int = 0  # Bytes downloaded or tests completed
    total: int = 0  # Total bytes or total tests
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ProgressTracker:
    """Thread-safe in-memory progress tracker"""

    def __init__(self):
        self._lock = threading.Lock()
        self._state: Optional[ProgressState] = None
        self._cancelled = False

    def start(self, operation: str, current_item: str, total: int = 0) -> None:
        """Start tracking a new operation"""
        with self._lock:
            self._cancelled = False  # Reset cancellation flag
            self._state = ProgressState(
                operation=operation,
                status='running',
                current_item=current_item,
                message=f"Starting {operation}...",
                total=total
            )

    def update(
        self,
        message: str,
        completed: Optional[int] = None,
        total: Optional[int] = None,
        current_item: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update progress state"""
        with self._lock:
            if self._state is None:
                return

            self._state.message = message

            if completed is not None:
                self._state.completed = completed
            if total is not None:
                self._state.total = total
            if current_item is not None:
                self._state.current_item = current_item
            if metadata is not None:
                self._state.metadata.update(metadata)

            # Calculate progress percentage
            if self._state.total > 0:
                self._state.progress = self._state.completed / self._state.total

    def complete(self, message: str = "Complete") -> None:
        """Mark operation as complete"""
        with self._lock:
            if self._state is None:
                return

            self._state.status = 'complete'
            self._state.message = message
            self._state.progress = 1.0
            self._state.completed_at = datetime.now()

    def error(self, error_message: str) -> None:
        """Mark operation as failed"""
        with self._lock:
            if self._state is None:
                return

            self._state.status = 'error'
            self._state.error = error_message
            self._state.message = f"Error: {error_message}"
            self._state.completed_at = datetime.now()

    def cancel(self) -> None:
        """Cancel the current operation"""
        with self._lock:
            if self._state is None:
                return

            self._cancelled = True
            self._state.status = 'cancelled'
            self._state.message = "Benchmark cancelled by user"
            self._state.completed_at = datetime.now()

    def is_cancelled(self) -> bool:
        """Check if the current operation has been cancelled"""
        with self._lock:
            return self._cancelled

    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current state as dictionary"""
        with self._lock:
            if self._state is None:
                return None

            return {
                'operation': self._state.operation,
                'status': self._state.status,
                'current_item': self._state.current_item,
                'message': self._state.message,
                'progress': self._state.progress,
                'completed': self._state.completed,
                'total': self._state.total,
                'error': self._state.error,
                'metadata': self._state.metadata,
                'started_at': self._state.started_at.isoformat() if self._state.started_at else None,
                'completed_at': self._state.completed_at.isoformat() if self._state.completed_at else None
            }

    def clear(self) -> None:
        """Clear current state"""
        with self._lock:
            self._state = None

    def is_running(self) -> bool:
        """Check if an operation is currently running"""
        with self._lock:
            return self._state is not None and self._state.status == 'running'


# Global progress tracker instance
progress_tracker = ProgressTracker()
