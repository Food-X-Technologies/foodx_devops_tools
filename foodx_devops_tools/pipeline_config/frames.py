#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Applications, frames configuration I/O."""

import copy
import enum
import logging
import pathlib
import typing

import pydantic

from ._exceptions import FrameDefinitionsError
from ._loader import load_configuration
from ._structure import FrameFile, StructuredName, StructuredPathCollection

log = logging.getLogger(__name__)

ENTITY_NAME = "frames"
ENTITY_SINGULAR = "frame"

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


class ApplicationStepDelay(pydantic.BaseModel):
    """Define a pause delay for an application step."""

    delay_seconds: int


class ApplicationStepDeploymentDefinition(pydantic.BaseModel):
    """Application resource group deployment definition."""

    mode: DeploymentMode
    name: str
    resource_group: str

    arm_file: typing.Optional[pathlib.Path]
    puff_file: typing.Optional[pathlib.Path]
    static_secrets: typing.Optional[bool] = False


ApplicationDeploymentSteps = typing.List[
    typing.Union[ApplicationStepDeploymentDefinition, ApplicationStepDelay]
]


class ApplicationDefinition(pydantic.BaseModel):
    """A single application definition."""

    depends_on: typing.Optional[DependencyDeclarations]
    steps: ApplicationDeploymentSteps

    @pydantic.validator("steps")
    def check_applications(
        cls: pydantic.BaseModel, steps_candidate: ApplicationDeploymentSteps
    ) -> ApplicationDeploymentSteps:
        """Validate ``steps`` field."""
        step_names: typing.List[str] = [
            x.name
            for x in steps_candidate
            if not isinstance(x, ApplicationStepDelay)
        ]
        if len(step_names) != len(set(step_names)):
            message = "Application step names must be unique, {0}".format(
                str(step_names)
            )
            # log the message here because pydantic exception handling
            # masks the true exception that caused a validation failure.
            log.error(message)
            raise ValueError(message)

        return steps_candidate


ApplicationDeclarations = typing.Dict[str, ApplicationDefinition]


class SingularFrameDefinition(pydantic.BaseModel):
    """A single frame definition."""

    applications: ApplicationDeclarations
    folder: pathlib.Path

    depends_on: typing.Optional[DependencyDeclarations]
    triggers: typing.Optional[TriggersDefinition]

    @pydantic.validator("applications")
    def check_applications(
        cls: pydantic.BaseModel, applications_candidate: dict
    ) -> dict:
        """Validate ``applications`` field."""
        application_names: list = list(applications_candidate.keys())
        if any([not x for x in application_names]):
            message = "Empty {0} names prohibited".format(ENTITY_SINGULAR)
            # log the message here because pydantic exception handling
            # masks the true exception that caused a validation failure.
            log.error(message)
            raise ValueError(message)
        if len(set(application_names)) != len(application_names):
            message = "Duplicate {0} names prohibited".format(ENTITY_SINGULAR)
            # log the message here because pydantic exception handling
            # masks the true exception that caused a validation failure.
            log.error(message)
            raise ValueError(message)

        return applications_candidate

    @pydantic.root_validator
    def check_dependencies(
        cls: pydantic.BaseModel, applications_candidate: dict
    ) -> dict:
        """
        Validate frame dependencies.

        Frames must only declare dependencies on other frames.
        """
        applications: dict = applications_candidate.get("applications", dict())
        frame_names: set = set(applications.keys())
        for name, item in applications.items():
            if item.depends_on and (
                any([x not in frame_names for x in item.depends_on])
            ):
                message = "Unknown application dependency, {0}".format(
                    str(item.depends_on)
                )
                # log the message here because pydantic exception handling
                # masks the true exception that caused a validation failure.
                log.error(message)
                raise ValueError(message)

        return applications_candidate


FrameDeclarations = typing.Dict[str, SingularFrameDefinition]

U = typing.TypeVar("U", bound="FramesTriggersDefinition")


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

    def arm_file_paths(self: U) -> StructuredPathCollection:
        """
        Generate collection of ARM template file paths.

        Paths not specified are defined as ``None``. Default path inferences
        are calculated elsewhere in the application.

        Returns:
            Collection of ARM template file paths indexed by structured name.
        """
        result: StructuredPathCollection = dict()
        for frame_name, frame_data in self.frames.items():
            frame_structure = StructuredName()
            frame_structure.append(frame_name)

            this_folder = frame_data.folder
            for (
                application_name,
                application_data,
            ) in frame_data.applications.items():
                app_structure = copy.deepcopy(frame_structure)
                app_structure.append(application_name)
                for this_step in application_data.steps:
                    if isinstance(
                        this_step, ApplicationStepDeploymentDefinition
                    ):
                        step_structure = copy.deepcopy(app_structure)
                        step_structure.append(this_step.name)

                        arm_name: typing.Optional[pathlib.Path]
                        if this_step.arm_file:
                            arm_name = this_step.arm_file
                        else:
                            # default names are inferred elsewhere
                            arm_name = None

                        result[step_structure] = FrameFile(
                            dir=this_folder, file=arm_name
                        )
        return result

    def puff_file_paths(self: U) -> StructuredPathCollection:
        """
        Generate collection of source puff file paths.

        Paths not specified are defined as ``None``. Default path inferences
        are calculated elsewhere in the application.

        Returns:
            Collection of YAML puff file paths indexed by structured name.
        """
        result: StructuredPathCollection = dict()
        for frame_name, frame_data in self.frames.items():
            frame_structure = StructuredName()
            frame_structure.append(frame_name)

            this_folder = frame_data.folder
            for (
                application_name,
                application_data,
            ) in frame_data.applications.items():
                app_structure = copy.deepcopy(frame_structure)
                app_structure.append(application_name)
                for this_step in application_data.steps:
                    if isinstance(
                        this_step, ApplicationStepDeploymentDefinition
                    ):
                        step_structure = copy.deepcopy(app_structure)
                        step_structure.append(this_step.name)

                        puff_name: typing.Optional[pathlib.Path]
                        if this_step.puff_file:
                            puff_name = this_step.puff_file
                        else:
                            # default names are inferred elsewhere
                            puff_name = None

                        result[step_structure] = FrameFile(
                            dir=this_folder, file=puff_name
                        )
        return result

    def frame_folders(self: U) -> StructuredPathCollection:
        """
        Generate collection of frame folder paths.

        Returns:
            Collection of frame folder paths indexed by structured name.
        """
        result: StructuredPathCollection = dict()
        for frame_name, frame_data in self.frames.items():
            this_structure = StructuredName()
            this_structure.append(frame_name)
            result[this_structure] = FrameFile(
                dir=frame_data.folder, file=pathlib.Path("")
            )

        return result


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
