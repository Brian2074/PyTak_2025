#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
import pytak
from configparser import ConfigParser

# Function to generate a CoT (Cursor-on-Target) event in XML format.
def gen_cot():
    """Generate CoT Event."""
    # Create the root XML element for the event.
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-h-A-M-A")  # Set marker type; customize as needed.
    root.set("uid", "name_your_marker")  # Unique identifier for the marker.
    root.set("how", "m-g")  # Indicates the method the event is generated.
    # Set timestamps using pytak helper (time, start, and stale).
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(60))  # 'stale' is set 60 seconds after start.
    
    # Define Geo-location properties (latitude, longitude, and errors).
    pt_attr = {
        "lat": "40.781789",  # Latitude for Central Park, NY.
        "lon": "-73.968698",  # Longitude for Central Park, NY.
        "hae": "0",           # Height above ellipsoid.
        "ce": "10",           # Circular error.
        "le": "10",           # Linear error.
    }
    # Add the point element as a child of the root.
    ET.SubElement(root, "point", attrib=pt_attr)
    
    # Return the XML string representation of the CoT event.
    return ET.tostring(root)


# Worker class that generates and sends CoT events.
class MySender(pytak.QueueWorker):
    """
    Processes any pre-CoT data by generating CoT events and placing them on the TX queue.
    This example continuously generates an event every 5 seconds.
    """

    async def handle_data(self, data):
        """Queue the serialized CoT event for transmission."""
        await self.put_queue(data)

    async def run(self):
        """Continuously generate and send CoT events."""
        while True:
            data = gen_cot()  # Generate a new CoT event.
            self._logger.info("Sending:\n%s\n", data.decode())
            await self.handle_data(data)
            await asyncio.sleep(5)  # Pause before sending the next event.


# Worker class that receives and processes incoming CoT events.
class MyReceiver(pytak.QueueWorker):
    """
    Handles processing of received CoT events.
    By default, it logs the received event data.
    """

    async def handle_data(self, data):
        """Log the received CoT event."""
        self._logger.info("Received:\n%s\n", data.decode())

    async def run(self):
        """Continuously process events from the RX queue."""
        while True:
            data = await self.queue.get()  # Retrieve the next event from the queue.
            await self.handle_data(data)


async def main():
    """Main entry point for setting up the CoT tool configuration and tasks."""
    # Initialize configuration; update 'COT_URL' as per your TAK server endpoint.
    config = ConfigParser()
    config["mycottool"] = {"COT_URL": "tcp://takserver.example.com:8087"}
    config = config["mycottool"]

    # Set up the CLI tool that manages TX/RX queues.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add sender and receiver workers to the task list.
    clitool.add_tasks(set([
        MySender(clitool.tx_queue, config),
        MyReceiver(clitool.rx_queue, config)
    ]))

    # Begin running all tasks; this call will run indefinitely.
    await clitool.run()


# Entry point: start the asyncio event loop.
if __name__ == "__main__":
    asyncio.run(main())