# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.deploy_me_entry import flit_entry


class TestFlitEntry:
    def test_clean(self, mocker):
        mock_flow = mocker.patch("foodx_devops_tools.deploy_me_entry.deploy_me")

        flit_entry()

        mock_flow.assert_called_once_with()
