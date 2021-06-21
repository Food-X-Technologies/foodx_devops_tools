#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Subscriptions deployment configuration I/O."""

import pathlib
import typing

import pydantic

from ._loader import load_configuration

ENTITY_NAME = "deployments"


class DeploymentsDefinitionError(Exception):
    """Problem loading deployment definitions."""


class SingularDeployment(pydantic.BaseModel):
    """Definition of a singular deployment."""

    locations: typing.List[str]
    subscription: str


T = typing.TypeVar("T", bound="DeploymentsDefinition")

ValueType = typing.Dict[str, SingularDeployment]


class DeploymentsDefinition(pydantic.BaseModel):
    """Definition of deployments."""

    deployments: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_deployments(
        cls: pydantic.BaseModel, value: ValueType
    ) -> ValueType:
        """Validate ``deployments`` field."""
        if not value:
            raise ValueError("Empty deployment names prohibited")

        return value


def load_deployments(file_path: pathlib.Path) -> DeploymentsDefinition:
    """
    Load client definitions from file.

    Args:
        file_path: Path to client definitions file.

    Returns:
        Deployment definitions.
    Raises:
        DeploymentsDefinitionError: If an error occurs loading the file.
    """
    result = load_configuration(
        file_path,
        DeploymentsDefinition,
        DeploymentsDefinitionError,
        ENTITY_NAME,
    )

    return typing.cast(DeploymentsDefinition, result)
