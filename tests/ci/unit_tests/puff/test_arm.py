#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import json
import os
import pathlib
import typing
import uuid

import pytest
from ruamel.yaml import YAML

from foodx_devops_tools.puff.arm import (
    ArmTemplateError,
    _delete_parameter_file,
    _do_file_actions,
    _linearize_environments,
    _linearize_name,
    _linearize_regions,
    _linearize_services,
    _remove_keys,
    _save_parameter_file,
    do_arm_template_parameter_action,
    load_yaml,
)
from tests.ci.support.asyncio import mock_context  # noqa: F401


def initialize_filesystem(file_name: pathlib.Path, file_content: str):
    with file_name.open("w") as f:
        f.write(file_content)


class TestLinearizeName:
    MOCK_BASE = {
        "environments": dict(),
        "services": dict(),
    }

    def test_level0_name(self):
        expected_result = {
            "another-name": {
                "environments": dict(),
                "services": dict(),
            },
        }
        mock_file = "some-file"
        mock_input = {
            **self.MOCK_BASE,
            "name": "another-name",
        }

        result = _linearize_name(mock_input, mock_file)

        assert result == expected_result
        assert "name" not in result["another-name"]

    def test_level0_noname(self):
        expected_result = {
            "some-file": {
                "environments": dict(),
                "services": dict(),
            },
        }
        mock_file = "some-file"
        mock_input = self.MOCK_BASE.copy()

        result = _linearize_name(mock_input, mock_file)

        assert result == expected_result
        assert "name" not in result["some-file"]


