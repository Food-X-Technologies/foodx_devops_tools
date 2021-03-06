#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Deployment status data model."""

import asyncio
import copy
import dataclasses
import enum
import logging
import typing

import click

log = logging.getLogger(__name__)

DEFAULT_MONITOR_SLEEP_SECONDS = 10


@dataclasses.dataclass
class DeploymentState:
    """Signal state of a deployment."""

    @enum.unique
    class ResultType(enum.Enum):
        """Deployment state enumeration."""

        cancelled = enum.auto()
        failed = enum.auto()
        in_progress = enum.auto()
        pending = enum.auto()
        skipped = enum.auto()
        success = enum.auto()

    COMPLETED_OK = {
        ResultType.skipped,
        ResultType.success,
    }
    COMPLETED_RESULTS = {
        ResultType.cancelled,
        ResultType.failed,
        ResultType.skipped,
        ResultType.success,
    }

    code: ResultType
    message: typing.Optional[str] = None


def all_success(values: typing.List[DeploymentState]) -> bool:
    """
    Evaluate if a list of deployment states are all succeeded.

    NOTE: "skipped" is also considered a success here.
    """
    result = all([x.code in DeploymentState.COMPLETED_OK for x in values])
    return result


def all_completed(values: typing.List[DeploymentState]) -> bool:
    """
    Evaluate if a list of deployment states are all completed.

    "All completed" is defined here as any one of the deployment states that
    can be interpreted as the process having stopped for some reason;
    success, failed or cancelled.
    """
    result = all([x.code in DeploymentState.COMPLETED_RESULTS for x in values])
    return result


def any_completed_dirty(values: typing.List[DeploymentState]) -> bool:
    """Evaluate if any deployment states completed without success."""
    result = any(
        [
            (x.code in DeploymentState.COMPLETED_RESULTS)
            and (x.code not in DeploymentState.COMPLETED_OK)
            for x in values
        ]
    )
    return result


T = typing.TypeVar("T", bound="DeploymentStatus")


