import pytest
from unittest.mock import AsyncMock, MagicMock
from aiohttp import ClientSession

from buva_qstream import QstreamDevice
from buva_qstream.api import QstreamAPI


@pytest.fixture
def mock_device() -> QstreamDevice:
    """Fixture for a mock QstreamDevice."""
    return QstreamDevice(
        {
            "Device": "MockDevice",
            "FirmwareVersion": "1.0",
            "IP": "1.1.1.1",
            "MAC": "aa:bb:cc:dd:ee:ff",
        }
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture for a mocked aiohttp.ClientSession."""
    session = AsyncMock(spec=ClientSession)

    # Mock the response object that get() and post() will return
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()

    session.get = AsyncMock(return_value=mock_response)
    session.post = AsyncMock(return_value=mock_response)

    return session


@pytest.fixture
def api(mock_device: QstreamDevice, mock_session: AsyncMock) -> QstreamAPI:
    """Fixture for a QstreamAPI instance with a mocked session."""
    return QstreamAPI(mock_device, mock_session)


class TestQstreamAPI:
    @pytest.mark.asyncio
    async def test_actual_speed(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "Some Status Qactual 50 Other Info"})

        speed = await api.actual_speed()

        assert speed == "50"
        mock_session.get.assert_called_once_with("http://1.1.1.1/Status")

    @pytest.mark.asyncio
    async def test_selected_speed(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "Some Status Qset 60 Other Info"})

        speed = await api.selected_speed()

        assert speed == "60"
        mock_session.get.assert_called_once_with("http://1.1.1.1/Status")

    @pytest.mark.asyncio
    async def test_nominal_speed(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "70"})

        speed = await api.nominal_speed()

        assert speed == "70"
        mock_session.get.assert_called_once_with("http://1.1.1.1/Qnom")

    @pytest.mark.asyncio
    async def test_air_quality_index(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "42"})

        aqi = await api.air_quality_index()

        assert aqi == 42
        mock_session.get.assert_called_once_with("http://1.1.1.1/AQI")

    @pytest.mark.asyncio
    async def test_is_demand_control_enabled(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "DEMAND CONTROL ON "})
        assert await api.is_demand_control_enabled() is True

        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "DEMAND CONTROL OFF "})
        assert await api.is_demand_control_enabled() is False

    @pytest.mark.asyncio
    async def test_set_demand_control_on(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        await api.set_demand_control_on()

        mock_session.post.assert_called_once_with("http://1.1.1.1/Timer", data='{ "Value": "TIMER 0 MIN" }')

    @pytest.mark.asyncio
    async def test_set_speed(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        await api.set_speed(50, 60)
        mock_session.post.assert_called_once_with(
            "http://1.1.1.1/Timer",
            data='{ "Value": "TIMER 60 MIN 50% DEMAND CONTROL OFF DAY" }',
        )

        mock_session.post.reset_mock()

        await api.set_speed(75, 0)
        mock_session.post.assert_called_once_with(
            "http://1.1.1.1/Timer",
            data='{ "Value": "TIMER CONT 75% DEMAND CONTROL OFF DAY" }',
        )

    @pytest.mark.asyncio
    async def test_retrieve_status_value_not_found(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.json = AsyncMock(return_value={"Value": "Some Status Other Info"})

        with pytest.raises(RuntimeError, match="Qactual field not found in Qstream status."):
            await api._retrieve_status_value("Qactual")

    @pytest.mark.asyncio
    async def test_retrieve_value_error(self, api: QstreamAPI, mock_session: AsyncMock) -> None:
        mock_session.get.return_value.raise_for_status.side_effect = Exception("Boom!")

        with pytest.raises(Exception, match="Boom!"):
            await api._retrieve_value("NonExistentField")
