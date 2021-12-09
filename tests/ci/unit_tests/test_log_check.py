#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib
import tempfile

import pytest

from foodx_devops_tools._log_check import (
    CredentialLeakageError,
    check_credential_leakage,
)

EXAMPLE_CONTENT = """
some
really{0}
long
content
"""


def test_detected_secret():
    expected_string = "thisismysecret"

    with tempfile.TemporaryDirectory() as dir:
        file_path = pathlib.Path(dir) / "sample"
        with (file_path).open(mode="w") as f:
            # ensure the secret is in the file so the check can fail
            f.write(EXAMPLE_CONTENT.format(expected_string))

        with pytest.raises(
            CredentialLeakageError, match=r"^Credentials leaked into log file"
        ):
            check_credential_leakage({expected_string}, file_path)


def test_detected_multiple_secrets():
    expected_secrets = {"notinfile", "long"}

    with tempfile.TemporaryDirectory() as dir:
        file_path = pathlib.Path(dir) / "sample"
        with (file_path).open(mode="w") as f:
            # ensure the secret is in the file so the check can fail
            f.write(EXAMPLE_CONTENT.format(expected_secrets))

        with pytest.raises(
            CredentialLeakageError, match=r"^Credentials leaked into log file"
        ):
            check_credential_leakage(expected_secrets, file_path)


def test_not_detected_secret():
    expected_string = "thisismysecret"

    with tempfile.TemporaryDirectory() as dir:
        file_path = pathlib.Path(dir) / "sample"
        with (file_path).open(mode="w") as f:
            # ensure the secret is not in the file so the check runs clean
            f.write(EXAMPLE_CONTENT.format(""))

        check_credential_leakage({expected_string}, file_path)
