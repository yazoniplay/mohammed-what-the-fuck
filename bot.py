import os, asyncio, traceback
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web

from database import init_db, save_listing, get_listing, update_listing, get_all_listings
from gemini_service import analyze_images, regenerate_description
from reseller_features import listing_quality, generate_tags, photo_quality, recommend_price
from ai_brain import seller_report


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", "8"))


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

if not os.getenv("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY is missing")


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


async def start_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="running"))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()


def vinted_text(x):
    return (
        f"{x.get('title', 'Okänt')}\n\n"
        f"{x.get('description', '')}\n\n"
        f"Pris: {x.get('suggested_price_sek', '')} kr\n"
        f"Rekommenderat pris: {x.get('recommended_price', '')} kr\n"
        f"Taggar: {', '.join(x.get('tags', []))}"
    )


@bot.event
async def on_ready():
    init_db()
    print(f"Logged in as {bot.user}")
    print("Bot ready")


@bot.event
async def on_message(message):

    if message.author.bot:
        return


    imgs = []

    for attachment in message.attachments[:MAX_IMAGES]:

        filename = attachment.filename.lower()

        is_image = (
            (attachment.content_type and attachment.content_type.startswith("image/"))
            or filename.endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp",
                    ".gif"
                )
            )
        )


        if not is_image:
            continue


        try:
            image_bytes = await attachment.read()


            if not image_bytes:
                print(
                    f"Empty image received: {attachment.filename}"
                )
                continue


            mime = attachment.content_type or "image/jpeg"

            imgs.append(
                (
                    image_bytes,
                    mime
                )
            )


            print(
                f"Loaded image: {attachment.filename} "
                f"{len(image_bytes)} bytes "
                f"{mime}"
            )


        except Exception:
            print(
                f"Failed reading image {attachment.filename}"
            )
            traceback.print_exc()



    if imgs:

        m = await message.reply(
            "🤖 Analyserar..."
        )


        try:

            print(
                f"Sending {len(imgs)} images to Gemini"
            )


            data = await analyze_images(imgs)


            if not isinstance(data, dict):
                raise Exception(
                    "Gemini returned invalid data"
                )


            data.setdefault(
                "status",
                "draft"
            )

            data.setdefault(
                "buy_price",
                0
            )

            data.setdefault(
                "sell_price",
                0
            )

            data.setdefault(
                "profit",
                0
            )


            data["tags"] = generate_tags(data)

            data["recommended_price"] = recommend_price(data)


            quality = listing_quality(data)

            photos = photo_quality(imgs)


            data["quality_score"] = quality["score"]
            data["quality_missing"] = quality["missing"]

            data["photo_score"] = photos["score"]
            data["photo_issues"] = photos["issues"]


            data["created_at"] = datetime.now().isoformat()


            lid = save_listing(data)


            await m.edit(
                content=(
                    f"✅ Listing #{lid}\n"
                    f"⭐ Quality: {quality['score']}/100\n"
                    f"📸 Photo score: {photos['score']}/100\n"
                    f"💰 Recommended price: {data['recommended_price']}kr\n"
                    f"🔧 Improve: {', '.join(quality['missing']) or 'Ready'}\n\n"
                    f"{vinted_text(data)}"
                )
            )


        except Exception as e:

            print("IMAGE PROCESSING ERROR")
            traceback.print_exc()


            await m.edit(
                content=(
                    f"❌ Error: {type(e).__name__}\n"
                    f"{e}"
                )
            )


    await bot.process_commands(message)



@bot.command()
async def brain(ctx):

    report = seller_report(
        get_all_listings()
    )

    await ctx.send(
        f"🧠 AI Seller Brain\n\n"
        f"Sold items: {report['sold_count']}\n"
        f"Best brand: {report['best_brand']}\n"
        f"Average profit: {report['average_profit']}kr\n\n"
        f"💡 {report['recommendation']}"
    )



@bot.command()
async def inventory(ctx):

    items = get_all_listings()

    await ctx.send(
        "\n".join(
            [
                f"#{i['id']} {i.get('title','')} | {i.get('status','draft')} | {i.get('profit',0)}kr"
                for i in items[:15]
            ]
        )
        or "📦 Empty"
    )



@bot.command()
async def stale(ctx):

    items = get_all_listings()

    old = []

    for i in items:

        created = i.get("created_at")

        if created:

            try:

                days = (
                    datetime.now()
                    -
                    datetime.fromisoformat(created)
                ).days


                if days >= 14 and i.get("status") != "sold":

                    old.append(
                        f"#{i['id']} {i.get('title','')} - {days} dagar"
                    )


            except:
                pass


    await ctx.send(
        "⚠️ Stale listings:\n"
        +
        "\n".join(old)
        if old
        else
        "✅ No stale listings"
    )



@bot.command()
async def sold(ctx, id:int, price:float):

    item = get_listing(id)

    if not item:
        return await ctx.send(
            "❌ Listing not found"
        )


    item["status"] = "sold"
    item["sell_price"] = price
    item["profit"] = price - float(item.get("buy_price",0))

    update_listing(
        id,
        item
    )


    await ctx.send(
        f"✅ Sold #{id}\nProfit: {item['profit']}kr"
    )



@bot.command()
async def listing(ctx,id:int):

    item = get_listing(id)

    await ctx.send(
        vinted_text(item)
        if item
        else
        "❌ Listing not found"
    )



@bot.command()
async def dashboard(ctx):

    items = get_all_listings()

    sold = [
        i for i in items
        if i.get("status") == "sold"
    ]


    await ctx.send(
        f"📊 Reseller Dashboard\n\n"
        f"Items: {len(items)}\n"
        f"Sold: {len(sold)}\n"
        f"Revenue: {sum(float(i.get('sell_price',0)) for i in sold)}kr\n"
        f"Profit: {sum(float(i.get('profit',0)) for i in sold)}kr"
    )



@bot.command()
async def buyprice(ctx,id:int,price:float):

    item = get_listing(id)

    if not item:
        return await ctx.send(
            "❌ Listing not found"
        )


    item["buy_price"] = price
    item["profit"] = float(item.get("sell_price",0))-price

    update_listing(
        id,
        item
    )


    await ctx.send(
        f"💰 Updated #{id} purchase price: {price}kr"
    )



async def main():

    await start_server()

    print("Starting Discord bot...")

    await bot.start(
        TOKEN
    )



asyncio.run(main())