class TestLinearizedServices:
    def test_services_environments(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
                "services": {
                    "s1": {
                        "p2": "s1p2",
                        "environments": {
                            "e1": {
                                "k1": "s1e1k1",
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "s1p2",
                "environments": {
                    "e1": {
                        "k1": "s1e1k1",
                        "k2": "be1k2",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_multiple_services(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "services": {
                    "s1": {
                        "p2": "s1p2",
                    },
                    "s2": {
                        "p2": "s2p2",
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "s1p2",
            },
            "some-file.s2": {
                "p1": "bp1",
                "p2": "s2p2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_services_environments(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
                "services": {
                    "s1": {
                        "p2": "s1p2",
                        "environments": {
                            "e1": {
                                "k1": "s1e1k1",
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p1": "bp1",
                "p2": "s1p2",
                "environments": {
                    "e1": {
                        "k1": "s1e1k1",
                        "k2": "be1k2",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_empty_services(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
                "services": dict(),
            },
        }
        expected_result = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "environments": {
                    "e1": {
                        "k1": "be1k1",
                        "k2": "be1k2",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_no_services_no_environments(self):
        mock_base = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
                "services": dict(),
            },
        }
        expected_result = {
            "some-file": {
                "p1": "bp1",
                "p2": "bp2",
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_no_services_no_environments_empty_base(self):
        mock_base = {
            "some-file": dict(),
        }
        expected_result = mock_base
        result = _linearize_services(mock_base)

        assert result == expected_result

    def test_services_empty_base(self):
        mock_base = {
            "some-file": {
                "services": {
                    "s1": {
                        "p2": "s1p2",
                        "environments": {
                            "e1": {
                                "k1": "s1e1k1",
                            },
                        },
                    },
                },
            },
        }
        expected_result = {
            "some-file.s1": {
                "p2": "s1p2",
                "environments": {
                    "e1": {
                        "k1": "s1e1k1",
                    },
                },
            },
        }
        result = _linearize_services(mock_base)

        assert result == expected_result


class TestLinearizedEnvironments:
    def test_environments_regions(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                        "regions": [
                            {"r1": {"k1": "e1r1k1"}},
                            {"r2": {"k2": "e1r2k2"}},
                        ],
                    },
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "p1": "bp1",
                "k1": "e1k1",
                "k2": "bk2",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_multiple_stubs_multiple_environments(self):
        mock_base = {
            "stub1": {
                "p1": "stub1.p1",
                "k2": "stub1.k2",
                # "full" environment
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                    },
                    "e2": {
                        "k1": "e2k1",
                    },
                },
            },
        }
        expected_result = {
            "stub1.e1": {
                "p1": "stub1.p1",
                "k1": "e1k1",
                "k2": "stub1.k2",
            },
            "stub1.e2": {
                "p1": "stub1.p1",
                "k1": "e2k1",
                "k2": "stub1.k2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_multiple_stubs_mixed_environments(self):
        mock_base = {
            "stub1": {
                "p1": "stub1.p1",
                "k2": "stub1.k2",
                # "full" environment
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                        "regions": [
                            {"r1": {"k1": "e1r1k1"}},
                            {"r2": {"k2": "e1r2k2"}},
                        ],
                    },
                },
            },
            "stub2": {
                "p1": "stub2.p1",
                "k2": "stub2.k2",
                # empty environment
                "environments": dict(),
            },
        }
        expected_result = {
            "stub1.e1": {
                "p1": "stub1.p1",
                "k1": "e1k1",
                "k2": "stub1.k2",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
            "stub2": {
                "p1": "stub2.p1",
                "k2": "stub2.k2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_empty_environments(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
                "environments": dict(),
            },
        }
        expected_result = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_environments_no_environment_regions(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                    },
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "p1": "bp1",
                "k1": "e1k1",
                "k2": "bk2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_no_environments_no_regions(self):
        mock_base = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        expected_result = {
            "this.stub": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_no_environments_no_regions_empty_base(self):
        mock_base = {
            "this.stub": dict(),
        }
        expected_result = {
            "this.stub": dict(),
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result

    def test_environments_empty_base(self):
        mock_base = {
            "this.stub": {
                "environments": {
                    "e1": {
                        "k1": "e1k1",
                        "regions": [
                            {"r1": {"k1": "e1r1k1"}},
                            {"r2": {"k2": "e1r2k2"}},
                        ],
                    },
                },
            },
        }
        expected_result = {
            "this.stub.e1": {
                "k1": "e1k1",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        result = _linearize_environments(mock_base)

        assert result == expected_result


class TestLinearizedRegions:
    def test_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "k1": "e1r1k1",
            },
            "this.stub.r2": {
                "k1": "bk1",
                "k2": "e1r2k2",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_multiple_stubs_mixed_regions(self):
        mock_base = {
            "stub1": {
                "k1": "stub1.k1",
                # "full" region in a stub
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
            "stub2": {
                "k1": "stub2.k1",
                # empty regions in a stub
                "regions": list(),
            },
        }
        expected_result = {
            "stub1.r1": {
                "k1": "e1r1k1",
            },
            "stub1.r2": {
                "k1": "stub1.k1",
                "k2": "e1r2k2",
            },
            "stub2": {
                "k1": "stub2.k1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_empty_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": list(),
            },
        }
        expected_result = {
            "this.stub": {
                "k1": "bk1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_no_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
            },
        }
        expected_result = {
            "this.stub": {
                "k1": "bk1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_regions_empty_base(self):
        mock_base = {
            "this.stub": {
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "k1": "e1r1k1",
            },
            "this.stub.r2": {
                "k2": "e1r2k2",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_no_regions_empty_base(self):
        mock_base = {
            "this.stub": dict(),
        }
        expected_result = {
            "this.stub": dict(),
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result


class TestRemoveKeys:
    def test_clean(self):
        data = {
            "name": "some name",
            "p1": "v1",
            "p2": 3.14159,
            "environments": dict(),
            "services": dict(),
        }
        pre_copy = data.copy()
        result = _remove_keys(data, ["name", "environments", "services"])

        assert result == {
            "p1": "v1",
            "p2": 3.14159,
        }
        # original data must not be modified
        assert data == pre_copy


class TestSaveParameterFile:
    @pytest.mark.asyncio
    async def test_create_clean(self, tmp_path_factory):
        data = {
            "p1": "v1",
            "p2": "v2",
        }
        content = await self._do_create_test(data, tmp_path_factory)
        assert "p1" in content["parameters"]
        assert "p2" in content["parameters"]
        assert content["parameters"]["p1"]["value"] == "v1"
        assert content["parameters"]["p2"]["value"] == "v2"

    def _check_basic_content(self, this_file: pathlib.Path) -> dict:
        assert this_file.exists()
        with this_file.open("r") as f:
            content = json.load(f)

        assert all(
            [x in content for x in ["$schema", "contentVersion", "parameters"]]
        )
        return content

    async def _do_create_test(
        self,
        parameter_data: typing.Optional[dict],
        path_factory,
        is_pretty: bool = False,
    ) -> dict:
        this_directory = path_factory.mktemp(str(uuid.uuid4()))
        this_file = this_directory / "some_file"
        assert not this_file.exists()

        await _save_parameter_file(this_file, parameter_data, is_pretty)

        return self._check_basic_content(this_file)

    @pytest.mark.asyncio
    async def test_none_parameters(self, tmp_path_factory):
        await self._do_create_test(None, tmp_path_factory)

    @pytest.mark.asyncio
    async def test_empty_parameters(self, tmp_path_factory):
        await self._do_create_test(dict(), tmp_path_factory)

    @pytest.mark.asyncio
    async def test_pretty(self, mock_context, mocker, tmp_path_factory):
        mock_context("foodx_devops_tools.puff.arm.aiofiles.open")
        mock_dump = mocker.patch("foodx_devops_tools.puff.arm.json.dumps")

        this_directory = pathlib.Path("some/path")
        this_file = this_directory / "some_file"

        await _save_parameter_file(this_file, dict(), True)

        mock_dump.assert_called_once_with(mocker.ANY, sort_keys=True, indent=2)

    @pytest.mark.asyncio
    async def test_not_pretty(self, mock_context, mocker, tmp_path_factory):
        mock_context("foodx_devops_tools.puff.arm.aiofiles.open")
        mock_dump = mocker.patch("foodx_devops_tools.puff.arm.json.dumps")

        this_directory = pathlib.Path("some/path")
        this_file = this_directory / "some_file"

        await _save_parameter_file(this_file, dict(), False)

        mock_dump.assert_called_once_with(mocker.ANY)


class TestDeleteParameterFile:
    @pytest.mark.asyncio
    async def test_delete_clean(self, tmp_path_factory):
        this_directory = tmp_path_factory.mktemp(str(uuid.uuid4()))
        this_file = this_directory / "some_file"
        initialize_filesystem(this_file, "some content")

        assert this_file.exists()

        await _delete_parameter_file(this_file)

        assert not this_file.exists()


class TestDoFileActions:
    MOCK_PARAMETER_DATA = {
        "some-file": {
            "k1": "v1",
        }
    }

    @pytest.mark.asyncio
    async def test_delete_clean(self, mocker):
        mock_delete = mocker.patch(
            "foodx_devops_tools.puff.arm._delete_parameter_file"
        )
        mocker.patch("foodx_devops_tools.puff.arm._save_parameter_file")

        await _do_file_actions(
            True, pathlib.Path("some/path"), self.MOCK_PARAMETER_DATA, False
        )

        mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_clean(self, mocker):
        mocker.patch("foodx_devops_tools.puff.arm._delete_parameter_file")
        mock_save = mocker.patch(
            "foodx_devops_tools.puff.arm._save_parameter_file"
        )

        await _do_file_actions(
            False, pathlib.Path("some/path"), self.MOCK_PARAMETER_DATA, False
        )

        mock_save.assert_called_once()


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
