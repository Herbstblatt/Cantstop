from typing import TYPE_CHECKING
import discord
from discord.ext import commands

from bot.core.game import load_games
from bot.core.invite import Room
from .game import Game, GameCog

if TYPE_CHECKING:
    from bot.core.bot import Bot

async def setup(bot: "Bot"):
    await bot.add_cog(GameCog(bot))

async def start(room: Room):
    assert room.view is not None and room.view.active_interaction is not None
    
    view = Game(
        room=room
    )
    em = discord.Embed(
        title="Выбор букв",
        description=f"После начала игры должны будут составить в личных сообщениях бота как можно больше слов c буквами **{'**, **'.join(view.letters)}** за три минуты. Ведущий может поменять буквы или начать игру.",
        color=discord.Color.blue()
    )

    await room.view.active_interaction.followup.send(view=view, embed=em)
    room.attached_data = view
