import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        user="postgres.kahflroaztcjnyidxdtx",
        password="Muthu@!!)@07",
        host="aws-1-ap-northeast-2.pooler.supabase.com",
        port=6543,
        database="postgres",
    )
    print("Connected!")
    await conn.close()

asyncio.run(main())