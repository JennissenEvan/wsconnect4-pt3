#!/usr/bin/env python

import asyncio
import websockets
import json
from connect4 import PLAYER1, PLAYER2, Connect4
import secrets


JOIN = {}

WATCH = {}


async def error(websocket, message):
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))


async def broadcast(connected, event):
    websockets.broadcast(connected, json.dumps(event))


async def play(websocket, game, player, connected):
    async for message in websocket:
        event = json.loads(message)

        if event["type"] == "play":
            if len(connected) < 2:
                await error(websocket, "The other player has not connected yet.")
                continue

            if player is game.last_player:
                await error(websocket, "It's not your turn!")
                continue

            column = event["column"]

            try:
                row = game.play(player, column)
                out_event = {
                    "type": "play",
                    "player": player,
                    "column": column,
                    "row": row
                }
                await broadcast(connected, out_event)

            except RuntimeError as e:
                await error(websocket, str(e))

                continue

            if game.last_player_won:
                out_event = {
                    "type": "win",
                    "player": game.last_player
                }
                await broadcast(connected, out_event)


async def start(websocket):
    # Initialize a Connect Four game, the set of WebSocket connections
    # receiving moves from this game, and secret access token.
    game = Connect4()
    connected = {websocket}

    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    watch_key = secrets.token_urlsafe(12)
    WATCH[watch_key] = game, connected

    try:
        # Send the secret access token to the browser of the first player,
        # where it'll be used for building a "join" link.
        event = {
            "type": "init",
            "join": join_key,
            "watch": watch_key
        }
        await websocket.send(json.dumps(event))

        await play(websocket, game, PLAYER1, connected)

    finally:
        del JOIN[join_key]


async def join(websocket, join_key):
    # Find the Connect Four game.
    try:
        game, connected = JOIN[join_key]
    except KeyError:
        await error(websocket, "Game not found.")
        return

    # Register to receive moves from this game.
    connected.add(websocket)
    try:
        await play(websocket, game, PLAYER2, connected)

    finally:
        connected.remove(websocket)


async def watch(websocket, watch_key):
    watch_info = WATCH.get(watch_key, None)

    if watch_info is None:
        await error(websocket, "Game not found.")
        return

    game, connected = watch_info

    connected.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)


async def handler(websocket):
    # Receive and parse the "init" event from the UI.
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"

    if "join" in event:
        # Second player joins an existing game.
        await join(websocket, event["join"])
    elif "watch" in event:
        await watch(websocket, event["watch"])
    else:
        # First player starts a new game.
        await start(websocket)


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
