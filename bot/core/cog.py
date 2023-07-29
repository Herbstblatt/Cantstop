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

class InviteMember(discord.ui.View):
	def __init__(self, room, member):
		super().__init__()
		self.room = room
		self.member = member
	
	@discord.ui.button(label='Согласиться', style=discord.ButtonStyle.green)
	async def accept(self, interaction, button):
		if interaction.user.id == self.member.id:
			if self.room.state != RoomState.waiting:
				await interaction.response.send_message('Данная игра уже начата или отменена.', ephemeral=True)
			elif self.member in self.room.participants:
				await interaction.response.send_message('Вы уже находитесь в данной комнате.', ephemeral=True)
			elif self.room.manager.check_user(self.member):
				await interaction.response.send_message('Вы уже находитесь в другой комнате.', ephemeral=True)
			else:
				if self.member.id in getattr(self.room, 'declined', []):
					self.room.declined.remove(self.member.id)
				self.clear_items()
				self.add_item(discord.ui.Button(label='Одобрено', style=discord.ButtonStyle.green, disabled=True))
				await self.room.add_participant(self.member)
				await self.room.view.message.edit(embed=self.room.view.render())
				await interaction.response.edit_message(view=self)
		else:
			await interaction.response.send_message('Вы не участвуете в данном приглашении.', ephemeral=True)

	@discord.ui.button(label='Отказаться', style=discord.ButtonStyle.red)
	async def decline(self, interaction, button):
		if interaction.user.id == self.member.id:
			if self.member.id in getattr(self.room, 'declined', []):
				await interaction.response.send_message('Вы уже отказалиcь от данного приглашения.', ephemeral=True)
			else:
				if getattr(self.room, 'declined', None):
					self.room.declined.append(self.member.id)
				else:
					self.room.declined = [self.member.id]
				self.clear_items()
				self.add_item(discord.ui.Button(label='Отклонено', style=discord.ButtonStyle.red, disabled=True))
				await interaction.response.edit_message(view=self)
		else:
			await interaction.response.send_message('Вы не участвуете в данном приглашении.', ephemeral=True)

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
            description = f'**Описание**: {game.description}\n**Количество участников**: '
            if game.min_players and game.max_players:
                description += f'{game.min_players}–{game.max_players}'
            else:
                description += 'Не ограничено'
            em.add_field(
                name=game.name,
                value=description,
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
        players = 'Не ограничено'
        if game.min_players and game.max_players:
            players = f'{game.min_players}–{game.max_players}'
        em.add_field(
            name='Количество участников',
            value=players,
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

    @room.command()
    @commands.guild_only()
    async def invite(self, ctx, member: discord.Member):
        """Приглашает игрока в комнату

        Аргументы:
            member: Игрок, которого нужно пригласить
        """
        for room in self.bot.rooms:
            if room.state == RoomState.waiting and room.host.id == ctx.author.id and room.view.message.channel.id == ctx.channel.id:
                if member in room.participants:
                    await ctx.send('Данный игрок уже находится в комнате.', ephemeral=True)
                elif room.manager.check_user(member):
                    await ctx.send('Данный игрок уже находится в другой комнате.', ephemeral=True)
                elif member.id in getattr(room, 'declined', []):
                    await ctx.send('Данный игрок отказался от приглашения в комнату.', ephemeral=True)
                else:
                    await ctx.send(f'{ctx.author.global_name} приглашает игрока {member.mention} в игру {room.game.emoji} {room.game.name}.', view=InviteMember(room, member))
            return
        await ctx.send('Вы не являетесь ведущим ни в одной из комнат в данном канале.', ephemeral=True)

async def setup(bot: "Bot") -> None:
    await bot.add_cog(Commands(bot))
        
