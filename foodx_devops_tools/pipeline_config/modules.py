#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Applications, modules configuration I/O."""

import pathlib
import typing

import pydantic

from ._loader import load_configuration

ENTITY_NAME = "modules"
ENTITY_SINGULAR = "module"


class ModuleDefinitionsError(Exception):
    """Problem loading module definitions."""


ApplicationDeclarations = typing.List[str]


class SingularModuleDefinition(pydantic.BaseModel):
    """A single module definition."""

    applications: ApplicationDeclarations


ValueType = typing.List[typing.Dict[str, SingularModuleDefinition]]

T = typing.TypeVar("T", bound="ModulesDefinition")


class ModulesDefinition(pydantic.BaseModel):
    """Definition of modules."""

    modules: ValueType

    @pydantic.validator(ENTITY_NAME)
    def check_modules(
        cls: pydantic.BaseModel, modules_candidate: ValueType
    ) -> ValueType:
        """Validate ``modules`` field."""
        module_names: list = list()
        for x in modules_candidate:
            module_names += list(x.keys())
        if any([not x for x in module_names]):
            raise ValueError(
                "Empty {0} names prohibited".format(ENTITY_SINGULAR)
            )
        if len(set(module_names)) != len(module_names):
            raise ValueError(
                "Duplicate {0} names prohibited".format(ENTITY_SINGULAR)
            )

        return modules_candidate


def load_modules(file_path: pathlib.Path) -> ModulesDefinition:
    """
    Load module definitions from file.

    Args:
        file_path: Path to module definitions file.

    Returns:
        Module definitions.
    Raises:
        ModulesDefinitionError: If an error occurs loading the file.
    """
    result = load_configuration(
        file_path, ModulesDefinition, ModuleDefinitionsError, ENTITY_NAME
    )

    return typing.cast(ModulesDefinition, result)
