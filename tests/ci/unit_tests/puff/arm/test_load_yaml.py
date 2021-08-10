#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import os

import pytest

from foodx_devops_tools.puff.arm import load_yaml


class TestLoadYaml:
    @pytest.mark.asyncio
    async def test_clean(self, tmp_path_factory):
        this_directory = tmp_path_factory.mktemp("tmp")
        this_path = this_directory / "some.file"
        with this_path.open(mode="w") as f:
            f.write(
                """---
some:
- d1
- d2
"""
            )
        result = await load_yaml(this_path)

        assert result == {"some": ["d1", "d2"]}

    @pytest.mark.asyncio
    async def test_empty_yaml_warns(self, caplog, tmp_path_factory):
        this_directory = tmp_path_factory.mktemp("tmp")
        this_path = this_directory / "some.file"
        with this_path.open(mode="w") as f:
            f.write(
                """---
"""
            )

        result = await load_yaml(this_path)

        assert any(["Empty YAML file" in x for x in caplog.messages])

    @pytest.mark.asyncio
    async def test_missing_file_raises(self, caplog, tmp_path_factory):
        this_directory = tmp_path_factory.mktemp("tmp")
        this_path = this_directory / "some.file"

        with pytest.raises(
            FileNotFoundError, match=r"No such file or " r"directory"
        ):
            await load_yaml(this_path)

        assert any(["File not found" in x for x in caplog.messages])

    @pytest.mark.asyncio
    async def test_directory_raises(self, caplog, tmp_path_factory):
        """Path pointing to a directory raises an exception."""
        this_directory = tmp_path_factory.mktemp("tmp")
        this_path = this_directory / "some.dir"
        os.makedirs(this_path, exist_ok=True)

        with pytest.raises(IsADirectoryError, match=r"Is a directory"):
            await load_yaml(this_path)

        assert any(["Path is a directory" in x for x in caplog.messages])

    @pytest.mark.asyncio
    async def test_unexpected_logs(self, caplog, mocker, tmp_path_factory):
        """Unexpected error logs a report."""
        this_directory = tmp_path_factory.mktemp("tmp")
        mocker.patch(
            "foodx_devops_tools.puff.arm.ruamel.yaml.YAML",
            side_effect=RuntimeError("some error"),
        )
        this_path = this_directory / "some.dir"
        os.makedirs(this_path, exist_ok=True)

        with pytest.raises(RuntimeError, match=r"^some error"):
            await load_yaml(this_path)

        assert any(["Unexpected error with path" in x for x in caplog.messages])
