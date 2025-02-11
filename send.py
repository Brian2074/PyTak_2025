#!/usr/bin/env python3
"""
PyTak_2025 send.py

Usage:
    Run this script to start the PyTak Cursor on Target Event generator.
    It initializes configuration, sets up the serializer tasks,
    and starts the asyncio loop to generate and send CoT events.

Note:
    This script uses asyncio for asynchronous tasks and requires pytak
    library for specialized CoT event handling.
"""

import asyncio
import xml.etree.ElementTree as ET

from configparser import ConfigParser

import pytak


class MySerializer(pytak.QueueWorker):
    """
    Processes or generates Cursor on Target (CoT) events and enqueues them for transmission.
    Inherits from pytak.QueueWorker to leverage asynchronous task management.
    """
    
    async def handle_data(self, data):
        """
        Converts raw data into CoT event and adds it to the transmission queue.
        
        Parameters:
            data: Input data that will be forwarded as a CoT event.
        """
        # Process the incoming data (here, simply forward it)
        event = data
        await self.put_queue(event)  # Enqueue the processed event

    async def run(self):
        """
        Continuously generates takPong events, processes them and enqueues for TX.
        
        This method runs indefinitely and sleeps for 20 seconds between events.
        """
        while True:
            # Generate a new takPong event (simple CoT event)
            data = tak_pong()
            # Process the generated event
            await self.handle_data(data)
            # Wait for 20 seconds before generating the next event
            await asyncio.sleep(20)


def tak_pong():
    """
    Generates a simple takPong Cursor on Target (CoT) Event.
    
    Returns:
        A bytes object containing serialized XML representing the takPong event.
    """
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "t-x-d-d")
    root.set("uid", "takPong")
    root.set("how", "m-g")
    # Set the event times using pytak's helper methods
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(3600))
    return ET.tostring(root)


async def main():
    """
    Main asynchronous entry point of the program.
    
    Actions:
        - Loads or defines configuration parameters.
        - Initializes the pytak CLI tool and its worker tasks.
        - Registers the MySerializer task.
        - Starts the asynchronous loop to process events.
    
    To run the script, execute:
        $ ./send.py
    """
    # Parse or define configuration parameters for pytak
    config = ConfigParser()
    config["mycottool"] = {"COT_URL": "tcp://takserver.example.com:8087"}
    config = config["mycottool"]

    # Initialize the pytak CLI tool which sets up required queues and tasks
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add MySerializer task to the pytak task list for processing events
    clitool.add_tasks(set([MySerializer(clitool.tx_queue, config)]))

    # Start all registered asynchronous tasks
    await clitool.run()


if __name__ == "__main__":
    # Entry point: run the main async function using asyncio's event loop
    asyncio.run(main())