#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import uuid

import pytest

from foodx_devops_tools.puff.arm import _delete_parameter_file, _remove_keys

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
