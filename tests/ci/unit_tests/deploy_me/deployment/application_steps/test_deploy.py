#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.deploy_me.application_steps._deploy import (
    _construct_resource_group_name,
)


class TestConstructResourceGroupName:
    def test_clean_user_precedence(self):
        result = _construct_resource_group_name("client", "some_name")

        assert result == "client-some_name"
