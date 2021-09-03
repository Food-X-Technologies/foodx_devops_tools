#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging
import pathlib

from foodx_devops_tools.utilities.ansible import managed_file_decrypt
from tests.ci.support.ansible import encrypted_file


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