class DeploymentStatus:
    """Coordinate reporting of asynchronous deployment status."""

    __iteration_context: str
    __rw_lock: asyncio.Lock
    __state_updates: asyncio.Queue
    __status: typing.Dict[str, DeploymentState]
    __timeout_seconds: float

    STATE_COLOURS = {
        DeploymentState.ResultType.cancelled: "yellow",
        DeploymentState.ResultType.failed: "red",
        DeploymentState.ResultType.in_progress: "cyan",
        DeploymentState.ResultType.pending: "white",
        DeploymentState.ResultType.skipped: "white",
        DeploymentState.ResultType.success: "green",
    }

    EVENT_KEY_SUCCEEDED = "_all_ok"
    EVENT_KEY_COMPLETED = "_all_completed"

    def __init__(
        self: T, iteration_context: str, timeout_seconds: float
    ) -> None:
        """Construct ``DeploymentStatus`` object."""
        self.__events: dict = {
            self.EVENT_KEY_COMPLETED: asyncio.Event(),
            self.EVENT_KEY_SUCCEEDED: asyncio.Event(),
        }

        self.__iteration_context = iteration_context
        self.__rw_lock = asyncio.Lock()
        self.__state_updates = asyncio.Queue()
        self.__status = dict()
        self.__timeout_seconds = timeout_seconds

    async def initialize(self: T, name: str) -> None:
        """
        Register a new deployment name to record status against.

        Args:
            name: Name of deployment.

        """
        if name in self.__status:
            log.warning(
                "Re-initializing existing status entry, {0}".format(name)
            )
        async with self.__rw_lock:
            self.__status[name] = DeploymentState(
                code=DeploymentState.ResultType.pending
            )
        log.info(f"initialized deployment status, {name}")

    async def write(
        self: T,
        name: str,
        code: DeploymentState.ResultType,
        message: typing.Optional[str] = None,
    ) -> None:
        """
        Write deployment state for specified deployment name.

        Args:
            name: Name of deployment.
            code: Status code to record.
            message: Status message (optional).
        """
        state_update = DeploymentState(
            code=code,
            message=message,
        )
        await self.__state_updates.put((name, state_update))

    async def read(self: T, name: str) -> DeploymentState:
        """
        Read deployment state for specified deployment name.

        Args:
            name: Name of deployment.

        Returns:
            Read state.
        Raises:
            KeyError: If name does not exist.
        """
        async with self.__rw_lock:
            result = copy.deepcopy(self.__status[name])

        return result

    async def names(self: T) -> typing.Set[str]:
        """
        Read the name registered for deployment monitoring.

        Returns:
            Set of deployment names registered.
        """
        async with self.__rw_lock:
            result = set(self.__status.keys())

        return result

    async def wait_for_completion(self: T, name: str) -> None:
        """
        Block the call until the named deployment has completed.

        Completion state as defined by ``DeploymentState.COMPLETED_RESULTS``.

        Raises:
            asyncio.TimeoutError: If there is a timeout waiting for completion.
        """
        async with self.__rw_lock:
            if name not in self.__events:
                # create an event since this must be the first wait.
                self.__events[name] = asyncio.Event()

            # check the current state to ensure that it is not already where it
            # needs to be.
            self.__evaluate_named_completed(name)

        log.debug(
            "waiting for named completion, {0}, ({1})".format(
                name, self.__iteration_context
            )
        )
        await asyncio.wait_for(
            self.__events[name].wait(), timeout=self.__timeout_seconds
        )
        log.debug(
            "completed event set for name, {0}, ({1})".format(
                name, self.__iteration_context
            )
        )

    async def wait_for_all_completed(self: T) -> None:
        """
        Block the caller until the "all completed" event is triggered.

        "All completed" means that all registered deployment have reached a
        completion state as defined by ``DeploymentState.COMPLETED_RESULTS``.

        Raises:
            asyncio.TimeoutError: If there is a timeout waiting for completion.
        """
        log.debug(
            "waiting for everything completed, {0}".format(
                self.__iteration_context
            )
        )
        await asyncio.wait_for(
            self.__events[self.EVENT_KEY_COMPLETED].wait(),
            timeout=self.__timeout_seconds,
        )
        log.debug(
            "everything completed event set, {0}".format(
                self.__iteration_context
            )
        )

    async def wait_for_all_succeeded(self: T) -> None:
        """
        Block the caller until the "all succeeded" event is triggered.

        "All succeeded" means that all registered deployments have reported a
        ``success`` result.

        Raises:
            asyncio.TimeoutError: If there is a timeout waiting for success.
        """
        log.debug(
            "waiting for everything succeeded, {0}".format(
                self.__iteration_context
            )
        )
        await asyncio.wait_for(
            self.__events[self.EVENT_KEY_SUCCEEDED].wait(),
            timeout=self.__timeout_seconds,
        )
        log.debug(
            "everything succeeded event set, {0}".format(
                self.__iteration_context
            )
        )

    def __report_update(
        self: T, name: str, status: typing.Dict[str, DeploymentState]
    ) -> bool:
        """Report changes in deployment status to console and logs."""
        completed = False
        state = status[name]
        message = "{0}: {1} {2}".format(
            self.__iteration_context, name, state.code.name
        )
        this_colour = self.STATE_COLOURS[state.code]
        log.info(message)
        click.echo(click.style(message, fg=this_colour))

        if all_success(list(status.values())):
            completed = True
            log.info(
                "all deployments succeeded for context, {0}".format(
                    self.__iteration_context
                )
            )
        elif all_completed(list(status.values())):
            completed = True
            log.info(
                "all deployments completed with some failures for "
                "context, {0}".format(self.__iteration_context)
            )

        return completed

    async def __process_state_queue(self: T) -> None:
        log.debug("starting state queue processing")
        completed = False
        while not completed:
            log.debug("waiting for items to be added to state queue")
            name, state_update = await self.__state_updates.get()

            current_status: typing.Dict[str, DeploymentState] = {
                n: await self.read(n) for n in await self.names()
            }
            current_state = current_status[name]

            log.debug(
                f"state update, {name}, {state_update.code.name}, "
                f"{state_update.message}"
            )
            log.debug(
                f"current state, {name}, {current_state.code.name}, "
                f"{current_state.message}"
            )

            if (state_update.code != current_state.code) or (
                state_update.message != current_state.message
            ):
                log.debug(f"status change detected, {name}")
                # state has changed, so evaluate for completion and report state
                async with self.__rw_lock:
                    self.__status[name] = copy.deepcopy(state_update)

                    self.__evaluate_named_completed(name)
                    self.__evaluate_all_success()
                    self.__evaluate_all_completed()

                completed = self.__report_update(name, current_status)
            else:
                message = "nothing to report, {0}".format(
                    self.__iteration_context
                )
                log.info(message)
                click.echo(click.style(message, fg="yellow"))

            self.__state_updates.task_done()

    def __evaluate_named_completed(self: T, name: str) -> None:
        """Evaluate if the named status has completed."""
        # WARNING: assumes self.__rw_lock has been applied
        code = self.__status[name].code
        if (name in self.__events) and (
            code in DeploymentState.COMPLETED_RESULTS
        ):
            self.__events[name].set()

    def __evaluate_all_success(self: T) -> bool:
        """Evaluate if all statuses have *succeeded*."""
        # WARNING: assumes self.__rw_lock has been applied
        values = list(self.__status.values())
        result = all_success(values)
        if result:
            self.__events[self.EVENT_KEY_SUCCEEDED].set()

        return result

    def __evaluate_all_completed(self: T) -> bool:
        """
        Evaluate if all statuses have *completed*.

        Completed => finished but not necessarily due to success. The
        deployment may have failed.
        """
        # WARNING: assumes self.__rw_lock has been applied
        values = list(self.__status.values())
        result = all_completed(values)
        if result:
            self.__events[self.EVENT_KEY_COMPLETED].set()

        return result

    def start_monitor(self: T) -> None:
        """
        Start the concurrent deployment status monitor.

        Status is reported to console and log until all members have hit one
        of the three deployment termination states [success|failed|cancelled].
        """
        asyncio.create_task(self.__process_state_queue())
