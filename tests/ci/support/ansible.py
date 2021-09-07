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

from foodx_devops_tools.utilities.ansible import _encrypt_vault


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
