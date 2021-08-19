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
        success = enum.auto()

    code: ResultType
    message: typing.Optional[str] = None


T = typing.TypeVar("T", bound="DeploymentStatus")


class DeploymentStatus:
    """Coordinate reporting of asynchronous deployment status."""

    __iteration_context: str
    __lock: asyncio.Lock
    __status: typing.Dict[str, DeploymentState]

    STATE_COLOURS = {
        DeploymentState.ResultType.pending: "white",
        DeploymentState.ResultType.in_progress: "orange",
        DeploymentState.ResultType.cancelled: "yellow",
        DeploymentState.ResultType.failed: "red",
        DeploymentState.ResultType.success: "green",
    }

    def __init__(self: T, iteration_context: str) -> None:
        """Construct ``DeploymentStatus`` object."""
        self.__iteration_context = iteration_context
        self.__lock = asyncio.Lock()
        self.__status = dict()

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
        async with self.__lock:
            self.__status[name] = DeploymentState(
                code=DeploymentState.ResultType.pending
            )

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
        async with self.__lock:
            self.__status[name].code = code
            self.__status[name].message = message

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
        async with self.__lock:
            result = copy.deepcopy(self.__status[name])

        return result

    async def names(self: T) -> typing.Set[str]:
        """
        Read the name registered for deployment monitoring.

        Returns:
            Set of deployment names registered.
        """
        async with self.__lock:
            result = set(self.__status.keys())

        return result

    async def __monitor_status(self: T) -> None:
        completed = False
        while not completed:
            status = {n: await self.read(n) for n in await self.names()}
            if not status:
                message = "status is empty, {0}".format(
                    self.__iteration_context
                )
                log.info(message)
                click.echo(click.style(message, fg="yellow"))
            else:
                for n, s in status.items():
                    message = "{0}: {1} {2}".format(
                        self.__iteration_context, n, s.code.name
                    )
                    this_colour = self.STATE_COLOURS[s.code]
                    log.info(message)
                    click.echo(click.style(message, fg=this_colour))
                if all(
                    x
                    in [
                        DeploymentState.ResultType.success,
                        DeploymentState.ResultType.failed,
                        DeploymentState.ResultType.cancelled,
                    ]
                    for x in status.values()
                ):
                    completed = True
                    log.info(
                        "all deployments succeeded for context, {0}".format(
                            self.__iteration_context
                        )
                    )

            if not completed:
                log.debug(
                    "status monitor sleeping for, {0} seconds".format(
                        DEFAULT_MONITOR_SLEEP_SECONDS
                    )
                )
                await asyncio.sleep(DEFAULT_MONITOR_SLEEP_SECONDS)

    async def start_monitor(self: T) -> None:
        """
        Start the concurrent deployment status monitor.

        Status is reported to console and log until all members have hit one
        of the three deployment termination states [success|failed|cancelled].
        """
        asyncio.create_task(self.__monitor_status())
