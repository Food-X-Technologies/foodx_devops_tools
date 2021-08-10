#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import contextlib
import copy
import json
import pathlib
import typing
import uuid

import pytest

from foodx_devops_tools.puff.arm import _save_parameter_file


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
    async def test_pretty(self, mock_context, mocker):
        mock_context("foodx_devops_tools.puff.arm.aiofiles.open")
        mock_dump = mocker.patch("foodx_devops_tools.puff.arm.json.dumps")

        this_directory = pathlib.Path("some/path")
        this_file = this_directory / "some_file"

        await _save_parameter_file(this_file, dict(), True)

        mock_dump.assert_called_once_with(mocker.ANY, sort_keys=True, indent=2)

    @pytest.mark.asyncio
    async def test_not_pretty(self, mock_context, mocker):
        mock_context("foodx_devops_tools.puff.arm.aiofiles.open")
        mock_dump = mocker.patch("foodx_devops_tools.puff.arm.json.dumps")

        this_directory = pathlib.Path("some/path")
        this_file = this_directory / "some_file"

        await _save_parameter_file(this_file, dict(), False)

        mock_dump.assert_called_once_with(mocker.ANY)


class MockFileStream:
    def __init__(self, target: pathlib.Path, mode: str = "r"):
        self.sleep_intervals = {0.1, 1}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def write(self, stuff: str):
        pass


class TestConcurrentTargets:
    @pytest.mark.asyncio
    async def test_concurrent_save(self, mocker):
        mock_dump = mocker.patch("foodx_devops_tools.puff.arm.json.dumps")
        mocker.patch(
            "foodx_devops_tools.puff.arm.aiofiles.open",
            side_effect=MockFileStream,
        )
        data = [
            {
                "expected": {
                    "$schema": "https://schema.management.azure.com/schemas/2019-04-01"
                    "/deploymentParameters.json#",
                    "contentVersion": "1.0.0.0",
                    "parameters": {"av": 3.14},
                },
                "path": pathlib.Path("a"),
                "parameters": {"av": 3.14},
            },
            {
                "expected": {
                    "$schema": "https://schema.management.azure.com/schemas/2019-04-01"
                    "/deploymentParameters.json#",
                    "contentVersion": "1.0.0.0",
                    "parameters": {"bv": "something"},
                },
                "path": pathlib.Path("b"),
                "parameters": {"bv": "something"},
            },
        ]
        await asyncio.gather(
            *[
                _save_parameter_file(
                    x["path"], copy.deepcopy(x["expected"]["parameters"]), True
                )
                for x in data
            ]
        )

        a = mock_dump.mock_calls[0].args[0]
        b = mock_dump.mock_calls[1].args[0]

        # Ensure that the parameters sub-dict is unique in each concurrent call.
        assert id(a["parameters"]) != id(b["parameters"])
