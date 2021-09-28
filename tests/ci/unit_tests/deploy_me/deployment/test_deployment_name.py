#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy

from foodx_devops_tools.deploy_me._deployment import _construct_deployment_name


def test_clean(mock_deploystep_context):
    mock_data = copy.deepcopy(mock_deploystep_context["deployment_data"])
    mock_data.context.pipeline_id = "12345678.24"

    result = _construct_deployment_name(mock_data, "stepname")

    assert result == "app-name_stepname_12345678.24"


def test_plus(mock_deploystep_context):
    mock_data = copy.deepcopy(mock_deploystep_context["deployment_data"])
    mock_data.context.pipeline_id = "12345678+24"

    result = _construct_deployment_name(mock_data, "stepname")

    assert result == "app-name_stepname_12345678-24"


def test_underscore(mock_deploystep_context):
    mock_data = copy.deepcopy(mock_deploystep_context["deployment_data"])
    mock_data.context.pipeline_id = "12345678_24"

    result = _construct_deployment_name(mock_data, "stepname")

    assert result == "app-name_stepname_12345678-24"
