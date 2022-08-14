#!/usr/bin/env python3

from typing import Dict
import os

from discord.ext import commands
import discord

from . import invite
from .game import Game
from ..games.cantstop import game

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or('$'), 
            intents=discord.Intents.default(),  
            **kwargs
        )

        self.games: Dict[str, Game] = {}
        for dir in os.listdir("bot/games"):
            self.games[dir] = Game.from_dir(dir)

    async def setup_hook(self) -> None:
        await self.load_extension("jishaku")
        
    async def on_ready(self):
        print(f'Logged on as {self.user}')

bot = Bot()  

@bot.tree.command(name="game")
async def field_cmd(interaction: discord.Interaction):
    """Start a new game
    
    """

    game_invite = invite.InviteView(host=interaction.user)
    await interaction.response.send_message(
        view=game_invite,
        content=game_invite.render()
    )
    await game_invite.wait()
    
    if game_invite.status == invite.GameStatus.cancelled:
        await interaction.followup.send(f"{interaction.user} cancelled the game :confused:")
    elif game_invite.status == invite.GameStatus.requested_to_start:
        view = game.Game(players=game_invite.participants)
        await interaction.followup.send(content=view.content, view=view)

