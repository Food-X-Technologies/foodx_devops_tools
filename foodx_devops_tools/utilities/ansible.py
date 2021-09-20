#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Ansible related utilities."""

import contextlib
import logging
import os
import pathlib
import typing

from ._exceptions import AnsibleVaultError
from .command import detect_venv_command, run_command

log = logging.getLogger(__name__)


def _encrypt_vault(
    encrypted_file_path: pathlib.Path,
    password_file_path: pathlib.Path,
    unencrypted_file_path: pathlib.Path,
) -> None:
    command_path = str(detect_venv_command("ansible-vault"))
    this_command = [
        command_path,
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
        raise AnsibleVaultError(message)


def _decrypt_vault(
    encrypted_file_path: pathlib.Path,
    decrypted_path: pathlib.Path,
    password_file_path: pathlib.Path,
) -> None:
    command_path = str(detect_venv_command("ansible-vault"))
    this_command = [
        command_path,
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
        raise AnsibleVaultError(message)


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
    except AnsibleVaultError:
        raise
    except Exception as e:
        message = "Failed to decrypt Ansible vault file, {0}".format(str(e))
        log.error(message)
        raise AnsibleVaultError(message) from e
    finally:
        if decrypted_path.exists():
            os.remove(decrypted_path)
        if password_file_path.exists():
            os.remove(password_file_path)
