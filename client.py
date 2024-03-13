import asyncio
import websockets




async def test_server():
    async with websockets.connect('ws://emotion-detect.azurewebsites.net:8765') as websocket:
        with open("me-2.png", "rb") as image_file:
            await websocket.send(image_file.read())
        response = await websocket.recv()
        print(response)

asyncio.get_event_loop().run_until_complete(test_server())