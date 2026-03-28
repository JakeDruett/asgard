"""Progress Reporting Infrastructure -- spinners, progress bars, and status updates."""

import sys
import time
from threading import Event, Thread
from typing import Iterator, List, Optional, TypeVar

from Asgard.common._progress_types import ProgressConfig, ProgressStyle

T = TypeVar('T')


class ProgressReporter:
    """Progress reporter for long-running operations.
    Supports context manager, iterator, and manual control patterns."""

    SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]
    DOTS_FRAMES = [".", "..", "...", ""]

    def __init__(
        self, message: str = "Processing", total: Optional[int] = None,
        config: Optional[ProgressConfig] = None,
    ):
        self.message = message
        self.total = total
        self.config = config or ProgressConfig()
        self._current = 0
        self._status = ""
        self._start_time: Optional[float] = None
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._frame = 0

    def __enter__(self) -> "ProgressReporter":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.finish(success=exc_type is None)

    @classmethod
    def iterate(
        cls, items: List[T], message: str = "Processing",
        config: Optional[ProgressConfig] = None,
    ) -> Iterator[T]:
        """Iterate over items with progress reporting."""
        with cls(message, total=len(items), config=config) as progress:
            for item in items:
                yield item
                progress.advance()

    def start(self) -> None:
        """Start the progress indicator."""
        if not self.config.enabled or self.config.style == ProgressStyle.NONE:
            return
        self._start_time = time.time()
        self._stop_event.clear()
        if self.config.style in (ProgressStyle.SPINNER, ProgressStyle.DOTS):
            self._thread = Thread(target=self._animate, daemon=True)
            self._thread.start()
        else:
            self._render()

    def stop(self) -> None:
        """Stop the progress indicator."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def finish(self, success: bool = True) -> None:
        """Finish progress reporting with final status."""
        self.stop()
        if not self.config.enabled or self.config.style == ProgressStyle.NONE:
            return
        self._clear_line()
        elapsed = self._elapsed_str()
        icon = "\u2713" if success else "\u2717"
        if self.total:
            print(f"{icon} {self.message}: {self._current}/{self.total} ({elapsed})")
        else:
            print(f"{icon} {self.message} ({elapsed})")

    def update(self, current: int, status: str = "") -> None:
        """Update progress to a specific count."""
        self._current = current
        self._status = status
        if self.config.style == ProgressStyle.BAR:
            self._render()

    def advance(self, count: int = 1, status: str = "") -> None:
        """Advance progress by count."""
        self.update(self._current + count, status)

    def set_status(self, status: str) -> None:
        """Set the current status message."""
        self._status = status

    def _animate(self) -> None:
        while not self._stop_event.is_set():
            self._render()
            time.sleep(self.config.refresh_rate)
            self._frame = (self._frame + 1) % len(self._get_frames())

    def _get_frames(self) -> List[str]:
        if self.config.style == ProgressStyle.DOTS:
            return self.DOTS_FRAMES
        return self.SPINNER_FRAMES

    def _render(self) -> None:
        if not self.config.enabled:
            return
        self._clear_line()
        if self.config.style == ProgressStyle.BAR:
            line = self._render_bar()
        elif self.config.style == ProgressStyle.SPINNER:
            line = self._render_spinner()
        elif self.config.style == ProgressStyle.DOTS:
            line = self._render_dots()
        else:
            line = self.message
        sys.stdout.write(line)
        sys.stdout.flush()

    def _render_spinner(self) -> str:
        frame = self.SPINNER_FRAMES[self._frame % len(self.SPINNER_FRAMES)]
        parts = [f"\r{frame} {self.message}"]
        if self.config.show_count and self.total:
            parts.append(f" [{self._current}/{self.total}]")
        elif self.config.show_count and self._current > 0:
            parts.append(f" [{self._current}]")
        if self.config.show_percentage and self.total and self.total > 0:
            pct = (self._current / self.total) * 100
            parts.append(f" {pct:.0f}%")
        if self.config.show_elapsed:
            parts.append(f" ({self._elapsed_str()})")
        if self._status:
            parts.append(f" - {self._status}")
        return "".join(parts)

    def _render_bar(self) -> str:
        parts = [f"\r{self.message}: "]
        if self.total and self.total > 0:
            pct = self._current / self.total
            filled = int(self.config.bar_width * pct)
            empty = self.config.bar_width - filled
            bar = "\u2588" * filled + "\u2591" * empty
            parts.append(f"[{bar}]")
            if self.config.show_percentage:
                parts.append(f" {pct * 100:.0f}%")
            if self.config.show_count:
                parts.append(f" ({self._current}/{self.total})")
        else:
            parts.append(f"[{chr(0x2591) * self.config.bar_width}]")
            if self.config.show_count:
                parts.append(f" ({self._current})")
        if self.config.show_elapsed:
            parts.append(f" {self._elapsed_str()}")
        if self._status:
            parts.append(f" - {self._status}")
        return "".join(parts)

    def _render_dots(self) -> str:
        dots = self.DOTS_FRAMES[self._frame % len(self.DOTS_FRAMES)]
        parts = [f"\r{self.message}{dots}"]
        if self.config.show_count and self._current > 0:
            parts.append(f" ({self._current})")
        return "".join(parts)

    def _elapsed_str(self) -> str:
        if not self._start_time:
            return "0s"
        elapsed = time.time() - self._start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        elif elapsed < 3600:
            return f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        else:
            return f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m"

    def _clear_line(self) -> None:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()


def with_progress(
    items: List[T], message: str = "Processing",
    style: ProgressStyle = ProgressStyle.SPINNER,
) -> Iterator[T]:
    """Iterate with progress reporting."""
    config = ProgressConfig(style=style)
    yield from ProgressReporter.iterate(items, message, config)


def spinner(message: str = "Loading") -> ProgressReporter:
    """Create a simple spinner."""
    return ProgressReporter(message, config=ProgressConfig(style=ProgressStyle.SPINNER))


def progress_bar(message: str = "Processing", total: int = 100) -> ProgressReporter:
    """Create a progress bar."""
    return ProgressReporter(
        message, total=total,
        config=ProgressConfig(style=ProgressStyle.BAR),
    )
