from typing import List
import discord
from .game import Game

async def start(
    interaction: discord.Interaction, 
    participants: List[discord.Member]
):
    view = Game(players=participants)
    await interaction.followup.send(content=view.content, view=view)
