#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import copy
import dataclasses
import enum
import logging
import typing

from foodx_devops_tools.pipeline_config import (
    FlattenedDeployment,
    PipelineConfiguration,
    SingularFrameDefinition,
)

log = logging.getLogger(__name__)


class DeploymentError(Exception):
    """Problem executing deployment."""


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

    __lock: asyncio.Lock
    __status: typing.Dict[str, DeploymentState]

    def __init__(self: T) -> None:
        """Construct ``DeploymentStatus`` object."""
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


async def deploy_frame(
    frame_data: typing.Dict[str, SingularFrameDefinition],
    deployment_data: FlattenedDeployment,
    status: DeploymentStatus,
    enable_validation: bool,
) -> None:
    """Deploy the applications of a frame."""
    log.debug(
        "deployment data, {0}".format(str(dataclasses.asdict(deployment_data)))
    )
    for name, data in frame_data.items():
        await status.initialize(name)

        log.debug("frame deployment, {0}".format(name))
        if enable_validation:
            log.debug("validation deployment enabled")
        else:
            log.debug("deployment enabled")


def assess_results(results: typing.List[DeploymentState]) -> DeploymentState:
    """
    Condense an array of deployment results into a single result.

    Args:
        results: Array of results to condense.

    Returns:
        Success, if all results are success. Failed otherwise.
    """
    if all([x.code == DeploymentState.ResultType.success for x in results]):
        this_result = DeploymentState(code=DeploymentState.ResultType.success)
    else:
        messages = [
            x.message
            for x in results
            if x.message and (x.code != DeploymentState.ResultType.success)
        ]
        this_result = DeploymentState(
            code=DeploymentState.ResultType.failed, message=str(messages)
        )

    return this_result


async def do_deploy(
    configuration: PipelineConfiguration,
    deployment_data: FlattenedDeployment,
    enable_validation: bool,
) -> DeploymentState:
    """Iterate over the flattened deployment configurations and deploy each."""
    this_frames = configuration.frames
    deployment_status = DeploymentStatus()

    await asyncio.gather(
        *[
            deploy_frame(
                {name: data},
                deployment_data,
                deployment_status,
                enable_validation,
            )
            for name, data in this_frames.frames.items()
        ],
        return_exceptions=True,
    )
    log.debug(
        "deployment data, {0}".format(str(dataclasses.asdict(deployment_data)))
    )

    results = [
        await deployment_status.read(x) for x in await deployment_status.names()
    ]
    condensed_result = assess_results(results)

    return condensed_result
