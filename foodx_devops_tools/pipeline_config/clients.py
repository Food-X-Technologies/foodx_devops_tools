#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Clients deployment configuration I/O."""

import pathlib
import typing

import pydantic

from ._loader import load_configuration

ENTITY_NAME = "clients"


class ClientsDefinitionError(Exception):
    """Problem loading client definitions."""


T = typing.TypeVar("T", bound="ClientsDefinition")


ValueType = typing.List[str]


class ClientsDefinition(pydantic.BaseModel):
    """Definition of deployment clients."""

    clients: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_clients(cls: pydantic.BaseModel, value: ValueType) -> ValueType:
        """Validate ``clients`` field."""
        if not value:
            raise ValueError("Empty client names prohibited")
        if len(set(value)) != len(value):
            raise ValueError("Duplicate client names prohibited")

        return value


def load_clients(file_path: pathlib.Path) -> ClientsDefinition:
    """
    Load client definitions from file.

    Args:
        file_path: Path to client definitions file.

    Returns:
        Client definitions.
    Raises:
        ClientsDefinitionError: If an error occurs loading the file.
    """
    result = load_configuration(
        file_path, ClientsDefinition, ClientsDefinitionError, ENTITY_NAME
    )

    return typing.cast(ClientsDefinition, result)
