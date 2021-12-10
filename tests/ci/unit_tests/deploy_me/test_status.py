#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import logging

import pytest

logging.basicConfig(level=logging.DEBUG)

from foodx_devops_tools.deploy_me._status import (
    DeploymentState,
    DeploymentStatus,
    all_completed,
    all_success,
    any_completed_dirty,
)

TIMEOUT_SECONDS = 10


class TestAllSuccess:
    def test_clean(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.success),
        ]
        result = all_success(mock_input)
        assert result

    def test_not_clean1(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.failed),
        ]
        result = all_success(mock_input)
        assert not result

    def test_not_clean2(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.cancelled),
        ]
        result = all_success(mock_input)
        assert not result

    def test_not_clean3(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.pending),
        ]
        result = all_success(mock_input)
        assert not result

    def test_not_clean4(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.in_progress),
        ]
        result = all_success(mock_input)
        assert not result


class TestAllCompleted:
    def test_clean1(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.failed),
            DeploymentState(DeploymentState.ResultType.cancelled),
        ]
        result = all_completed(mock_input)
        assert result

    def test_clean2(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.success),
        ]
        result = all_completed(mock_input)
        assert result

    def test_clean3(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.failed),
            DeploymentState(DeploymentState.ResultType.failed),
            DeploymentState(DeploymentState.ResultType.failed),
        ]
        result = all_completed(mock_input)
        assert result

    def test_clean4(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.cancelled),
            DeploymentState(DeploymentState.ResultType.cancelled),
            DeploymentState(DeploymentState.ResultType.cancelled),
        ]
        result = all_completed(mock_input)
        assert result

    def test_not_clean1(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.in_progress),
        ]
        result = all_completed(mock_input)
        assert not result

    def test_not_clean2(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.pending),
        ]
        result = all_completed(mock_input)
        assert not result


class TestAnyCompletedDirty:
    def test_clean1(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.failed),
        ]
        result = any_completed_dirty(mock_input)
        assert result

    def test_clean2(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.cancelled),
        ]
        result = any_completed_dirty(mock_input)
        assert result

    def test_in_progress(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.failed),
            DeploymentState(DeploymentState.ResultType.in_progress),
        ]
        result = any_completed_dirty(mock_input)
        assert result

    def test_pending(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.cancelled),
            DeploymentState(DeploymentState.ResultType.pending),
        ]
        result = any_completed_dirty(mock_input)
        assert result

    def test_all_success(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.success),
        ]
        result = any_completed_dirty(mock_input)
        assert not result

    def test_in_progress(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.in_progress),
        ]
        result = any_completed_dirty(mock_input)
        assert not result

    def test_pending(self):
        mock_input = [
            DeploymentState(DeploymentState.ResultType.success),
            DeploymentState(DeploymentState.ResultType.pending),
        ]
        result = any_completed_dirty(mock_input)
        assert not result


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

        under_test.start_monitor()

        return under_test

    return _apply


class TestDeploymentStatus:
    @pytest.mark.asyncio
    async def test_clean(self, status_instance):
        under_test = status_instance()
        this_name = "some_name"

        try:
            assert not await under_test.names()
            await asyncio.wait_for(
                under_test.initialize(this_name), timeout=TIMEOUT_SECONDS
            )
            under_test.start_monitor()

            assert await asyncio.wait_for(
                under_test.names(), timeout=TIMEOUT_SECONDS
            ) == {this_name}

            await under_test.write(
                this_name,
                DeploymentState.ResultType.pending,
                message="some message",
            )

            # pause slightly to enable queue to be processed
            await asyncio.sleep(0.1)

            result = await asyncio.wait_for(
                under_test.read(this_name), timeout=TIMEOUT_SECONDS
            )

            assert result.code == DeploymentState.ResultType.pending
            assert result.message == "some message"
        except asyncio.TimeoutError:
            pytest.fail("status test timed out")


