import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
from database import init_db, save_listing, get_listing, update_listing
from gemini_service import analyze_images, regenerate_description

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MAX_IMAGES = int(os.getenv('MAX_IMAGES', '8'))
PORT = int(os.getenv('PORT', '10000'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def health(request):
    return web.Response(text='Discord bot is running')

async def start_server():
    app = web.Application()
    app.router.add_get('/', health)
    app.router.add_get('/health', health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    print(f'Web server running on port {PORT}')


def vinted_text(item):
    return f"{item.get('title','Okänt')}\n\n{item.get('description','')}\n\nStorlek: {item.get('size','Okänt')}\nSkick: {item.get('condition','Okänt')}\nFärg: {item.get('color','Okänt')}\nPris: {item.get('suggested_price_sek','Okänt')} kr"


class ListingView(discord.ui.View):
    def __init__(self, id):
        super().__init__(timeout=1800)
        self.id = id
        self.add_item(discord.ui.Button(label='🚀 Öppna Vinted', url='https://www.vinted.se/upload'))

    @discord.ui.button(label='📋 Vinted text')
    async def text(self, i, b):
        await i.response.send_message(vinted_text(get_listing(self.id)), ephemeral=True)

    @discord.ui.button(label='🔄 Ny beskrivning')
    async def regen(self, i, b):
        await i.response.defer(ephemeral=True)
        item = get_listing(self.id)
        item['description'] = await regenerate_description(item)
        update_listing(self.id, item)
        await i.followup.send('✅ Automatisk ny beskrivning klar:\n' + item['description'], ephemeral=True)

    @discord.ui.button(label='💰 Ändra pris')
    async def price(self, i, b):
        await i.response.send_modal(PriceModal(self.id))


class PriceModal(discord.ui.Modal, title='Ändra pris'):
    price = discord.ui.TextInput(label='Pris SEK')

    def __init__(self, id):
        super().__init__()
        self.id = id

    async def on_submit(self, i):
        item = get_listing(self.id)
        item['suggested_price_sek'] = self.price.value
        update_listing(self.id, item)
        await i.response.send_message('✅ Pris sparat', ephemeral=True)


@bot.event
async def on_ready():
    init_db()
    print(f'Logged in as {bot.user}')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    images = []
    for a in message.attachments[:MAX_IMAGES]:
        if a.content_type and a.content_type.startswith('image/'):
            images.append((await a.read(), a.content_type))

    if images:
        msg = await message.reply('🤖 Automatisk analys startad...')
        try:
            data = await analyze_images(images)
            listing_id = save_listing(data)
            formatted = vinted_text(data)
            await msg.edit(content=f'✅ Listing #{listing_id} skapad automatiskt\n\n{formatted}\n\nKlicka på knapparna för att förbättra den.', view=ListingView(listing_id))
        except Exception as e:
            await msg.edit(content=f'❌ Automationsfel: {e}')

    await bot.process_commands(message)


@bot.command()
async def listing(ctx, id: int):
    item = get_listing(id)
    await ctx.send(vinted_text(item), view=ListingView(id))


async def main():
    await start_server()
    await bot.start(TOKEN)


asyncio.run(main())
