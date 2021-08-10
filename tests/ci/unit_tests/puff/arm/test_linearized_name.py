#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.puff.arm import _linearize_name


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
