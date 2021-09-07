#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Static secrets deployment configuration I/O."""

import logging
import pathlib
import typing

import pydantic

from foodx_devops_tools.utilities.ansible import AnsibleVaultError
from foodx_devops_tools.utilities.io import load_encrypted_data

from ._exceptions import StaticSecretsError

log = logging.getLogger(__name__)


ValueType = typing.Dict[str, typing.Dict[str, typing.Any]]


class StaticSecrets(pydantic.BaseModel):
    """Define a collection of static secrets."""

    static_secrets: ValueType


def load_static_secrets(
    secrets_paths: typing.Set[pathlib.Path], decrypt_token: str
) -> StaticSecrets:
    """Load static secrets from the relevant directory and it's files."""
    try:
        secrets_data: dict = {
            "static_secrets": dict(),
        }
        for this_path in secrets_paths:
            if this_path.is_file():
                yaml_data = load_encrypted_data(this_path, decrypt_token)
                if "static_secrets" in yaml_data:
                    secrets_data["static_secrets"].update(
                        yaml_data["static_secrets"]
                    )
                else:
                    log.error(
                        f"static_secrets field not present in file, {this_path}"
                    )

        this_object = StaticSecrets.parse_obj(secrets_data)

        return this_object
    except (AnsibleVaultError, NotADirectoryError, FileNotFoundError) as e:
        raise StaticSecretsError(str(e)) from e
