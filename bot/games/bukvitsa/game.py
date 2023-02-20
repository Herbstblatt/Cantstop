import random
import discord
from discord.ext import tasks, commands
import asyncio

from constants import LETTER_PROBABILITY_DISTRIBUTION, DICTIONARY


def generate_letters(distribution: dict = LETTER_PROBABILITY_DISTRIBUTION) -> list:
    return random.choices(
        list(distribution.keys()), weights=list(distribution.values()), k=3
    )


def check_word(letters: list, word: str, dictionary: set = DICTIONARY) -> bool:
    if (
        all([letters.count(l) <= word.lower().count(l) for l in letters])
        and word.lower() in DICTIONARY
    ):
        return True
    return False


class Game(discord.ui.View):
    def __init__(
        self,
        host: discord.User,
        channel: discord.TextChannel,
        g_list,
        timeout: int = 420,
    ):
        super().__init__(timeout=timeout)
        self.host = host
        self.players = {host: list()}
        self.channel = channel
        self.ongoing = False
        self.letters = generate_letters()
        self.g_list = g_list

    @discord.ui.button(label="Присоединиться к игре", style=discord.ButtonStyle.green)
    async def add_player(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        if interaction.user in list(self.players.keys()):
            await interaction.response.send_message(
                "Вы уже участвуете в данной игре", ephemeral=True
            )
        elif self.g_list.check_user(interaction.user):
            await interaction.response.send_message(
                "Вы уже присоединились к другой игре", ephemeral=True
            )
        else:
            self.players[interaction.user] = list()
            await self.update(interaction.response)

    @discord.ui.button(label="Покинуть игру", style=discord.ButtonStyle.red)
    async def delete_player(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        if interaction.user == self.host:
            await interaction.response.send_message(
                "Ведущий не может покинуть игру", ephemeral=True
            )
        elif interaction.user in list(self.players.keys())[1:]:
            self.players.pop(interaction.user)
            await self.update(interaction.response)
        else:
            await interaction.response.send_message(
                "Вы не присоединялись к игре", ephemeral=True
            )

    @discord.ui.button(
        label="Начать игру",
        style=discord.ButtonStyle.blurple,
        emoji=discord.PartialEmoji.from_str("<:icons_customstaff:1009175726810988714"),
    )
    async def start(self, interaction: discord.Interaction, button: discord.Button):
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
            for player in self.players:
                try:
                    await player.send(
                        embed=discord.Embed(
                            description=f'Вы должны составить как можно больше слов с буквами **{"**, **".join(self.letters)}** за три минуты',
                            colour=discord.Colour.blue(),
                        )
                    )
                except discord.errors.Forbidden:
                    await self.channel.send(
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
            for player in self.players:
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
                    description=await self.leaderboard(),
                    colour=discord.Colour.blue(),
                )
            )
            self.stop()
            self.g_list.delete(self)
        else:
            await interaction.response.send_message(
                "Только ведущий может запустить игру", ephemeral=True
            )

    @discord.ui.button(
        label="Отменить игру",
        style=discord.ButtonStyle.grey,
        emoji=discord.PartialEmoji.from_str("<:icons_customstaff:1009175726810988714"),
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user == self.host:
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Игра отменена", style=discord.ButtonStyle.grey, disabled=True
                )
            )
            await interaction.message.edit(view=view)
            await interaction.response.send_message("Игра отменена", ephemeral=True)
            self.stop()
            self.g_list.delete(self)
        else:
            await interaction.response.send_message(
                "Только ведущий может отменить игру", ephemeral=True
            )

    @discord.ui.button(
        label="Поменять буквы",
        style=discord.ButtonStyle.grey,
        emoji=discord.PartialEmoji.from_str("<:icons_customstaff:1009175726810988714"),
    )
    async def change_letters(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        if interaction.user == self.host:
            self.letters = generate_letters()
            await self.update(interaction.response)
        else:
            await interaction.response.send_message(
                "Только ведущий может поменять буквы", ephemeral=True
            )

    async def leaderboard(self):
        leaderboard = ""
        for place, player in enumerate(
            sorted(
                self.players.items(), key=lambda player: len(player[1]), reverse=True
            )
        ):
            leaderboard += f"**{place + 1}**. {player[0].mention} — {len(player[1])}\n"
        return leaderboard

    async def update(self, response: discord.InteractionResponse):
        content = f'Игроки должны будут составить в личных сообщениях бота как можно больше слов с буквами **{"**, **".join(self.letters)}** за три минуты. Начать игру может только ведущий, нажав на соответствующую кнопку\n\n**Игроки**:\n<:icons_customstaff:1009175726810988714> {self.host.mention}'
        if len(self.players) > 1:
            content += (
                "\n<:icons_Person:1009175664156487810>"
                + "\n<:icons_Person:1009175664156487810>".join(
                    [player.mention for player in list(self.players.keys())[1:]]
                )
            )
        await response.edit_message(
            embed=discord.Embed(
                title=":abc: Буквица", description=content, colour=discord.Colour.blue()
            )
        )

    @tasks.loop(seconds=60.0, count=2)
    async def timer(self):
        for player in self.players:
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
        self.g_list.delete(self)


class GameList:
    def __init__(self):
        self.games = list()

    def add(self, game: Game):
        self.games.append(game)

    def delete(self, game: Game):
        self.games.remove(game)

    def check_channel(self, channel: discord.TextChannel) -> bool:
        for game in self.games:
            if channel == game.channel:
                return True
        return False

    def check_user(self, user: discord.User) -> bool:
        for game in self.games:
            if user in set(game.players.keys()):
                return True
        return False


class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g_list = GameList()

    @commands.hybrid_command()
    @commands.guild_only()
    async def start(self, ctx: commands.Context):
        if self.g_list.check_user(ctx.author):
            await ctx.send("Вы уже записались в другую игру")
        elif self.g_list.check_channel(ctx.channel):
            await ctx.send("В этом канале уже идёт игра")
        else:
            game = Game(ctx.author, ctx.channel, self.g_list)
            self.g_list.add(game)

            await ctx.send(
                embed=discord.Embed(
                    title=":abc: Буквица",
                    description=f'Игроки должны будут составить в личных сообщениях бота как можно больше слов c буквами **{"**, **".join(game.letters)}** за три минуты. Начать игру может только ведущий, нажав на соответствующую кнопку\n\n**Игроки**:\n<:icons_customstaff:1009175726810988714> {ctx.author.mention}',
                    colour=discord.Colour.blue(),
                ),
                view=game,
            )

    @commands.Cog.listener()
    async def on_message(self, msg):
        for game in self.g_list.games:
            if all(
                [
                    msg.author in set(game.players.keys()),
                    type(msg.channel) == discord.DMChannel,
                    game.ongoing,
                ]
            ):
                if (
                    check_word(game.letters, msg.content)
                    and msg.content.lower() not in game.players[msg.author]
                ):
                    await msg.add_reaction("✅")
                    game.players[msg.author].append(msg.content.lower())
                else:
                    await msg.add_reaction("❌")


async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))
