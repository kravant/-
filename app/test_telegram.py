import asyncio
import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.telegram.org") as response:
            print(response.status)
            print(await response.text())


asyncio.run(main())
