import random
from typing import TYPE_CHECKING
import discord
from discord.ext import tasks, commands
import asyncio

from bot.core.invite import Room, RoomState
from .constants import LETTER_PROBABILITY_DISTRIBUTION, DICTIONARY

if TYPE_CHECKING:
    from bot.core.bot import Bot


def generate_letters(distribution: dict = LETTER_PROBABILITY_DISTRIBUTION) -> list:
    return random.choices(
        list(distribution.keys()), weights=list(distribution.values()), k=3
    )


def check_word(letters: list, word: str, dictionary: set = DICTIONARY) -> bool:
    if (
        all(letters.count(l) <= word.lower().count(l) for l in letters)
        and word.lower() in DICTIONARY
    ):
        return True
    return False


class Game(discord.ui.View):
    def __init__(
        self,
        room: Room,
        timeout: int = 420,
    ):
        super().__init__(timeout=timeout)
        self.room = room
        self.host = room.host
        self.players = {p.id: list() for p in room.participants}
        self.active_interaction = room.view.active_interaction
        self.ongoing = False
        self.letters = generate_letters()
        
    @discord.ui.button(
        label="Начать игру",
        style=discord.ButtonStyle.blurple,
        emoji=discord.PartialEmoji.from_str("<:icons_customstaff:1009175726810988714"),
    )
    async def start(self, interaction: discord.Interaction, _):
        if interaction.user == self.host:
            await interaction.response.defer()
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Игра начата", style=discord.ButtonStyle.grey, disabled=True
                )
            )
            await interaction.message.edit(view=view)
            self.ongoing = True
            for player in self.room.participants:
                try:
                    await player.send(
                        embed=discord.Embed(
                            description=f"Вы должны составить как можно больше слов с буквами **{'**, **'.join(self.letters)}** за три минуты",
                            colour=discord.Colour.blue(),
                        )
                    )
                except discord.errors.Forbidden:
                    await self.active_interaction.followup.send(
                        embed=discord.Embed(
                            title=":exclamation: Ошибка",
                            description=f"{player.mention}, бот не может отправлять вам сообщения в личные сообщения. Проверьте свои настройки конфиденциальности",
                            colour=discord.Colour.red(),
                        )
                    )
            await asyncio.sleep(60.0)
            self.timer.start()
            await asyncio.sleep(120.0)
            self.ongoing = False
            for player in self.room.participants:
                try:
                    await player.send(
                        embed=discord.Embed(
                            description=f"Игра окончена", colour=discord.Colour.red()
                        )
                    )
                except discord.errors.Forbidden:
                    pass
            await interaction.followup.send(
                embed=discord.Embed(
                    title=":trophy: Результаты",
                    description=await self.render_leaderboard(),
                    colour=discord.Colour.blue(),
                )
            )
            self.stop()
            self.room.manager.delete(self.room)
        else:
            await interaction.response.send_message(
                "Только ведущий может запустить игру", ephemeral=True
            )

    @discord.ui.button(
        label="Поменять буквы",
        style=discord.ButtonStyle.grey,
        emoji=discord.PartialEmoji.from_str("<:icons_customstaff:1009175726810988714"),
    )
    async def change_letters(
        self, interaction: discord.Interaction, _
    ):
        if interaction.user == self.host:
            self.letters = generate_letters()
            await interaction.response.edit_message(embed=self.render())
        else:
            await interaction.response.send_message(
                "Только ведущий может поменять буквы", ephemeral=True
            )

    async def render_leaderboard(self):
        leaderboard = ""
        for place, player in enumerate(
            sorted(
                self.players.items(), key=lambda player: len(player[1]), reverse=True
            )
        ):
            leaderboard += f"**{place + 1}**. <@{player[0]}> — {len(player[1])}\n"
        return leaderboard

    def render(self):
        return discord.Embed(
            title="Выбор букв",
            description=f"После начала игры должны будут составить в личных сообщениях бота как можно больше слов c буквами **{'**, **'.join(self.letters)}** за три минуты. Ведущий может поменять буквы или начать игру.",
            color=discord.Color.blue()
        )

    @tasks.loop(seconds=60.0, count=2)
    async def timer(self):
        for player in self.room.participants:
            try:
                await player.send(
                    embed=discord.Embed(
                        description=f":timer: Минут до окончания игры: {2 - self.timer.current_loop}",
                        colour=discord.Colour.red(),
                    )
                )
            except discord.errors.Forbidden:
                pass

    async def on_timeout(self):
        self.room.manager.delete(self.room)


class GameCog(commands.Cog):
    def __init__(self, bot: "Bot"):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        for room in self.bot.rooms:
            if all(
                [
                    room.game == self.bot.games["bukvitsa"],
                    msg.author in room.participants,
                    type(msg.channel) == discord.DMChannel,
                    room.state is RoomState.game_in_progress,
                ]
            ):
                game = room.attached_data
                assert isinstance(game, Game)
                if (
                    check_word(game.letters, msg.content)
                    and msg.content.lower() not in game.players[msg.author.id]
                ):
                    await msg.add_reaction("✅")
                    game.players[msg.author.id].append(msg.content.lower())
                else:
                    await msg.add_reaction("❌")
