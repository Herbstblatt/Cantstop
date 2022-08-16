from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

from .game import Game, load_games

if TYPE_CHECKING:
    from .bot import Bot


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
    async def convert(cls, ctx: commands.Context, arg: str):
        return ctx.bot.games[arg]
    

class Commands(commands.Cog):
    def __init__(self, bot: "Bot") -> None:
        self.bot = bot

    @commands.hybrid_group()
    async def game(self, ctx: commands.Context) -> None:
        pass

    @game.command()
    async def list(self, ctx: commands.Context) -> None:
        """Показывает список поддерживаемых игр
        """
        em = discord.Embed(
            title="Список поддерживаемых игр",
            color=discord.Color.blurple()
        )
        for game in self.bot.games.values():
            em.add_field(
                name=game.name,
                value=f"**Описание**: {game.description}\n**Количество участников**: {game.min_players}—{game.max_players}"
            )
        await ctx.send(embed=em)

    @game.command()
    async def info(self, ctx: commands.Context, game: app_commands.Transform[Game, GameTransformer]):
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
    

async def setup(bot: "Bot") -> None:
    await bot.add_cog(Commands(bot))
        