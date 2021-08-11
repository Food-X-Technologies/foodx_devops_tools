#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Applications, frames configuration I/O."""

import enum
import logging
import pathlib
import typing

import pydantic

from ._loader import load_configuration

log = logging.getLogger(__name__)

ENTITY_NAME = "frames"
ENTITY_SINGULAR = "frame"


class FrameDefinitionsError(Exception):
    """Problem loading frame definitions."""


DependencyDeclarations = typing.List[str]
GlobPathDeclarations = typing.List[str]


@enum.unique
class DeploymentMode(str, enum.Enum):
    """Azure Cloud resource group deployment mode enumeration."""

    complete = "Complete"
    incremental = "Incremental"


class TriggersDefinition(pydantic.BaseModel):
    """Definition of deployment triggers."""

    paths: GlobPathDeclarations


class ApplicationDeploymentDefinition(pydantic.BaseModel):
    """Application resource group deployment definition."""

    mode: DeploymentMode

    arm_file: typing.Optional[pathlib.Path]
    puff_file: typing.Optional[pathlib.Path]
    resource_group: typing.Optional[str]


ApplicationDeploymentSteps = typing.List[ApplicationDeploymentDefinition]

ApplicationDeclarations = typing.Dict[str, ApplicationDeploymentSteps]


class SingularFrameDefinition(pydantic.BaseModel):
    """A single frame definition."""

    applications: ApplicationDeclarations
    folder: pathlib.Path

    depends_on: typing.Optional[DependencyDeclarations]
    triggers: typing.Optional[TriggersDefinition]


FrameDeclarations = typing.Dict[str, SingularFrameDefinition]


class FramesTriggersDefinition(pydantic.BaseModel):
    """Definition of frames and triggers."""

    frames: FrameDeclarations
    triggers: typing.Optional[TriggersDefinition]

    @pydantic.validator(ENTITY_NAME)
    def check_frames(cls: pydantic.BaseModel, frames_candidate: dict) -> dict:
        """Validate ``frames`` field."""
        frame_names: list = list(frames_candidate.keys())
        if any([not x for x in frame_names]):
            message = "Empty {0} names prohibited".format(ENTITY_SINGULAR)
            # log the message here because pydantic exception handling
            # masks the true exception that caused a validation failure.
            log.error(message)
            raise ValueError(message)
        if len(set(frame_names)) != len(frame_names):
            message = "Duplicate {0} names prohibited".format(ENTITY_SINGULAR)
            # log the message here because pydantic exception handling
            # masks the true exception that caused a validation failure.
            log.error(message)
            raise ValueError(message)

        return frames_candidate

    @pydantic.root_validator
    def check_dependencies(
        cls: pydantic.BaseModel, frames_candidate: dict
    ) -> dict:
        """
        Validate frame dependencies.

        Frames must only declare dependencies on other frames.
        """
        frames: dict = frames_candidate.get("frames", dict())
        frame_names: set = set(frames.keys())
        for name, item in frames.items():
            if item.depends_on and (
                any([x not in frame_names for x in item.depends_on])
            ):
                message = "Unknown frame dependency, {0}".format(
                    str(item.depends_on)
                )
                # log the message here because pydantic exception handling
                # masks the true exception that caused a validation failure.
                log.error(message)
                raise ValueError(message)

        return frames_candidate


ValueType = FramesTriggersDefinition

T = typing.TypeVar("T", bound="FramesDefinition")


class FramesDefinition(pydantic.BaseModel):
    """Definition of frames."""

    frames: ValueType


def load_frames(file_path: pathlib.Path) -> FramesDefinition:
    """
    Load frame definitions from file.

    Args:
        file_path: Path to frame definitions file.

    Returns:
        Frame definitions.
    Raises:
        FrameDefinitionsError: If an error occurs loading the file.
    """
    log.info("loading frame definitions from file, {0}".format(file_path))
    result = load_configuration(
        file_path, FramesDefinition, FrameDefinitionsError, ENTITY_NAME
    )

    return typing.cast(FramesDefinition, result)
