#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Service principal secrets deployment configuration I/O."""

import contextlib
import logging
import os
import pathlib
import typing

import pydantic
import ruamel.yaml

from foodx_devops_tools.utilities import run_command

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


def _encrypt_vault(
    encrypted_file_path: pathlib.Path,
    password_file_path: pathlib.Path,
    unencrypted_file_path: pathlib.Path,
) -> None:
    this_command = [
        "ansible-vault",
        "encrypt",
        "--output",
        str(encrypted_file_path),
        "--vault-password-file",
        str(password_file_path),
        str(unencrypted_file_path),
    ]
    result = run_command(this_command)
    if result.returncode != 0:
        message = "Error encrypting Ansible vault file, {0}".format(
            encrypted_file_path
        )
        log.debug("stdout, {0}".format(result.stdout))
        log.debug("stderr, {0}".format(result.stderr))
        raise ServicePrincipalsError(message)


def _decrypt_vault(
    encrypted_file_path: pathlib.Path,
    decrypted_path: pathlib.Path,
    password_file_path: pathlib.Path,
) -> None:
    this_command = [
        "ansible-vault",
        "decrypt",
        "--output",
        str(decrypted_path),
        "--vault-password-file",
        str(password_file_path),
        str(encrypted_file_path),
    ]
    result = run_command(this_command)
    if result.returncode != 0:
        message = "Error decrypting Ansible vault file, {0}".format(
            encrypted_file_path
        )
        log.debug("stdout, {0}".format(result.stdout))
        log.debug("stderr, {0}".format(result.stderr))
        raise ServicePrincipalsError(message)


@contextlib.contextmanager
def managed_file_decrypt(
    encrypted_file_path: pathlib.Path, decrypt_token: str
) -> typing.Generator[typing.TextIO, None, None]:
    """
    Manage the decryption of an Ansible vault within a context.

    The encrypted Ansible vault is decrypted to an unencrypted file for the
    duration of the context. On context exit the unencrypted file is deleted.

    Args:
        encrypted_file_path: Path to encrypted file.
        decrypt_token: Token for decrypting Ansible vault.

    Yields:
        File stream object of decrypted file.
    """
    decrypted_path = pathlib.Path(str(encrypted_file_path) + ".yml")
    password_file_path = pathlib.Path(str(encrypted_file_path) + ".password")
    try:
        with password_file_path.open(mode="w") as f:
            f.write(decrypt_token)
        _decrypt_vault(encrypted_file_path, decrypted_path, password_file_path)
        os.remove(password_file_path)

        with decrypted_path.open(mode="r") as f:
            yield f
    except ServicePrincipalsError:
        raise
    except Exception as e:
        message = "Failed to decrypt Ansible vault file, {0}".format(str(e))
        log.error(message)
        raise ServicePrincipalsError(message) from e
    finally:
        if decrypted_path.exists():
            os.remove(decrypted_path)
        if password_file_path.exists():
            os.remove(password_file_path)


def load_service_principals(
    encrypted_file_path: pathlib.Path, decrypt_token: str
) -> ServicePrincipals:
    """Load service principal secrets from a string."""
    yaml = ruamel.yaml.YAML(typ="safe")
    with managed_file_decrypt(
        encrypted_file_path, decrypt_token
    ) as decrypted_stream:
        yaml_data = yaml.load(decrypted_stream)

    this_object = ServicePrincipals.parse_obj(yaml_data)

    return this_object
