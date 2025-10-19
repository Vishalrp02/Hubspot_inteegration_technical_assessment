import os

import redis.asyncio as redis
from kombu.utils.url import safequote

redis_host = os.environ.get('REDIS_HOST', '127.0.0.1')
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

async def add_key_value_redis(key, value, expire=None):
    await redis_client.set(key, value,ex=expire)
    # if expire:
    #     await redis_client.expire(key, expire)

async def get_value_redis(key):
    value = await redis_client.get(key)
    if value is not None:
        value = value.decode('utf-8')
    return value

async def delete_key_redis(key):
    await redis_client.delete(key)

