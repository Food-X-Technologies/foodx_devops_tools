#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Check log file for specific content."""

import logging
import mmap
import pathlib
import typing

log = logging.getLogger(__name__)


class CredentialLeakageError(Exception):
    """Test for credentials in a file has failed."""


def check_credential_leakage(
    secrets: typing.Set[str], log_file: pathlib.Path
) -> None:
    """
    Check a file for the presence of the specified string.

    Args:
        secrets: Text to check for in file.
        log_file: File to check for string.

    Raises:
        CredentialLeakageError: If the specified string is found in the text
                                file.
    """
    tests_failed: typing.List[bool] = list()
    with log_file.open(mode="rb") as f:
        this_map = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        for this_secret in secrets:
            result = this_map.find(this_secret.encode())
            if result == -1:
                # the string was not found in the file so the test PASSED
                tests_failed.append(False)
            else:
                # the string was found in the file so the test FAILED
                tests_failed.append(True)

    if any(tests_failed):
        log.debug(f"check_credential_leakage, {tests_failed}")
        raise CredentialLeakageError(
            f"Credentials leaked into log file, {log_file}"
        )
