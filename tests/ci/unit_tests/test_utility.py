#  Copyright (c) 2020 Russell Smiley
#
#  This file is part of build_harness.
#
#  You should have received a copy of the MIT License along with build_harness.
#  If not, see <https://opensource.org/licenses/MIT>.
#
# https://gitlab.com/ci-cd-devops/build_harness/-/blob/main/tests/ci/unit_tests/test_utility.py

from foodx_devops_tools.utility import run_command


class TestRunCommand:
    def test_simple(self, mocker):
        mock_run = mocker.patch("foodx_devops_tools.utility.subprocess.run")
        command = ["something", "--option"]

        result = run_command(command)

        mock_run.assert_called_once_with(command)
        assert result == mock_run.return_value
