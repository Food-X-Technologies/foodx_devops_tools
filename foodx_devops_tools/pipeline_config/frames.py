#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Applications, frames configuration I/O."""

import pathlib
import typing

import pydantic

from ._loader import load_configuration

ENTITY_NAME = "frames"
ENTITY_SINGULAR = "frame"


class FrameDefinitionsError(Exception):
    """Problem loading frame definitions."""


ApplicationDeclarations = typing.List[str]
DependencyDeclarations = typing.List[str]
PathDeclarations = typing.List[str]


class SingularFrameDefinition(pydantic.BaseModel):
    """A single frame definition."""

    applications: ApplicationDeclarations
    depends_on: typing.Optional[DependencyDeclarations]
    paths: typing.Optional[PathDeclarations]


ValueType = typing.Dict[str, SingularFrameDefinition]

T = typing.TypeVar("T", bound="FramesDefinition")


class FramesDefinition(pydantic.BaseModel):
    """Definition of frames."""

    frames: ValueType
    paths: typing.Optional[PathDeclarations]

    @pydantic.validator(ENTITY_NAME)
    def check_frames(cls: pydantic.BaseModel, frames_candidate: dict) -> dict:
        """Validate ``frames`` field."""
        frame_names: list = list(frames_candidate.keys())
        if any([not x for x in frame_names]):
            raise ValueError(
                "Empty {0} names prohibited".format(ENTITY_SINGULAR)
            )
        if len(set(frame_names)) != len(frame_names):
            raise ValueError(
                "Duplicate {0} names prohibited".format(ENTITY_SINGULAR)
            )

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
                raise ValueError(
                    "Unknown frame dependency, {0}".format(str(item.depends_on))
                )

        return frames_candidate


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
    result = load_configuration(
        file_path, FramesDefinition, FrameDefinitionsError, ENTITY_NAME
    )

    return typing.cast(FramesDefinition, result)
