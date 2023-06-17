from __future__ import annotations

from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

from .invite import Room, RoomState

from .game import Game, load_games

if TYPE_CHECKING:
    from .bot import Bot, Context


class GameTransformer(app_commands.Transformer):
    def __init__(self) -> None:
        super().__init__()
        self.games = load_games()
    
    @property
    def choices(self):
        return [
            app_commands.Choice(
                name=g.name, value=name
            ) 
            for name, g in self.games.items()
        ]

    async def transform(self, interaction: discord.Interaction, value: str) -> Game:
        return self.games[value]

    @classmethod
    async def convert(cls, ctx: Context, arg: str):
        return ctx.bot.games[arg]
    

class Commands(commands.Cog):
    def __init__(self, bot: "Bot") -> None:
        self.bot = bot

    @commands.hybrid_group()
    async def game(self, ctx: Context) -> None:
        pass

    @game.command()
    async def list(self, ctx: Context) -> None:
        """Показывает список поддерживаемых игр
        """
        em = discord.Embed(
            title="Список поддерживаемых игр",
            color=discord.Color.blurple()
        )
        for game in self.bot.games.values():
            em.add_field(
                name=game.name,
                value=f"**Описание**: {game.description}\n**Количество участников**: {game.min_players}—{game.max_players}",
                inline=False
            )
        await ctx.send(embed=em)

    @game.command()
    async def info(self, ctx: Context, game: app_commands.Transform[Game, GameTransformer]):
        """Показывает информацию о конкретной игре
        
        Аргументы:
            game: Название игры, о которой надо показать информацию
        """
        em = discord.Embed(
            title=game.name,
            color=discord.Color.blurple(),
            description=game.description
        )
        em.add_field(
            name="Количество участников",
            value=f"{game.min_players}—{game.max_players}",
            inline=True
        )
        await ctx.send(embed=em)

    @commands.hybrid_group()
    async def room(self, _):
        pass

    @room.command()
    @commands.guild_only()
    async def create(self, ctx: Context, game: app_commands.Transform[Game, GameTransformer]):
        """Создаёт новую комнату

        Аргументы:
            game: Название игры
        """
        if self.bot.rooms.check_user(ctx.author):  # type: ignore
            await ctx.send("Вы уже участвуете в другой игре.", ephemeral=True)
            return
            
        room = await Room.create(ctx, game)
        self.bot.rooms.add(room)
        await room.wait()

        if room.state == RoomState.game_in_progress:
            await game.start(room)
        else:
            self.bot.rooms.delete(room)
    

async def setup(bot: "Bot") -> None:
    await bot.add_cog(Commands(bot))
        
