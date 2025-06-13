# Updated consumer to process orders from RabbitMQ
import asyncio
import json
import logging
import os

import aio_pika
from pydantic import ValidationError

from src import core
from src.app import services, schemas, models

RABBITMQ_URL = "amqp://guest:guest@127.0.0.1/"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_order(uow: core.UnitOfWork, order_data: dict):
    orders_service = services.Orders()
    try:
        # Convert to proper types
        order_data["order_type"] = models.OrderType(order_data["order_type"])
        order_data["direction"] = models.OrderDirection(order_data["direction"])

        # Validate and convert to schema
        order = schemas.orders.Read.model_validate(order_data)

        # Process order
        handler = orders_service.order_handlers.get((order.order_type, order.direction))
        if not handler:
            logger.error(f"No handler for order type {order.order_type} direction {order.direction}")
            return

        await handler(uow, order)
        logger.info(f"Processed order {order.id} successfully")

    except ValidationError as e:
        logger.error(f"Order validation error: {e}")
    except Exception as e:
        logger.exception(f"Error processing order: {e}")

async def message_handler(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            body = json.loads(message.body.decode())
            async with core.UnitOfWork(use_postgres=True) as uow:
                await process_order(uow, body)
        except json.JSONDecodeError as e:
            logger.exception("JSON decode error")
        except Exception:
            logger.exception("Unexpected error")

async def main(loop):
    connection = await aio_pika.connect_robust(RABBITMQ_URL, loop=loop)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("order_processing", durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await message_handler(message)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
