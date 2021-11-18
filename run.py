import asyncio
import os
from arkitekt.messages.postman.assign.assign_return import AssignReturnMessage
from arkitekt.messages.postman.unprovide.bounced_unprovide import (
    BouncedUnprovideMessage,
)
from arkitekt.messages.types import BOUNCED_FORWARDED_ASSIGN
from pydantic.main import BaseModel
import websockets
from arkitekt.messages import (
    ProvideTransitionMessage,
    BouncedForwardedAssignMessage,
    BouncedForwardedUnassignMessage,
)
from arkitekt.messages.utils import expandToMessage
import json
import logging
from websockets.exceptions import ConnectionClosedError
from arkitekt.messages.postman.provide.provide_transition import (
    ProvideMode,
    ProvideState,
)

logger = logging.getLogger(__name__)

HERMANUS_HOST = os.getenv("HERMANUS_HOST", "hermanus")
HERMANUS_PORT = os.getenv("HERMANUS_PORT", 7676)
BOUNCED_PROVIDE = os.getenv("BOUNCED_PROVIDE", "fake")


class ConnectionFailedError(Exception):
    pass


class CorrectableConnectionFail(ConnectionFailedError):
    pass


class DefiniteConnectionFail(ConnectionFailedError):
    pass


class PortActor:
    def __init__(self, broadcast) -> None:
        self.send_queue = None
        self._broadcast = broadcast
        self.retries = 5
        self.time_between_retries = 5
        self.connection_alive = False
        self.connection_dead = False

        self.assignments = {}

    async def broadcast(message):
        print(message)

    async def forward(self, message: BaseModel):
        await self.send_queue.put(json.dumps(message.dict()))

    async def handle_assign(self, args, kwargs, assign):
        print(f"Assigning {args}")

        await asyncio.sleep(2)

        await self.forward(
            AssignReturnMessage(
                data={
                    "returns": []  # We are not shrinking the outputs as they are already shrinked
                },
                meta={
                    "reference": assign.meta.reference,
                    "extensions": assign.meta.extensions,
                },
            )
        )

        return

    async def sending(self, client):
        try:
            while True:
                message = await self.send_queue.get()
                logger.debug("Port Websocket: >>>>>> " + message)
                await client.send(message)
                self.send_queue.task_done()
        except asyncio.CancelledError as e:
            logger.debug("Sending Task sucessfully Cancelled")

    async def receiving(self, client):
        try:
            async for message in client:
                logger.debug("Port Websocket: <<<<<<< " + message)
                message = expandToMessage(json.loads(message))
                await self.broadcast(message)
        except asyncio.CancelledError as e:
            logger.debug("Receiving Task sucessfully Cancelled")

    async def aprovide(self):
        self.send_queue = asyncio.Queue()
        await self.websocket_loop()

    async def on_provide(self):
        return None

    async def websocket_loop(self, retry=0):
        socket_url = f"ws://{HERMANUS_HOST}:{HERMANUS_PORT}"
        print(socket_url)
        try:
            try:
                async with websockets.connect(socket_url) as client:
                    await client.send(BOUNCED_PROVIDE)

                    self.provision = expandToMessage(json.loads(BOUNCED_PROVIDE))

                    await self.forward(
                        ProvideTransitionMessage(
                            data={
                                "state": ProvideState.PROVIDING,
                                "message": "We just got started Bay",
                            },
                            meta={
                                "reference": self.provision.meta.reference,
                                "extensions": self.provision.meta.extensions,
                            },
                        )
                    )

                    await self.on_provide()

                    await self.forward(
                        ProvideTransitionMessage(
                            data={
                                "state": ProvideState.ACTIVE,
                                "message": "We just got started Bay",
                                "mode": ProvideMode.PRODUCTION,
                            },
                            meta={
                                "reference": self.provision.meta.reference,
                                "extensions": self.provision.meta.extensions,
                            },
                        )
                    )

                    send_task = asyncio.create_task(self.sending(client))

                    async for message in client:
                        logger.debug("Port Websocket: <<<<<<< " + message)
                        message = expandToMessage(json.loads(message))

                        if isinstance(message, BouncedForwardedAssignMessage):
                            print(message)

                            self.assignments[
                                message.meta.reference
                            ] = asyncio.create_task(
                                self.assign(
                                    message.data.args, message.data.kwargs, message
                                )
                            )

                            print("Assignment Done")

                        if isinstance(message, BouncedUnprovideMessage):
                            print("Received Unprovide we are saying goodbye")
                            # TODO: Cancell alll tasks
                            break

            except ConnectionClosedError as e:
                logger.exception(e)
                raise CorrectableConnectionFail from e

            except Exception as e:
                logger.warning(
                    "THIS EXCEPTION HAS NO RETRY STRATEGY... TRYING TO RETRY??"
                )
                raise CorrectableConnectionFail from e

        except CorrectableConnectionFail as e:
            logger.info(f"Trying to Recover from Exception {e}")
            if retry > self.retries:
                raise DefiniteConnectionFail("Exceeded Number of Retries")
            await asyncio.sleep(self.time_between_retries)
            logger.info(f"Retrying to connect")
            await self.websocket_loop(retry=retry + 1)

        except DefiniteConnectionFail as e:
            self.connection_dead = False
            raise e

    async def adisconnect(self):
        logger.info(f"Websocket Transport {self} succesfully disconnected")


async def main():
    socket_url = f"ws://{HERMANUS_HOST}:{HERMANUS_PORT}"
    print(socket_url)

    async def broadcast(message):
        print(message)

    port = PortActor(broadcast=broadcast)
    await port.aprovide()


asyncio.run(main())
