import asyncio, os, json
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient

HERE = Path(__file__).parent
ROOT = HERE.parent
load_dotenv(HERE / ".env")
api_id   = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]
channel  = -1001324653248  # числовой ID из result.json
results  = []

async def check(stem):
    path = ROOT / stem
    try:
        client = TelegramClient(str(path), api_id, api_hash)
        await asyncio.wait_for(client.connect(), timeout=10)
        auth = await client.is_user_authorized()
        row = {"s": stem, "auth": auth}
        if auth:
            me = await client.get_me()
            row["user"] = f"{me.first_name} @{me.username}"
            try:
                ent = await client.get_entity(channel)
                row["ch"] = ent.title
                p = await client.get_permissions(ent, me)
                row["can_delete"] = getattr(p, "delete_messages", "?")
            except Exception as e:
                row["ch_err"] = str(e)
        await client.disconnect()
    except Exception as e:
        row = {"s": stem, "err": str(e)}
    results.append(row)

async def main():
    for stem in ["session", "session2", "session2_finance", "session2_kod_ai"]:
        await check(stem)

asyncio.run(main())
(HERE / "session_check.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("done")
