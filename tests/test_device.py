import asyncio
import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from buva_qstream import QstreamDevice, discover
from buva_qstream.device import _QstreamDiscoverProtocol, _DEVICE_INFO_MESSAGE


class TestDevice:

    @pytest.mark.asyncio
    async def test_qstream_device_success(self) -> None:
        mock_transport = MagicMock(spec=asyncio.BaseTransport)
        mock_future: asyncio.Future[QstreamDevice] = asyncio.Future()
        mock_future.set_result(
            QstreamDevice({"Device": "MockDevice", "FirmwareVersion": "1.0", "IP": "1.1.1.1", "MAC": "aa:bb:cc"})
        )

        with patch("buva_qstream.device._create_device_info_endpoint", return_value=(mock_transport, mock_future)):
            result = await discover("192.168.1.100")
            assert isinstance(result, QstreamDevice)
            assert result.device == "MockDevice"
            mock_transport.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_qstream_device_timeout(self) -> None:
        mock_transport = MagicMock(spec=asyncio.BaseTransport)
        mock_future: asyncio.Future[QstreamDevice] = asyncio.Future()  # Will not be resolved within the timeout

        with patch("buva_qstream.device._create_device_info_endpoint", return_value=(mock_transport, mock_future)):
            result = await discover("192.168.1.100")
            assert result is None
            mock_transport.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_made(self) -> None:
        future: asyncio.Future[QstreamDevice] = asyncio.Future()
        protocol = _QstreamDiscoverProtocol(future)
        mock_transport = MagicMock(spec=asyncio.DatagramTransport)
        protocol.connection_made(mock_transport)
        mock_transport.sendto.assert_called_once_with(_DEVICE_INFO_MESSAGE.encode())

    @pytest.mark.asyncio
    async def test_datagram_received_valid_json(self) -> None:
        future: asyncio.Future[QstreamDevice] = asyncio.Future()
        protocol = _QstreamDiscoverProtocol(future)
        valid_data = json.dumps(
            {
                "Device": "TestDevice",
                "FirmwareVersion": "1.0",
                "IP": "127.0.0.1",
                "MAC": "AA:BB:CC:DD:EE:FF",
            }
        ).encode()
        addr = ("192.168.1.10", 12345)
        protocol.datagram_received(valid_data, addr)
        result = await asyncio.wait_for(future, timeout=0.1)
        assert isinstance(result, QstreamDevice)
        assert result.device == "TestDevice"

    @pytest.mark.asyncio
    async def test_datagram_received_invalid_json(self, caplog: pytest.LogCaptureFixture) -> None:
        future: asyncio.Future[QstreamDevice] = asyncio.Future()
        protocol = _QstreamDiscoverProtocol(future)
        invalid_data = b"not valid json"
        addr = ("192.168.1.20", 54321)
        with caplog.at_level(logging.WARNING):
            protocol.datagram_received(invalid_data, addr)
            assert not future.done()
            assert f"Failed to parse data retrieved from address: {addr[0]}" in caplog.text

    def test_qstream_device_creation(self) -> None:
        device_info = {
            "Device": "MyQstream",
            "FirmwareVersion": "1.0.0",
            "IP": "192.168.1.100",
            "MAC": "00:11:22:33:44:55",
        }
        device = QstreamDevice(device_info)
        assert device.device == "MyQstream"
        assert device.firmware_version == "1.0.0"
        assert device.ip == "192.168.1.100"
        assert device.mac == "00:11:22:33:44:55"

    def test_qstream_device_repr(self) -> None:
        device_info = {
            "Device": "TestDevice",
            "FirmwareVersion": "2.0",
            "IP": "10.0.0.5",
            "MAC": "AA:BB:CC:DD:EE:FF",
        }
        device = QstreamDevice(device_info)
        expected_repr = (
            'QstreamDeviceInfo(device="TestDevice", firmware_version="2.0", ip="10.0.0.5", mac="AA:BB:CC:DD:EE:FF")'
        )
        assert repr(device) == expected_repr

    def test_qstream_device_equality(self) -> None:
        device_info1 = {
            "Device": "DeviceA",
            "FirmwareVersion": "1.1",
            "IP": "192.168.1.1",
            "MAC": "01:02:03:04:05:06",
        }
        device1 = QstreamDevice(device_info1)
        device2 = QstreamDevice(device_info1)
        device_info3 = {
            "Device": "DeviceB",
            "FirmwareVersion": "1.1",
            "IP": "192.168.1.1",
            "MAC": "01:02:03:04:05:06",
        }
        device3 = QstreamDevice(device_info3)
        assert device1 == device2
        assert device1 != device3
        assert device1 != "not a QstreamDevice"
