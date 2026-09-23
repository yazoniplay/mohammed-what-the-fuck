import os, asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
from database import init_db, save_listing, get_listing, update_listing, get_all_listings
from gemini_service import analyze_images, regenerate_description
from reseller_features import listing_quality, generate_tags

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
            data=await analyze_images(imgs)
            data.setdefault('status','draft')
            data.setdefault('buy_price',0)
            data.setdefault('sell_price',0)
            data.setdefault('profit',0)
            data['tags']=generate_tags(data)
            quality=listing_quality(data)
            data['quality_score']=quality['score']
            data['quality_missing']=quality['missing']
            lid=save_listing(data)
            improvements=', '.join(quality['missing']) or 'Ingen - redo!'
            await m.edit(content=f"✅ Listing #{lid}\n⭐ Quality: {quality['score']}/100\n🔧 Improve: {improvements}\n\n{vinted_text(data)}")
        except Exception as e: await m.edit(content=f'❌ {e}')
    await bot.process_commands(message)

@bot.command()
async def inventory(ctx):
    items=get_all_listings()
    await ctx.send('\n'.join([f"#{i['id']} {i.get('title','')} | {i.get('status','draft')} | {i.get('profit',0)}kr" for i in items[:15]]) or '📦 Empty')

@bot.command()
async def sold(ctx,id:int,price:float):
    item=get_listing(id)
    if not item:return await ctx.send('❌ Listing not found')
    item['status']='sold'; item['sell_price']=price; item['profit']=price-float(item.get('buy_price',0)); update_listing(id,item)
    await ctx.send(f"✅ Sold #{id}\nProfit: {item['profit']}kr")

@bot.command()
async def listing(ctx,id:int):
    item=get_listing(id)
    await ctx.send(vinted_text(item) if item else '❌ Listing not found')

@bot.command()
async def dashboard(ctx):
    items=get_all_listings(); sold=[i for i in items if i.get('status')=='sold']
    await ctx.send(f"📊 Reseller Dashboard\n\nItems: {len(items)}\nSold: {len(sold)}\nRevenue: {sum(float(i.get('sell_price',0)) for i in sold)}kr\nProfit: {sum(float(i.get('profit',0)) for i in sold)}kr")

@bot.command()
async def buyprice(ctx,id:int,price:float):
    item=get_listing(id)
    if not item:return await ctx.send('❌ Listing not found')
    item['buy_price']=price; item['profit']=float(item.get('sell_price',0))-price; update_listing(id,item)
    await ctx.send(f'💰 Updated #{id} purchase price: {price}kr')

async def main():
    await start_server(); await bot.start(TOKEN)

asyncio.run(main())
