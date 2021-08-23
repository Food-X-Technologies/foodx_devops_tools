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

from ._exceptions import ClientsDefinitionError
from ._loader import load_configuration

ENTITY_NAME = "clients"

ReleaseStatesValueType = typing.List[str]


class SingularClientDefinition(pydantic.BaseModel):
    """A single client definition."""

    depends_on: typing.Optional[typing.Dict[str, typing.Optional[str]]]
    pseudonym: typing.Optional[str]
    release_states: ReleaseStatesValueType
    system: str


T = typing.TypeVar("T", bound="ClientsDefinition")


ValueType = typing.Dict[str, SingularClientDefinition]


class ClientsDefinition(pydantic.BaseModel):
    """Definition of deployment clients."""

    clients: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_clients(
        cls: pydantic.BaseModel, clients_candidate: ValueType
    ) -> ValueType:
        """Validate ``clients`` field."""
        if not clients_candidate:
            raise ValueError("Empty client names prohibited")
        if len(set(clients_candidate)) != len(clients_candidate):
            raise ValueError("Duplicate client names prohibited")

        for name, client_value in clients_candidate.items():
            if client_value.depends_on is not None:
                # check that the "depends_on" target exists.
                if any(
                    [
                        x not in clients_candidate
                        for x in client_value.depends_on.keys()
                    ]
                ):
                    raise ValueError(
                        "Nonexistent dependency in client, " "{0}".format(name)
                    )
                for this_name in [
                    x for x, y in client_value.depends_on.items() if not y
                ]:
                    # default to the last release state from the dependency
                    # client.
                    default_value = clients_candidate[this_name].release_states[
                        -1
                    ]
                    clients_candidate[name].depends_on[
                        this_name
                    ] = default_value  # type: ignore

        return clients_candidate


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
