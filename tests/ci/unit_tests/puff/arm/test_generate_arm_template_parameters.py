#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib
import typing
import uuid

import pytest
from ruamel.yaml import YAML

from foodx_devops_tools.puff.arm import (
    ArmTemplateError,
    do_arm_template_parameter_action,
)

from .support import initialize_filesystem


class TestGenerateArmTemplateParameters:
    @pytest.mark.asyncio
    async def test_file_logging(self, capsys, mocker):
        puff_content = """---
environments:
  e1:
    k1: e1k1
    k2: e1k2
"""
        this_yaml = YAML(typ="safe")
        data = this_yaml.load(puff_content)
        mocker.patch("foodx_devops_tools.puff.arm.load_yaml", return_value=data)
        mocker.patch("foodx_devops_tools.puff.arm._save_parameter_file")
        this_directory = pathlib.Path("some/path")
        puff_path = this_directory / "this_file.yml"

        await do_arm_template_parameter_action(puff_path, False, False)

        out = capsys.readouterr().out

        assert "loading, {0}".format(str(puff_path)) in out

    @pytest.mark.asyncio
    async def test_name_optional(self, mocker):
        puff_content = """---
environments:
  e1:
    k1: e1k1
    k2: e1k2
  e2:
    k1: e2k1
    k2: e2k2
"""
        expected_files = [
            "this_file.e1.json",
            "this_file.e2.json",
        ]
        expected_content = [
            {
                "k1": "e1k1",
                "k2": "e1k2",
            },
            {
                "k1": "e2k1",
                "k2": "e2k2",
            },
        ]

        await self._do_file_test(
            expected_files,
            expected_content,
            puff_content,
            mocker,
        )

    async def _do_file_test(
        self,
        expected_files: typing.List[str],
        expected_values: typing.List[dict],
        puff_content: str,
        this_mocker,
        is_delete_action: bool = False,
    ) -> None:
        this_yaml = YAML(typ="safe")
        data = this_yaml.load(puff_content)
        this_mocker.patch(
            "foodx_devops_tools.puff.arm.load_yaml", return_value=data
        )
        mock_save = this_mocker.patch(
            "foodx_devops_tools.puff.arm._save_parameter_file"
        )
        this_directory = pathlib.Path("some/path")
        puff_path = this_directory / "this_file.yml"

        await do_arm_template_parameter_action(
            puff_path, is_delete_action, False
        )

        expected_paths = [this_directory / x for x in expected_files]

        mock_save.has_calls(
            [
                this_mocker.call(expected_paths[x], expected_values[x])
                for x in range(0, len(expected_paths))
            ]
        )

    @pytest.mark.asyncio
    async def test_environments_regions_clean(self, mocker):
        puff_content = """---
name: some-name
environments:
  e1:
    k1: e1k1
    k2: e1k2
  e2:
    k1: e2k1
    k2: e2k2
    regions:
      - r1:
          k3: e2r1k3
"""
        expected_files = [
            "some-name.e1.json",
            "some-name.e2.r1.json",
        ]
        expected_content = [
            {
                "k1": "e1k1",
                "k2": "e1k2",
            },
            {
                "k1": "e2k1",
                "k2": "e2k2",
                "k3": "e2r1k3",
            },
        ]
        await self._do_file_test(
            expected_files,
            expected_content,
            puff_content,
            mocker,
        )

    @pytest.mark.asyncio
    async def test_services_clean(self, mocker):
        puff_content = """---
name: some-name
services:
  s1:
    k1: s1k1
    k2: s1k2
  s2:
    k1: s2k1
    k2: s2k2
    k3: s2k3
"""
        expected_files = [
            (".".join(["some-name", x, "json"])) for x in ["s1", "s2"]
        ]
        expected_content = [
            {
                "k1": "s1k1",
                "k2": "s1k2",
            },
            {
                "k1": "s2k1",
                "k2": "s2k2",
                "k3": "s2k3",
            },
        ]
        await self._do_file_test(
            expected_files,
            expected_content,
            puff_content,
            mocker,
        )

    @pytest.mark.asyncio
    async def test_environments_clean(self, mocker):
        puff_content = """---
name: some-name
environments:
  e1:
    k1: e1k1
    k2: e1k2
  e2:
    k1: e2k1
    k2: e2k2
    k3: e2k3
"""
        expected_files = [
            (".".join(["some-name", x, "json"])) for x in ["e1", "e2"]
        ]
        expected_content = [
            {
                "k1": "e1k1",
                "k2": "e1k2",
            },
            {
                "k1": "e2k1",
                "k2": "e2k2",
                "k3": "e2k3",
            },
        ]
        await self._do_file_test(
            expected_files,
            expected_content,
            puff_content,
            mocker,
        )

    @pytest.mark.asyncio
    async def test_regions_clean(self, mocker):
        puff_content = """---
name: some-name
environments:
  e1:
    regions:
      - r1:
          k1: e1r1k1
          k2: e1r1k2
      - r2:
          k1: e1r2k1
          k2: e1r2k2
          k3: e1r2k3
"""
        expected_files = [
            (".".join(["some-name", x, "json"])) for x in ["e1.r1", "e1.r2"]
        ]
        expected_content = [
            {
                "k1": "e1r1k1",
                "k2": "e1r1k2",
            },
            {
                "k1": "e1r2k1",
                "k2": "e1r2k2",
                "k3": "e1r2k3",
            },
        ]
        await self._do_file_test(
            expected_files,
            expected_content,
            puff_content,
            mocker,
        )

    @pytest.mark.asyncio
    async def test_all_in_clean(self, mocker):
        puff_content = """---
name: some-name
k1: bk1
k2: bk2
environments:
  e1:
    k3: e1k3
  e2:
    k3: e2k3
    regions:
      - r2:
          k1: e2r2k1
services:
  s1:
    k1: s1k1
    k2: s1k2
    environments:
      e1:
        k5: s1e1k5
        regions:
          - r1:
              k2: s1e1r1k2
              k6: s1e1r1k6
  s2:
    k1: s2k1
    k2: s2k2
    k3: s2k3
"""
        expected_files = [
            (".".join(["some-name", x, "json"]))
            for x in ["s1.e1.r1", "s1.e2.r2", "s2.e1", "s2.e2.r2"]
        ]
        expected_content = [
            {
                "k1": "value1",
                "k2": "s1e1r1k2",
                "k3": "e1k3",
                "k5": "s1e1k5",
                "k6": "s1e1r1k6",
            },
            {
                "k1": "e2r2k1",
                "k2": "bk2",
                "k3": "e2k3",
            },
            {
                "k1": "s2k1",
                "k2": "s2k2",
                "k3": "e1k3",
            },
            {
                "k1": "e2r2k1",
                "k2": "s2k2",
                "k3": "e2k3",
            },
        ]
        await self._do_file_test(
            expected_files,
            expected_content,
            puff_content,
            mocker,
        )

    @pytest.mark.asyncio
    async def test_empty_raises(self, tmp_path_factory):
        puff_content = ""
        this_directory = tmp_path_factory.mktemp(str(uuid.uuid4())).absolute()
        puff_path = this_directory / "this_file.yml"
        initialize_filesystem(puff_path, puff_content)

        with pytest.raises(ArmTemplateError):
            await do_arm_template_parameter_action(puff_path, False, False)

    @pytest.mark.asyncio
    async def test_empty_services_raises(self, tmp_path_factory):
        puff_content = """---
environments:
  e1:
    v: v
services:
"""
        this_directory = tmp_path_factory.mktemp(str(uuid.uuid4())).absolute()
        puff_path = this_directory / "this_file.yml"
        initialize_filesystem(puff_path, puff_content)

        with pytest.raises(ArmTemplateError):
            await do_arm_template_parameter_action(puff_path, False, False)
