#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import os
import pathlib
import tempfile
import typing

from foodx_devops_tools.pipeline_config import load_static_secrets
from foodx_devops_tools.utilities.ansible import _encrypt_vault


@contextlib.contextmanager
def encrypted_files(
    content: typing.Dict[str, str], password: str
) -> typing.Generator[typing.List[pathlib.Path], None, None]:
    with tempfile.TemporaryDirectory() as dir:
        dir_path = pathlib.Path(dir)
        encrypted_file_paths = set()
        for file_name, file_content in content.items():
            this_file = dir_path / file_name

            password_file_path = dir_path / "password-file"
            with password_file_path.open("w") as f:
                f.write(password)

            unencrypted_file_path = dir_path / "plain.file"
            with unencrypted_file_path.open("w") as f:
                f.write(file_content)

            _encrypt_vault(this_file, password_file_path, unencrypted_file_path)

            os.remove(unencrypted_file_path)
            os.remove(password_file_path)

            assert this_file.is_file()
            with this_file.open("r") as f:
                encrypted_content = f.read()

            assert encrypted_content.startswith("$ANSIBLE_VAULT;1.1;AES256")

            encrypted_file_paths.add(this_file)

        yield encrypted_file_paths


def test_load():
    file_text = {
        "f1": """---
static_secrets:
  s1:
    s1k1: s1k1v
    s1k2: s1k2v
  s2:
    s2k1: s2k1v
""",
        "f2": """---
static_secrets:
  s3:
    s3k1: s3k1v
""",
    }
    decrypt_token = "somesecret"
    with encrypted_files(file_text, decrypt_token) as encrypted_dir_paths:
        result = load_static_secrets(encrypted_dir_paths, decrypt_token)

    assert len(result.static_secrets) == 3
    assert result.static_secrets == {
        "s1": {
            "s1k1": "s1k1v",
            "s1k2": "s1k2v",
        },
        "s2": {"s2k1": "s2k1v"},
        "s3": {"s3k1": "s3k1v"},
    }
