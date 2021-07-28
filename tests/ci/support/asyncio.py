#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import typing
import unittest.mock

import pytest
from asynctest import CoroutineMock


@pytest.fixture()
def mock_async_method(mocker):
    def _apply(
        path_to_mock: str, return_value: typing.Optional[typing.Any] = None
    ):
        async_mock = unittest.mock.AsyncMock(return_value=return_value)
        this_mock = mocker.patch(path_to_mock, side_effect=async_mock)

        return this_mock

    return _apply


@pytest.fixture()
def mock_context(mocker):
    def _apply(path_to_mock: str):
        this_mock = mocker.patch(path_to_mock)
        this_mock.return_value.__aenter__.return_value.write = CoroutineMock()

        return this_mock

    return _apply