class TestAllCompletedEvent:
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

        waiter_task = asyncio.create_task(under_test.wait_for_all_completed())
        # schedule the status changes to be detected
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
        under_test = await simple_status(timeout_seconds=2)

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

        waiter_task = asyncio.create_task(under_test.wait_for_all_completed())
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
    async def test_success_cancelled(self, simple_status):
        under_test = await simple_status(timeout_seconds=2)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n1", DeploymentState.ResultType.success)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.cancelled)

        waiter_task = asyncio.create_task(under_test.wait_for_all_completed())
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
        ).code == DeploymentState.ResultType.cancelled

    @pytest.mark.asyncio
    async def test_in_progress(self, simple_status):
        under_test = await simple_status(timeout_seconds=1)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)

        waiter_task = asyncio.create_task(under_test.wait_for_all_completed())
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

        waiter_task = asyncio.create_task(under_test.wait_for_all_completed())
        asyncio.create_task(mock_status_updated())

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending

    @pytest.mark.asyncio
    async def test_prior_success(self, simple_status):
        """completion already flagged on entry is clean."""
        under_test = await simple_status(timeout_seconds=5)

        # both these deployments have completed (failed, cancelled)
        await under_test.write("n1", DeploymentState.ResultType.failed)
        await under_test.write("n2", DeploymentState.ResultType.cancelled)

        # need an await here to allow other tasks to execute (especially
        # processing the queue)
        await asyncio.sleep(0.01)

        waiter_task = asyncio.create_task(under_test.wait_for_all_completed())

        # status should now consistently read as those states
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.failed
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.cancelled

        await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.failed
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.cancelled


class TestAllSucceededEvent:
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

        waiter_task = asyncio.create_task(under_test.wait_for_all_succeeded())
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
        under_test = await simple_status(timeout_seconds=2)

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

        waiter_task = asyncio.create_task(under_test.wait_for_all_succeeded())
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

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.failed

    @pytest.mark.asyncio
    async def test_success_cancelled(self, simple_status):
        under_test = await simple_status(timeout_seconds=2)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n1", DeploymentState.ResultType.success)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.cancelled)

        waiter_task = asyncio.create_task(under_test.wait_for_all_succeeded())
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

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.cancelled

    @pytest.mark.asyncio
    async def test_in_progress(self, simple_status):
        under_test = await simple_status(timeout_seconds=1)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.in_progress)

        waiter_task = asyncio.create_task(under_test.wait_for_all_succeeded())
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

        waiter_task = asyncio.create_task(under_test.wait_for_all_succeeded())
        asyncio.create_task(mock_status_updated())

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending

    @pytest.mark.asyncio
    async def test_prior_success(self, simple_status):
        """success already flagged on entry is clean."""
        under_test = await simple_status(timeout_seconds=5)

        await under_test.write("n1", DeploymentState.ResultType.success)
        await under_test.write("n2", DeploymentState.ResultType.success)

        # need an await here to allow other tasks to execute (especially
        # processing the queue)
        await asyncio.sleep(0.01)
        waiter_task = asyncio.create_task(under_test.wait_for_all_succeeded())

        # the status will show as the initial state until the queue of state
        # updates is cleared.
        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.success

        await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.success
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.success


class TestCompletedNamedEvent:
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
            await under_test.write("n1", DeploymentState.ResultType.failed)
            await asyncio.sleep(0.2)
            await under_test.write("n2", DeploymentState.ResultType.success)

        waiter_task = asyncio.create_task(under_test.wait_for_completion("n2"))
        asyncio.create_task(mock_status_updated())

        assert (
            await under_test.read("n2")
        ).code != DeploymentState.ResultType.success

        await waiter_task

        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.success

    @pytest.mark.asyncio
    async def test_success_fail(self, simple_status):
        under_test = await simple_status(timeout_seconds=2)

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

        waiter_task = asyncio.create_task(under_test.wait_for_completion("n2"))
        asyncio.create_task(mock_status_updated())

        assert (
            await under_test.read("n2")
        ).code != DeploymentState.ResultType.failed

        await waiter_task

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

        waiter_task = asyncio.create_task(under_test.wait_for_completion("n2"))
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

        waiter_task = asyncio.create_task(under_test.wait_for_completion("n2"))
        asyncio.create_task(mock_status_updated())

        with pytest.raises(asyncio.TimeoutError):
            await waiter_task

        assert (
            await under_test.read("n1")
        ).code == DeploymentState.ResultType.pending
        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.pending

    @pytest.mark.asyncio
    async def test_prior_success(self, simple_status):
        """success already flagged on entry is clean."""
        under_test = await simple_status(timeout_seconds=5)

        async def mock_status_updated():
            nonlocal under_test

            await asyncio.sleep(0.1)
            await under_test.write("n1", DeploymentState.ResultType.in_progress)
            await asyncio.sleep(0.2)
            await under_test.write("n1", DeploymentState.ResultType.failed)

        await under_test.write("n2", DeploymentState.ResultType.success)

        # need an await here to allow other tasks to execute (especially
        # processing the queue)
        await asyncio.sleep(0.01)

        waiter_task = asyncio.create_task(under_test.wait_for_completion("n2"))
        asyncio.create_task(mock_status_updated())

        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.success

        await waiter_task

        assert (
            await under_test.read("n2")
        ).code == DeploymentState.ResultType.success
