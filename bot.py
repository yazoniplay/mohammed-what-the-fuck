import os, asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
from database import init_db, save_listing, get_listing, update_listing, get_all_listings
from gemini_service import analyze_images, regenerate_description

load_dotenv()
TOKEN=os.getenv('DISCORD_TOKEN')
PORT=int(os.getenv('PORT','10000'))
MAX_IMAGES=int(os.getenv('MAX_IMAGES','8'))

bot=commands.Bot(command_prefix='!', intents=discord.Intents(message_content=True, guilds=True))

async def start_server():
    app=web.Application(); app.router.add_get('/',lambda r:web.Response(text='running'))
    runner=web.AppRunner(app); await runner.setup(); await web.TCPSite(runner,'0.0.0.0',PORT).start()


def vinted_text(x):
    return f"{x.get('title','Okänt')}\n\n{x.get('description','')}\n\nPris: {x.get('suggested_price_sek','')} kr\nTaggar: {', '.join(x.get('tags',[]))}"

@bot.event
async def on_ready():
    init_db(); print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:return
    imgs=[(await a.read(),a.content_type) for a in message.attachments[:MAX_IMAGES] if a.content_type and a.content_type.startswith('image/')]
    if imgs:
        m=await message.reply('🤖 Analyserar...')
        try:
            data=await analyze_images(imgs); lid=save_listing(data)
            await m.edit(content=f'✅ Listing #{lid}\n{vinted_text(data)}')
        except Exception as e: await m.edit(content=f'❌ {e}')
    await bot.process_commands(message)

@bot.command()
async def inventory(ctx):
    items=get_all_listings()
    await ctx.send('\n'.join([f"#{i['id']} {i.get('title','')} | {i.get('status','draft')} | {i.get('profit',0)}kr" for i in items[:15]]) or '📦 Empty')

@bot.command()
async def sold(ctx,id:int,price:float):
    item=get_listing(id); item['status']='sold'; item['sell_price']=price; update_listing(id,item)
    await ctx.send(f"✅ Sold #{id} profit {item.get('profit',0)}kr")

@bot.command()
async def listing(ctx,id:int):
    await ctx.send(vinted_text(get_listing(id)))

async def main():
    await start_server(); await bot.start(TOKEN)

asyncio.run(main())
