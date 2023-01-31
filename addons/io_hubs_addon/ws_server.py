import bpy
import asyncio
from .preferences import get_addon_pref
from .utils import isModuleAvailable
from threading import Thread


async def handle_echo(websocket):
    async for message in websocket:
        await websocket.send(message)


global ws_server

# const webSocket = new WebSocket("ws://localhost:8765/");
# webSocket.onmessage = event => {
#   console.log(event.data);
# };
# webSocket.onopen = event => {
#   webSocket.send("Here's some text that the server is urgently awaiting!");
# };


def start_loop(loop, server):
    loop.run_until_complete(server)
    loop.run_forever()


def register():
    viewer_enabled = get_addon_pref(bpy.context).viewer_enabled
    if viewer_enabled and isModuleAvailable("websockets"):
        import websockets
        new_loop = asyncio.new_event_loop()
        start_server = websockets.serve(handle_echo, "localhost", 8765, loop=new_loop)
        ws_server = Thread(target=start_loop, args=(new_loop, start_server))
        ws_server.start()


def unregister():
    viewer_enabled = get_addon_pref(bpy.context).viewer_enabled
    if viewer_enabled and isModuleAvailable("websockets"):
        print("Closing websockets server")
