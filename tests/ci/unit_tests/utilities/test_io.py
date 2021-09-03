#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib
import tempfile

from foodx_devops_tools.utilities.io import acquire_token, load_encrypted_data
from tests.ci.support.ansible import encrypted_file


def test_acquire_token():
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)
        this_file = this_dir / "some.file"
        with this_file.open(mode="w") as f:
            f.write("something")

        with this_file.open("r") as f:
            result = acquire_token(f)

        assert result == "something"


def test_load_encrypted_data():
    file_content = """---
some:
  data: value
"""
    decrypt_token = "somesecret"
    with encrypted_file(file_content, decrypt_token) as (encrypted_file_path):

        result = load_encrypted_data(encrypted_file_path, decrypt_token)

        assert result == {"some": {"data": "value"}}
