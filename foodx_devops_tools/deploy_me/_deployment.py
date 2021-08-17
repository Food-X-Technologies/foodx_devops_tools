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
import pathlib
import re
import typing

from foodx_devops_tools.azure.cloud.resource_group import (
    deploy as deploy_resource_group,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    validate as validate_resource_group,
)
from foodx_devops_tools.pipeline_config import (
    ApplicationDeploymentSteps,
    FlattenedDeployment,
    PipelineConfiguration,
    SingularFrameDefinition,
)

log = logging.getLogger(__name__)

SUBSCRIPTION_NAME_REGEX = (
    r"(?P<system>[a-z0-9]+)_(?P<client>[a-z0-9]+)_(?P<state>[a-z0-9]+)"
)


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
        messages = list()
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


def _construct_resource_group_name(
    application_name: str, frame_name: str, client: str
) -> str:
    """Construct a resource group name from deployment context."""
    return "-".join([application_name, frame_name, client])


def _construct_fqdn(
    leaf_name: str, domain_root: str, client: str, subscription_name: str
) -> str:
    """Construct an FQDN from deployment context."""
    this_match = re.match(SUBSCRIPTION_NAME_REGEX, subscription_name)
    if this_match is not None:
        subd_state = this_match.group("state")
    else:
        # assume the entire subscription name is DNS valid
        subd_state = subscription_name

    return ".".join([leaf_name, subd_state, client, domain_root])


def _mangle_validation_resource_group(current_name: str, suffix: str) -> str:
    this_suffix = re.sub(r"[_.]", "-", suffix)
    mangled_name = f"{current_name}-{this_suffix}"

    return mangled_name


async def deploy_application(
    application_data: ApplicationDeploymentSteps,
    deployment_data: FlattenedDeployment,
    application_status: DeploymentStatus,
    enable_validation: bool,
    frame_folder: pathlib.Path,
) -> None:
    """
    Deploy the steps of a frame application.

    Application steps must be deployed in sequence (serially).
    """
    this_context = str(deployment_data.data.iteration_context)

    try:
        await application_status.initialize(this_context)
        log.debug("application deployment, {0}".format(this_context))

        await application_status.write(
            this_context, DeploymentState.ResultType.in_progress
        )

        puff_frame_data = deployment_data.data.puff_map.frames[
            deployment_data.context.frame_name
        ]
        puff_application_data = puff_frame_data.applications[
            deployment_data.context.application_name
        ]
        puff_parameter_data = puff_application_data.arm_parameters_files[
            deployment_data.context.release_state
        ][deployment_data.context.azure_subscription_name]
        for this_step in application_data:
            resource_group = (
                _construct_resource_group_name(
                    deployment_data.context.application_name,
                    deployment_data.context.frame_name,
                    deployment_data.context.client,
                )
                if not this_step.resource_group
                else this_step.resource_group
            )
            arm_template_path = (
                frame_folder / this_step.arm_file
                if this_step.arm_file
                else frame_folder
                / "{0}.json".format(deployment_data.context.application_name)
            )
            arm_parameters_path = (
                frame_folder / puff_parameter_data[this_step.name]
            )
            deployment_arguments: dict = {
                "resource_group_name": resource_group,
                "arm_template_path": arm_template_path,
                "arm_parameters_path": arm_parameters_path,
                "location": deployment_data.data.location_primary,
                "mode": this_step.mode.value,
                "subscription": deployment_data.context.azure_subscription_name,
            }

            log.debug(str(deployment_data.context))
            log.debug(str(deployment_data.data))
            if enable_validation:
                log.info("validation deployment enabled")
                deployment_arguments[
                    "resource_group_name"
                ] = _mangle_validation_resource_group(
                    deployment_arguments["resource_group_name"],
                    deployment_data.context.pipeline_id,
                )
                log.info(
                    "validation resource group name, {0}".format(
                        deployment_arguments["resource_group_name"]
                    )
                )
                await validate_resource_group(**deployment_arguments)
            else:
                log.info("deployment enabled")
                await deploy_resource_group(**deployment_arguments)

        await application_status.write(
            this_context, DeploymentState.ResultType.success
        )
    except asyncio.CancelledError:
        message = "async cancelled signal"
        log.error(message)
        await application_status.write(
            this_context,
            DeploymentState.ResultType.cancelled,
            message,
        )
        raise
    except Exception as e:
        message = str(e)
        log.error(message)
        await application_status.write(
            this_context,
            DeploymentState.ResultType.failed,
            message,
        )


async def deploy_frame(
    frame_data: SingularFrameDefinition,
    deployment_data: FlattenedDeployment,
    frame_status: DeploymentStatus,
    enable_validation: bool,
) -> None:
    """
    Deploy the applications of a frame.

    Frame applications are deployed concurrently (in parallel).
    """
    this_context = str(deployment_data.data.iteration_context)

    await frame_status.initialize(this_context)
    log.debug("frame deployment, {0}".format(this_context))

    application_status = DeploymentStatus()
    await asyncio.gather(
        *[
            deploy_application(
                application_data,
                deployment_data.copy_add_application(application_name),
                application_status,
                enable_validation,
                frame_data.folder,
            )
            for application_name, application_data in frame_data.applications.items()  # noqa: E501
        ],
        return_exceptions=False,
    )
    log.debug(
        "deployment data, {0}".format(str(dataclasses.asdict(deployment_data)))
    )

    results = [await frame_status.read(x) for x in await frame_status.names()]
    condensed_result = assess_results(results)
    await frame_status.write(
        this_context, condensed_result.code, condensed_result.message
    )


async def do_deploy(
    configuration: PipelineConfiguration,
    deployment_data: FlattenedDeployment,
    enable_validation: bool,
) -> DeploymentState:
    """Deploy the frames in a flattened deployment configuration."""
    this_frames = configuration.frames
    frame_deployment_status = DeploymentStatus()
    deployment_data.data.iteration_context.append(
        deployment_data.data.deployment_tuple
    )
    deployment_data.data.puff_map = configuration.puff_map

    await asyncio.gather(
        *[
            deploy_frame(
                frame_data,
                deployment_data.copy_add_frame(frame_name),
                frame_deployment_status,
                enable_validation,
            )
            for frame_name, frame_data in this_frames.frames.items()
        ],
        return_exceptions=False,
    )
    log.debug(
        "deployment data, {0}".format(str(dataclasses.asdict(deployment_data)))
    )

    results = [
        await frame_deployment_status.read(x)
        for x in await frame_deployment_status.names()
    ]
    condensed_result = assess_results(results)

    return condensed_result
