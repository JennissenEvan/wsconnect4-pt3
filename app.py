#!/usr/bin/env python

import asyncio
import websockets
import json
from connect4 import PLAYER1, PLAYER2, Connect4


async def handler(websocket: websockets.WebSocketServerProtocol):
    # Initialize a Connect Four game.
    game = Connect4()

    async for message in websocket:
        event = json.loads(message)

        if event["type"] == "play":
            current_player = PLAYER1 if game.last_player is PLAYER2 else PLAYER2
            column = event["column"]

            try:
                row = game.play(current_player, column)
                out_event = {
                    "type": "play",
                    "player": current_player,
                    "column": column,
                    "row": row
                }
                await websocket.send(json.dumps(out_event))

            except RuntimeError as e:
                out_event = {
                    "type": "error",
                    "message": str(e)
                }
                await websocket.send(json.dumps(out_event))

            if game.last_player_won:
                out_event = {
                    "type": "win",
                    "player": game.last_player
                }
                await websocket.send(json.dumps(out_event))


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
