import discord
from database import get_listing, update_listing
from gemini_service import regenerate_description


class PriceModal(discord.ui.Modal, title="Edit listing price"):
    price = discord.ui.TextInput(
        label="New price (SEK)",
        placeholder="299",
        max_length=10
    )

    def __init__(self, listing_id):
        super().__init__()
        self.listing_id = listing_id

    async def on_submit(self, interaction: discord.Interaction):
        item = get_listing(self.listing_id)

        if not item:
            return await interaction.response.send_message(
                "❌ Listing not found",
                ephemeral=True
            )

        item["suggested_price_sek"] = float(self.price.value)
        update_listing(self.listing_id, item)

        await interaction.response.send_message(
            f"✅ Price updated to {self.price.value} kr",
            ephemeral=True
        )


async def regenerate_listing(interaction, listing_id):
    item = get_listing(listing_id)

    if not item:
        return await interaction.response.send_message(
            "❌ Listing not found",
            ephemeral=True
        )

    text = await regenerate_description(item)
    item["description"] = text
    update_listing(listing_id, item)

    await interaction.response.send_message(
        "✅ Description regenerated",
        ephemeral=True
    )
