import io
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
from database import init_db, save_listing, get_listing
from gemini_service import analyze_images

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID", "0"))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", "8"))
PORT = int(os.getenv("PORT", "10000"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def health_handler(request):
    return web.Response(text="OK")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Health server listening on port {PORT}")


def listing_text(item):
    return (f"**{item.get('title','Okänt')}**\n"
            f"Kategori: {item.get('category','Okänt')} / {item.get('subcategory','Okänt')}\n"
            f"Varumärke: {item.get('brand','Okänt')}\nStorlek: {item.get('size','Okänt')}\n"
            f"Skick: {item.get('condition','Okänt')}\nFärg: {item.get('color','Okänt')}\n"
            f"Prisförslag: {item.get('suggested_price_sek','Okänt')} kr\n\n"
            f"{item.get('description','')}\n\n"
            f"**Kontrollera:** {', '.join(item.get('needs_confirmation', [])) or 'Inget angivet'}")


@bot.event
async def on_ready():
    init_db()
    print(f"Inloggad som {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if ALLOWED_CHANNEL_ID and message.channel.id != ALLOWED_CHANNEL_ID:
        await bot.process_commands(message)
        return
    images = []
    for attachment in message.attachments[:MAX_IMAGES]:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            images.append((await attachment.read(), attachment.content_type))
    if images:
        status = await message.reply("🔎 Analyserar bilderna på svenska...")
        try:
            result = await analyze_images(images)
            listing_id = save_listing(result)
            embed = discord.Embed(title=f"Listing #{listing_id}: {result.get('title','Okänt')}", description=result.get('description',''), color=0x5865F2)
            embed.add_field(name="Kategori", value=result.get("category", "Okänt"), inline=True)
            embed.add_field(name="Skick", value=result.get("condition", "Okänt"), inline=True)
            embed.add_field(name="Prisförslag", value=f"{result.get('suggested_price_sek','Okänt')} kr", inline=True)
            embed.add_field(name="Kontrollera", value=", ".join(result.get("needs_confirmation", [])) or "Inget angivet", inline=False)
            await status.edit(content=f"✅ Sparad som listing **#{listing_id}**\n\n{listing_text(result)}", embed=embed)
        except Exception as exc:
            await status.edit(content=f"❌ Något gick fel: `{type(exc).__name__}: {exc}`")
    await bot.process_commands(message)


@bot.command(name="listing")
async def listing(ctx, listing_id: int):
    item = get_listing(listing_id)
    if not item:
        await ctx.send("Hittade ingen listing med det ID:t.")
        return
    await ctx.send(listing_text(item))


@bot.command(name="help_vinted")
async def help_vinted(ctx):
    await ctx.send("Skicka en eller flera produktbilder så analyserar jag dem. Använd `!listing ID` för att hämta en sparad listing. Allt granskas manuellt innan publicering.")


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN saknas")

async def main():
    await start_health_server()
    await bot.start(TOKEN)

asyncio.run(main())
