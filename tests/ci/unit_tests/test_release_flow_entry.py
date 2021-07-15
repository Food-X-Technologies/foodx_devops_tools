# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.release_flow_entry import _main

from ..support.capture import capture_stdout_stderr


class TestMain:
    def test_default(self):
        mock_input = ["release_flow", "refs/heads/feature/some/path"]

        with capture_stdout_stderr() as (captured_out, captured_err):
            _main(mock_input)

        captured_out.seek(0)

        assert captured_out.read().strip() == "ftr"
