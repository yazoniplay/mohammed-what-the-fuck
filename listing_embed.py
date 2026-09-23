import discord


def listing_embed(data, listing_id):
    embed = discord.Embed(
        title=f"✅ Listing #{listing_id} Ready",
        description=data.get("description", "No description"),
        color=discord.Color.green()
    )

    embed.add_field(
        name="Title",
        value=data.get("title", "Okänt"),
        inline=False
    )

    embed.add_field(
        name="Price",
        value=f"{data.get('recommended_price', data.get('suggested_price_sek', '?'))} kr",
        inline=True
    )

    embed.add_field(
        name="Condition",
        value=data.get("condition", "Okänt"),
        inline=True
    )

    tags = data.get("tags", [])
    if tags:
        embed.add_field(
            name="Tags",
            value=" ".join(tags),
            inline=False
        )

    embed.set_footer(text="AI Reseller Assistant")

    return embed
