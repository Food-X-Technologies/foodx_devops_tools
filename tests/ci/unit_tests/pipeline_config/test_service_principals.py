#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import io
import logging
import os
import pathlib
import tempfile
import typing

from foodx_devops_tools.pipeline_config import load_service_principals
from foodx_devops_tools.pipeline_config.service_principals import (
    _decrypt_vault,
    _encrypt_vault,
    managed_file_decrypt,
)


@contextlib.contextmanager
def encrypted_file(
    content: str, password: str
) -> typing.Generator[typing.Tuple[pathlib.Path, pathlib.Path], None, None]:
    with tempfile.TemporaryDirectory() as dir:
        dir_path = pathlib.Path(dir)
        encrypted_file_path = dir_path / "some.file"

        password_file_path = dir_path / "password-file"
        with password_file_path.open("w") as f:
            f.write(password)

        unencrypted_file_path = dir_path / "plain.file"
        with unencrypted_file_path.open("w") as f:
            f.write(content)

        _encrypt_vault(
            encrypted_file_path, password_file_path, unencrypted_file_path
        )

        os.remove(unencrypted_file_path)
        os.remove(password_file_path)

        assert encrypted_file_path.is_file()
        with encrypted_file_path.open("r") as f:
            encrypted_content = f.read()

        assert encrypted_content.startswith("$ANSIBLE_VAULT;1.1;AES256")

        yield encrypted_file_path


class TestManagedFile:
    def test_clean(self, caplog):
        with caplog.at_level(logging.DEBUG):
            file_text = """
    ---
    service_principals:
      sub1_name:
        id: 12345-id
        name: principal-name1
        secret: verysecret
    """
            decrypt_token = "somesecret"
            with encrypted_file(file_text, decrypt_token) as (
                encrypted_file_path
            ):
                expected_plain_file = pathlib.Path(
                    str(encrypted_file_path) + ".yml"
                )
                expected_password_file = pathlib.Path(
                    str(encrypted_file_path) + ".password"
                )
                # temporary files do not exist
                assert not expected_plain_file.exists()
                assert not expected_password_file.exists()

                with managed_file_decrypt(
                    encrypted_file_path, decrypt_token
                ) as f:
                    # plain text file has been created
                    assert expected_plain_file.is_file()

                    content = f.read()

                    assert content == file_text

                # temporary files have been erased
                assert not expected_plain_file.exists()
                assert not expected_password_file.exists()


class TestLoadServicePrincipals:
    mock_encrypted_path = pathlib.Path("some/file")
    mock_password_path = pathlib.Path("other/file")

    def test_simple(self, mocker):
        file_text = """
---
service_principals:
  sub1_name:
    id: 12345-id
    name: principal-name1
    secret: verysecret
  sub2_name:
    id: 123456-id
    name: principal-name2
    secret: verysecret
"""
        mock_stream = io.StringIO(initial_value=file_text)
        mock_context = mocker.patch(
            "foodx_devops_tools.pipeline_config.service_principals.managed_file_decrypt"
        )
        mock_context.return_value.__enter__.return_value = mock_stream

        result = load_service_principals(
            self.mock_encrypted_path, self.mock_password_path
        )

        assert len(result.service_principals) == 2
        assert result.service_principals["sub1_name"].id == "12345-id"
        assert result.service_principals["sub1_name"].name == "principal-name1"
        assert result.service_principals["sub1_name"].secret == "verysecret"

        assert result.service_principals["sub2_name"].id == "123456-id"

    def test_load(self):
        file_text = """
---
service_principals:
  sub1_name:
    id: 12345-id
    name: principal-name1
    secret: verysecret
  sub2_name:
    id: 123456-id
    name: principal-name2
    secret: verysecret
"""
        decrypt_token = "somesecret"
        with encrypted_file(file_text, decrypt_token) as (encrypted_file_path):
            result = load_service_principals(encrypted_file_path, decrypt_token)

        assert len(result.service_principals) == 2
        assert result.service_principals["sub1_name"].id == "12345-id"
        assert result.service_principals["sub1_name"].name == "principal-name1"
        assert result.service_principals["sub1_name"].secret == "verysecret"

        assert result.service_principals["sub2_name"].id == "123456-id"
