#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Service principal secrets deployment configuration I/O."""

import logging
import pathlib
import typing

import pydantic
import ruamel.yaml

from foodx_devops_tools.utilities.ansible import (
    AnsibleVaultError,
    managed_file_decrypt,
)

from ._exceptions import ServicePrincipalsError

log = logging.getLogger(__name__)


class PrincipalConfiguration(pydantic.BaseModel):
    """Define id and key needed for service principal access."""

    id: str
    secret: str
    name: str


ValueType = typing.Dict[str, PrincipalConfiguration]


class ServicePrincipals(pydantic.BaseModel):
    """Define a collection of service principal id's and keys."""

    service_principals: ValueType


def load_service_principals(
    encrypted_file_path: pathlib.Path, decrypt_token: str
) -> ServicePrincipals:
    """Load service principal secrets from a string."""
    yaml = ruamel.yaml.YAML(typ="safe")
    try:
        with managed_file_decrypt(
            encrypted_file_path, decrypt_token
        ) as decrypted_stream:
            yaml_data = yaml.load(decrypted_stream)

        this_object = ServicePrincipals.parse_obj(yaml_data)

        return this_object
    except AnsibleVaultError as e:
        raise ServicePrincipalsError(str(e)) from e
