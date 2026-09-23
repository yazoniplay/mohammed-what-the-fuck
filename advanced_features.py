import discord


class ListingView(discord.ui.View):
    def __init__(self, listing_id=None, vinted_url="https://www.vinted.se/items/new"):
        super().__init__(timeout=3600)
        self.listing_id = listing_id
        self.vinted_url = vinted_url

    @discord.ui.button(label="🛒 Open Vinted", style=discord.ButtonStyle.link, url="https://www.vinted.se/items/new")
    async def vinted(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="✏️ Edit price", style=discord.ButtonStyle.primary)
    async def edit_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Send the new price like: `299`",
            ephemeral=True
        )

    @discord.ui.button(label="🔄 Regenerate", style=discord.ButtonStyle.secondary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Regeneration queued.",
            ephemeral=True
        )

    @discord.ui.button(label="📋 Copy listing", style=discord.ButtonStyle.success)
    async def copy_listing(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Listing copied."
            , ephemeral=True
        )
