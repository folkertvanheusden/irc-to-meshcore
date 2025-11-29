#! /usr/bin/env python3

meshcore_host = '192.168.65.96'  # '10.208.3.122'
meshcore_port = 5000
meshcore_channel_nr = 1  # index, see configure.py
meshcore_channel_name = 'nurds'  # see configure.py
irc_channel = '#nurdsmc'
irc_server = 'irc.oftc.net'
irc_nick = 'nurdcore'
irc_name = 'NURDspace IRC bot'

###

import pydle

import argparse
import asyncio

from meshcore import MeshCore
from meshcore.events import EventType

meshcore = None
q = asyncio.Queue()


class MyOwnBot(pydle.Client):
    async def on_connect(self):
         await self.join(irc_channel)


    async def queue_msg(self, target, source, message):
        global q
        print(target, source, message)
        try:
            await q.put(f'{source} ({target}): {message}')
        except exception as e:
            print(f'on_message: {e}')


    async def on_message(self, target, source, message):
        await self.queue_msg(target, source, message)


    async def on_private_message(self, target, source, message):
        await self.queue_msg(target, source, message)


    async def on_notice(self, target, source, message):
        await self.queue_msg(target, source, message)


ic = MyOwnBot(irc_nick, realname=irc_name)


async def message_callback(event):
    print(f"Received message: {event.payload['text']}")
    print(f"From: {event.payload.get('pubkey_prefix', 'channel')}")
    print(f"Type: {event.payload['type']}")
    print(f"Timestamp: {event.payload['sender_timestamp']}")
    channel = ''
    if event.payload['type'] == 'CHAN':
        channel = (await meshcore.commands.get_channel(event.payload['channel_idx'])).payload['channel_name']
        print(f'CHANNEL: {channel}')
    print(event)

    if meshcore_channel_name.lower() in channel.lower():
        text = event.payload['text']
        parts = text.split()
        if len(parts) >= 2:
            if len(parts[1]) > 1 and parts[1][0] == '!':
                await ic.message(irc_channel, text[text.find(' '):].strip())  # handle by nurdbot
            else:
                await ic.message(irc_channel, 'MeshCore: ' + text)

    print()


async def advertisement_callback(event):
    print(f'Detected advertisement: {event}')


async def capture_irc(conn, msg):
    print(msg)


async def main():
    global meshcore
    meshcore = await MeshCore.create_tcp(meshcore_host, meshcore_port, auto_reconnect=True, max_reconnect_attempts=100000)

    await meshcore.commands.send_advert(flood=True)

    private_subscription = meshcore.subscribe(EventType.CONTACT_MSG_RECV, message_callback)
    channel_subscription = meshcore.subscribe(EventType.CHANNEL_MSG_RECV, message_callback)
    advert_subscription = meshcore.subscribe(EventType.ADVERTISEMENT, advertisement_callback)

    await meshcore.start_auto_message_fetching()

    await ic.connect(irc_server, tls=True, tls_verify=True)

    try:
        while True:
            print('Waiting for message...')
            m = await q.get()
            print(f'Send via meshcore to channel {meshcore_channel_nr}: {m}')
            await meshcore.commands.send_chan_msg(meshcore_channel_nr, m)
    except KeyboardInterrupt:
        meshcore.stop()
        print()
        print('Exiting...')
    except asyncio.CancelledError:
        print()
        print('Task cancelled - cleaning up...')
    finally:
        meshcore.unsubscribe(private_subscription)
        meshcore.unsubscribe(channel_subscription)
        meshcore.unsubscribe(advert_subscription)
        await meshcore.stop_auto_message_fetching()
        await meshcore.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'exception: {e}')
