#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Release states deployment configuration I/O."""

import pathlib
import typing

import pydantic

from ._exceptions import ReleaseStatesDefinitionError
from ._loader import load_configuration

ENTITY_NAME = "release_states"

T = typing.TypeVar("T", bound="ReleaseStatesDefinition")

ValueType = typing.List[str]


class ReleaseStatesDefinition(pydantic.BaseModel):
    """Definition of deployment release states."""

    release_states: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_release_states(
        cls: pydantic.BaseModel, value: ValueType
    ) -> ValueType:
        """Validate ``release_states`` field."""
        if not value:
            raise ValueError("Empty release state names prohibited")
        if len(set(value)) != len(value):
            raise ValueError("Duplicate release state names prohibited")

        return value


def load_release_states(file_path: pathlib.Path) -> ReleaseStatesDefinition:
    """
    Load release state definitions from file.

    Args:
        file_path: Path to system definitions file.

    Returns:
        Release state definitions.
    Raises:
        ReleaseStateDefinitionError: If an error occurs loading the file.
    """
    result = load_configuration(
        file_path,
        ReleaseStatesDefinition,
        ReleaseStatesDefinitionError,
        ENTITY_NAME,
    )

    return typing.cast(ReleaseStatesDefinition, result)
