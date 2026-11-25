"""Run larger search comparisons without blocking the Pygame event loop."""

import queue
import threading
from typing import Any, Callable, Optional, Tuple


class ComparisonWorker:
    """Own one background comparison and deliver its result to the UI thread."""

    def __init__(self) -> None:
        self._results = queue.Queue()
        self._generation = 0
        self.pending = False
        self.mode: Optional[str] = None

    def start(self, mode: str, work: Callable[[], Any]) -> None:
        self._generation += 1
        generation = self._generation
        self.mode = mode
        self.pending = True

        def run() -> None:
            try:
                result = work()
                error = None
            except Exception as exc:
                result = None
                error = f"{type(exc).__name__}: {exc}"
            self._results.put((generation, mode, result, error))

        thread = threading.Thread(target=run, name="maze-ai-comparison", daemon=True)
        try:
            thread.start()
        except Exception as exc:
            self._results.put((generation, mode, None, f"{type(exc).__name__}: {exc}"))

    def poll(self) -> Optional[Tuple[str, Any, Optional[str]]]:
        if not self.pending:
            return None

        while True:
            try:
                generation, mode, result, error = self._results.get_nowait()
            except queue.Empty:
                return None
            if generation != self._generation:
                continue

            self.pending = False
            self.mode = None
            return mode, result, error

    def cancel(self) -> None:
        """Invalidate any running comparison so a late result cannot affect new state."""
        self._generation += 1
        self.pending = False
        self.mode = None
