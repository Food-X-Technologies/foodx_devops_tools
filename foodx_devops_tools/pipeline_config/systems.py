#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Systems deployment configuration I/O."""

import pathlib
import typing

import pydantic

from ._exceptions import SystemsDefinitionError
from ._loader import load_configuration

ENTITY_NAME = "systems"

T = typing.TypeVar("T", bound="SystemsDefinition")

ValueType = typing.List[str]


class SystemsDefinition(pydantic.BaseModel):
    """Definition of deployable systems."""

    systems: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_systems(cls: pydantic.BaseModel, value: ValueType) -> ValueType:
        """Validate ``systems`` field."""
        if not value:
            raise ValueError("Empty system names prohibited")
        if len(set(value)) != len(value):
            raise ValueError("Duplicate system names prohibited")

        return value


def load_systems(file_path: pathlib.Path) -> SystemsDefinition:
    """
    Load system definitions from file.

    Args:
        file_path: Path to system definitions file.

    Returns:
        System definitions.
    Raises:
        SystemsDefinitionError: If an error occurs loading the file.
    """
    result = load_configuration(
        file_path, SystemsDefinition, SystemsDefinitionError, ENTITY_NAME
    )

    return typing.cast(SystemsDefinition, result)
