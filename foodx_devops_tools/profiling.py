#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Utilities for maintaining timing information."""

import contextlib
import datetime
import logging
import time
import typing

log = logging.getLogger(__name__)

T = typing.TypeVar("T", bound="Timer")


class Timer:
    """A simple relative monotonic timer."""

    def __init__(self: T) -> None:
        """Construct ``Timer`` object."""
        self.start_time_seconds: float = 0.0
        self.stop_time_seconds: float = 0.0

    def start(self: T) -> None:
        """Record the start time."""
        self.start_time_seconds = time.monotonic()

    def stop(self: T) -> None:
        """Record the stop time."""
        self.stop_time_seconds = time.monotonic()

    @property
    def elapsed_time_seconds(self: T) -> float:
        """Calculate the elapsed time interval in seconds."""
        return self.stop_time_seconds - self.start_time_seconds

    @property
    def elapsed_time_formatted(self: T) -> str:
        """Calculate the elapsed time and format into a string."""
        return str(datetime.timedelta(seconds=self.elapsed_time_seconds))

    def log_duration(
        self: T, this_log: logging.Logger, iteration_context: str
    ) -> None:
        """Log the elapsed time of the iteration."""
        this_log.info(
            f"{iteration_context} "
            f"elapsed time, {self.elapsed_time_formatted}"
        )


@contextlib.contextmanager
def timing(
    this_log: logging.Logger,
    iteration_context: str,
) -> typing.Generator[Timer, None, Timer]:
    """Manage the context of calculating a time interval."""
    this_timer = Timer()
    this_timer.start()

    yield this_timer

    this_timer.stop()
    this_timer.log_duration(this_log, iteration_context)

    return this_timer
