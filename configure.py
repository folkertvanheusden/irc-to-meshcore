#! /usr/bin/env python3

import asyncio
import time
from meshcore import MeshCore, EventType

async def main():
    #meshcore = await MeshCore.create_tcp("10.208.3.122", 5000)
    #meshcore = await MeshCore.create_tcp("192.168.2.34", 5000)
    meshcore = await MeshCore.create_tcp("192.168.65.96", 5000)
    
    result = await meshcore.commands.set_name('NURDspace')
    if result.type == EventType.ERROR:
        print('failed')
        return
    result = await meshcore.commands.set_radio(869.618, 62.5, 8, 8)
    if result.type == EventType.ERROR:
        print('failed')
        return
    result = await meshcore.commands.set_tx_power(20)
    if result.type == EventType.ERROR:
        print('failed')
        return
    result = await meshcore.commands.set_time(int(time.time()))
    if result.type == EventType.ERROR:
        print('failed')
        return
    result = await meshcore.commands.set_channel(1, '#nurds', None)
    if result.type == EventType.ERROR:
        print('failed')
        return
    result = await meshcore.commands.send_advert()
    if result.type == EventType.ERROR:
        print('failed')
        return

    await meshcore.disconnect()

asyncio.run(main())
