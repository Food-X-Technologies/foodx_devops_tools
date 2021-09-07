#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""I/O related utilities."""

import pathlib
import typing

import ruamel.yaml

from .ansible import managed_file_decrypt


def acquire_token(password_file: typing.IO) -> str:
    """
    Read a password token from the specified stream.

    Args:
        password_file: Input file stream to read password token from.

    Returns:
        Read token.
    """
    with password_file:
        content = password_file.read()

    return content


def load_encrypted_data(this_file: pathlib.Path, decrypt_token: str) -> dict:
    """Load YAML data from an Ansible Vault encrypted file."""
    yaml = ruamel.yaml.YAML(typ="safe")
    with managed_file_decrypt(this_file, decrypt_token) as decrypted_stream:
        yaml_data = yaml.load(decrypted_stream)

    return yaml_data
