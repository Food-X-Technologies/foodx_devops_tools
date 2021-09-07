#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

from foodx_devops_tools.pipeline_config import load_service_principals
from tests.ci.support.ansible import encrypted_file


class TestLoadServicePrincipals:
    mock_encrypted_path = pathlib.Path("some/file")
    mock_password_path = pathlib.Path("other/file")

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
