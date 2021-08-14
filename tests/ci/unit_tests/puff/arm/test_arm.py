#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import uuid

import pytest

from foodx_devops_tools.puff.arm import (
    _delete_parameter_file,
    _merge_default_name,
    _merge_list_of_dict,
    _remove_keys,
)

from .support import initialize_filesystem


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


class TestDeleteParameterFile:
    @pytest.mark.asyncio
    async def test_delete_clean(self, tmp_path_factory):
        this_directory = tmp_path_factory.mktemp(str(uuid.uuid4()))
        this_file = this_directory / "some_file"
        initialize_filesystem(this_file, "some content")

        assert this_file.exists()

        await _delete_parameter_file(this_file)

        assert not this_file.exists()


class TestMergeDefaultName:
    def test_default_present(self):
        mock_base = {
            "some-name": {
                "default": {"name": "name-variable-value"},
                "p1": "p1",
            }
        }
        expected_value = {
            "some-name": {"p1": "p1", "name": "name-variable-value"}
        }

        result = _merge_default_name(mock_base)

        assert result == expected_value

    def test_default_absent(self):
        mock_base = {
            "some-name": {
                "p1": "p1",
            }
        }
        expected_value = {
            "some-name": {
                "p1": "p1",
            }
        }

        result = _merge_default_name(mock_base)

        assert result == expected_value


class TestMergeListOfDict:
    def test_clean(self):
        data = [
            {"r1": {"k1": "e1r1k1"}},
            {"r1": {"k2": "e2r1k2"}},
            {"r1": {"k3": "e3r1k3"}},
            {"r2": {"k4": "e1r2k2"}},
            {"r2": {"k5": "e2r2k3"}},
        ]
        expected_value = {
            "r1": {
                "k1": "e1r1k1",
                "k2": "e2r1k2",
                "k3": "e3r1k3",
            },
            "r2": {
                "k4": "e1r2k2",
                "k5": "e2r2k3",
            },
        }

        result = _merge_list_of_dict(data)

        assert result == expected_value

    def test_none_empty_subsequent_entries(self):
        data = [
            {"r1": {"k1": "e1r1k1"}},
            {"r1": None},
            {"r1": {"k3": "e3r1k3"}},
            {"r2": {"k4": "e1r2k2"}},
            {"r2": dict()},
        ]
        expected_value = {
            "r1": {
                "k1": "e1r1k1",
                "k3": "e3r1k3",
            },
            "r2": {
                "k4": "e1r2k2",
            },
        }

        result = _merge_list_of_dict(data)

        assert result == expected_value

    def test_none_empty_initial_entries(self):
        data = [
            {"r1": None},
            {"r1": {"k2": "e2r1k2"}},
            {"r1": {"k3": "e3r1k3"}},
            {"r2": dict()},
            {"r2": {"k5": "e2r2k3"}},
        ]
        expected_value = {
            "r1": {
                "k2": "e2r1k2",
                "k3": "e3r1k3",
            },
            "r2": {
                "k5": "e2r2k3",
            },
        }

        result = _merge_list_of_dict(data)

        assert result == expected_value

    def test_none_empty_only_entries(self):
        data = [
            {"r1": None},
            {"r2": dict()},
        ]
        expected_value = {
            "r1": dict(),
            "r2": dict(),
        }

        result = _merge_list_of_dict(data)

        assert result == expected_value
