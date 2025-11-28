#! /usr/bin/env python3

meshcore_host = '192.168.65.96'  # '10.208.3.122'
meshcore_port = 5000
meshcore_channel_nr = 1  # index, see configure.py
meshcore_channel_name = 'nurds'  # see configure.py
mqtt_server = 'mqtt.vm.nurd.space'
mqtt_topic_publish = 'GHBot/to/irc/nurdsmc/notice'
mqtt_topic_receive = 'GHBot/from/irc/nurdsmc/+/message'

###

import aiomqtt
import argparse
import asyncio

from meshcore import MeshCore
from meshcore.events import EventType


meshcore = None
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
        async with aiomqtt.Client(mqtt_server) as client:
            text = event.payload['text']
            parts = text.split()
            if len(parts) >= 2:
                if len(parts[1]) > 1 and parts[1][0] == '!':
                    await client.publish(mqtt_topic_publish, payload=text[text.find(' '):].strip())  # handle by bot
                else:
                    await client.publish(mqtt_topic_publish, payload='MeshCore: ' + text)

    await meshcore.commands.send_advert(flood=True)
    print()


async def advertisement_callback(event):
    print(f'Detected advertisement: {event}')


async def mqtt_handler():
    async with aiomqtt.Client(mqtt_server) as client:
        await client.subscribe(mqtt_topic_receive)
        async for message in client.messages:
            print(f'mqtt: {message.payload} to {meshcore_channel_nr}')
            try:
                await meshcore.commands.send_chan_msg(meshcore_channel_nr, message.payload.decode('ascii'))
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f'mqtt_handler: {e}')


async def main():
    global meshcore
    meshcore = await MeshCore.create_tcp(meshcore_host, meshcore_port, auto_reconnect=True, max_reconnect_attempts=100000)

    await meshcore.commands.send_advert(flood=True)

    private_subscription = meshcore.subscribe(EventType.CONTACT_MSG_RECV, message_callback)
    channel_subscription = meshcore.subscribe(EventType.CHANNEL_MSG_RECV, message_callback)
    advert_subscription = meshcore.subscribe(EventType.ADVERTISEMENT, advertisement_callback)

    await meshcore.start_auto_message_fetching()

    try:
        await mqtt_handler()
    except KeyboardInterrupt:
        meshcore.stop()
        print()
        print('Exiting...')
    except asyncio.CancelledError:
        # Handle task cancellation from KeyboardInterrupt in asyncio.run()
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
