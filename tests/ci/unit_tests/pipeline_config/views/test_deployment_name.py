#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy


def test_clean(mock_flattened_deployment):
    under_test = copy.deepcopy(mock_flattened_deployment[0])
    under_test.context.application_name = "app_name"
    under_test.context.frame_name = "f1"
    under_test.context.pipeline_id = "12345678.24"

    result = under_test.construct_deployment_name("stepname")

    assert result == "app-name_stepname_12345678.24"


def test_plus(mock_flattened_deployment):
    under_test = copy.deepcopy(mock_flattened_deployment[0])
    under_test.context.application_name = "app_name"
    under_test.context.frame_name = "f1"
    under_test.context.pipeline_id = "12345678+24"

    result = under_test.construct_deployment_name("stepname")

    assert result == "app-name_stepname_12345678-24"


def test_underscore(mock_flattened_deployment):
    under_test = copy.deepcopy(mock_flattened_deployment[0])
    under_test.context.application_name = "app_name"
    under_test.context.frame_name = "f1"
    under_test.context.pipeline_id = "12345678_24"

    result = under_test.construct_deployment_name("stepname")

    assert result == "app-name_stepname_12345678-24"
