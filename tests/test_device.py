import asyncio.events
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from buva_qstream import qstream_device, QstreamDevice


class TestDevice(IsolatedAsyncioTestCase):

    async def test_retrieves_qstream_device(self) -> None:
        expected_device_info_dict = {'Device': 'QStream', 'FirmwareVersion': '0.7.10', 'IP': '172.26.0.117',
                                     'MAC': 'B4:E6:2D:64:BC:CE'}
        expected_qstream_device = QstreamDevice(expected_device_info_dict)

        with patch.object(asyncio.events.AbstractEventLoop, 'create_datagram_endpoint') as mockie:
            actual = await qstream_device("172.26.0.117")

            print(mockie.called)

            self.assertEqual(expected_qstream_device, actual)
