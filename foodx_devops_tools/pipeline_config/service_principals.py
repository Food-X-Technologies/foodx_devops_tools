#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Service principal secrets deployment configuration I/O."""


import typing

import pydantic
import ruamel.yaml


class PrincipalConfiguration(pydantic.BaseModel):
    """Define id and key needed for service principal access."""

    id: str
    secret: str
    name: str


class ServicePrincipals(pydantic.BaseModel):
    """Define a collection of service principal id's and keys."""

    service_principals: typing.Dict[str, PrincipalConfiguration]


def load_service_principals(content: str) -> ServicePrincipals:
    """Load service principal secrets from a string."""
    yaml = ruamel.yaml.YAML(typ="safe")

    yaml_data = yaml.load(content)
    this_object = ServicePrincipals.parse_obj(yaml_data)

    return this_object
