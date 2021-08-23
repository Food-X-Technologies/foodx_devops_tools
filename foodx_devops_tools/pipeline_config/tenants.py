#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Tenants deployment configuration I/O."""

import pathlib
import typing

import pydantic

from ._exceptions import TenantsDefinitionError
from ._loader import load_configuration

ENTITY_NAME = "tenants"


class SingularTenantDefinition(pydantic.BaseModel):
    """Single tenant definition."""

    azure_id: str
    azure_name: typing.Optional[str]


T = typing.TypeVar("T", bound="TenantsDefinition")

ValueType = typing.Dict[str, SingularTenantDefinition]


class TenantsDefinition(pydantic.BaseModel):
    """Definition of deployment Azure tenants."""

    tenants: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_tenants(cls: pydantic.BaseModel, value: ValueType) -> ValueType:
        """Validate ``tenants`` field."""
        if not value:
            raise ValueError("Empty tenant definition prohibited")

        return value


def load_tenants(file_path: pathlib.Path) -> TenantsDefinition:
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
        file_path,
        TenantsDefinition,
        TenantsDefinitionError,
        ENTITY_NAME,
    )

    return typing.cast(TenantsDefinition, result)
