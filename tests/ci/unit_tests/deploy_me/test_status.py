#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio

import pytest

from foodx_devops_tools.deploy_me._status import (
    DeploymentState,
    DeploymentStatus,
)


@pytest.fixture()
def status_instance():
    def _apply(timeout_seconds: float = 10):
        _status_instance = DeploymentStatus("some.context", timeout_seconds)

        return _status_instance

    return _apply


@pytest.fixture()
def simple_status(status_instance):
    async def _apply(timeout_seconds: float):
        under_test = status_instance(timeout_seconds=timeout_seconds)
        await under_test.initialize("n1")
        await under_test.initialize("n2")

        return under_test

    return _apply


class TestDeploymentStatus:
    @pytest.mark.asyncio
    async def test_clean(self, status_instance):
        under_test = status_instance()
        this_name = "some_name"
        assert not await under_test.names()
        await under_test.initialize(this_name)

        assert await under_test.names() == {this_name}

        await under_test.write(
            this_name,
            DeploymentState.ResultType.pending,
            message="some message",
        )

        result = await under_test.read(this_name)
        assert result.code == DeploymentState.ResultType.pending
        assert result.message == "some message"


class TestCompletedEvent:
    @pytest.mark.asyncio
    async def test_success(self, simple_status):
        under_test = await simple_status(timeout_seconds=5)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n1", DeploymentState.ResultType.success)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.success)

        waiter_task = asyncio.create_task(under_test.wait_for_completion())
        asyncio.create_task(mock_status_updated())

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.in_progress
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.in_progress

        await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.success

    @pytest.mark.asyncio
    async def test_success_fail(self, simple_status):
        under_test = await simple_status(timeout_seconds=5)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n1", DeploymentState.ResultType.success)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.failed)

        waiter_task = asyncio.create_task(under_test.wait_for_completion())
        asyncio.create_task(mock_status_updated())

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.in_progress
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.in_progress

        await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.failed

    @pytest.mark.asyncio
    async def test_in_progress(self, simple_status):
        under_test = await simple_status(timeout_seconds=1)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)

        waiter_task = asyncio.create_task(under_test.wait_for_completion())
        asyncio.create_task(mock_status_updated())

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
        await asyncio.sleep(0.2)
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.in_progress

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.in_progress
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.in_progress

    @pytest.mark.asyncio
    async def test_timeout_raises(self, simple_status):
        under_test = await simple_status(timeout_seconds=0.5)

        async def mock_status_updated():
            # do nothing so that state never transitions to a completed state.
            pass

        waiter_task = asyncio.create_task(under_test.wait_for_completion())
        asyncio.create_task(mock_status_updated())

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending
