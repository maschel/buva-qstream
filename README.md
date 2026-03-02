# BUVA Q-Stream

A Python library for controlling Buva Q-Stream devices.

## Installation

Install the package from PyPI:

```bash
pip install buva-qstream
```

## Usage

Here's a basic example of how to use the library:

```python
import asyncio
from aiohttp import ClientSession
from buva_qstream import QstreamAPI, discover

async def main():
    # Discover the device on the network
    device = await discover("192.168.1.255")
    if not device:
        print("No device found")
        return

    async with ClientSession() as session:
        api = QstreamAPI(device, session)

        # Get the actual speed
        actual_speed = await api.actual_speed()
        print(f"Actual speed: {actual_speed}")

        # Set the speed to 50% for 30 minutes
        await api.set_speed(50, 30)

if __name__ == "__main__":
    asyncio.run(main())
```

## API

The `buva-qstream` library provides the following classes:

*   `QstreamDevice`: Represents a Buva Q-Stream device.
*   `QstreamAPI`: Provides methods for controlling the device.

The `discover` function can be used to find devices on the network.

## License

This project is licensed under the GPL-3.0-or-later license.
