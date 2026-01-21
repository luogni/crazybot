#!/usr/bin/env python3

import asyncio
from queue import Queue, Empty
import threading


def serial_io(q: Queue[bytes], stop_ev: threading.Event):
    while True:
        if stop_ev.is_set():
            return
        try:
            v = q.get(block=True, timeout=1.0)
            print(v)
        except Empty:
            pass


async def main():
    print("TEST")

    async def _client_cb(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        q: Queue[bytes] = Queue(maxsize=10)
        stop_ev = threading.Event()

        async def _echo():
            while True:
                line = await reader.readline()
                print(line)
                q.put(line)

        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(_echo())
            ser = tg.create_task(asyncio.to_thread(serial_io, q, stop_ev))
            await asyncio.sleep(3)
            stop_ev.set()
            _ = t1.cancel()

    server = await asyncio.start_server(_client_cb, "127.0.0.1", 4567)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
