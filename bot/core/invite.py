import enum

from discord import ui
import discord

from ..games.cantstop.constants import LIST_MARKER, OTHER_MARKER

class GameStatus(enum.Enum):
    requested_to_start = 1
    cancelled = 2

class InviteView(ui.View):
    def __init__(self, *args, host, **kwards):
        super().__init__(*args, **kwards)
        self.participants = [host]
        self.host = host
        self.status = None

    async def finalize(self, interaction):
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    def render(self):
        content = "Participants:"
        for p in self.participants:
            if p == self.host:
                content += f"\n {OTHER_MARKER} {p} *[Host]*"
            else:
                content += f"\n {LIST_MARKER} {p}"
        
        return content

    @ui.button(label="Записаться", style=discord.ButtonStyle.green)
    async def entry(self, interaction, button):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)

            if self.host is None:
                self.host = interaction.user

            await interaction.response.edit_message(content=self.render())

    @ui.button(label="Выйти из игры", style=discord.ButtonStyle.grey)
    async def exit(self, interaction, button):
        if interaction.user in self.participants:
            self.participants.remove(interaction.user)

            if interaction.user == self.host:
                if self.participants:
                    self.host = self.participants[0]
                else:
                    self.host = None

            await interaction.response.edit_message(content=self.render())

    @ui.button(label="Начать игру", style=discord.ButtonStyle.blurple)
    async def begin(self, interaction, button):
        if interaction.user == self.host:
            self.status = GameStatus.requested_to_start
            await self.finalize(interaction)
        else:
            await interaction.response.send_message("Начать игру может только её создатель.")
    
    @ui.button(label="Отменить игру", style=discord.ButtonStyle.red)
    async def cancel(self, interaction, button):
        if interaction.user == self.host:
            self.status = GameStatus.cancelled
            await self.finalize(interaction)
        else:
            await interaction.response.send_message("Отменить игру может только её создатель.")
