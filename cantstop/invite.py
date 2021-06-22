import enum

from discord import ui
import discord

from .constants import LIST_MARKER

class GameStatus(enum.Enum):
    requested_to_start = 1
    cancelled = 2

class InviteView(ui.View):
    def __init__(self, *args, caller, **kwards):
        super().__init__(*args, **kwards)
        self.participants = [caller]
        self.caller = caller
        self.status = None

    async def finalize(self, interaction):
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @ui.button(label="Записаться", style=discord.ButtonStyle.green)
    async def entry(self, button, interaction):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            participants = [str(m) for m in self.participants]
            await interaction.response.edit_message(content=f"Участники:\n{LIST_MARKER} " + f"\n{LIST_MARKER} ".join(participants))

    @ui.button(label="Выйти из игры", style=discord.ButtonStyle.grey)
    async def exit(self, button, interaction):
        if interaction.user in self.participants:
            self.participants.remove(interaction.user)
            participants = [str(m) for m in self.participants]
            await interaction.response.edit_message(content=f"Участники:\n{LIST_MARKER} " + f"\n{LIST_MARKER} ".join(participants))

    @ui.button(label="Начать игру", style=discord.ButtonStyle.blurple)
    async def begin(self, button, interaction):
        if interaction.user == self.caller:
            self.status = GameStatus.requested_to_start
            await self.finalize(interaction)
        else:
            await interaction.response.send_message("Начать игру может только её создатель.")
    
    @ui.button(label="Отменить игру", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        if interaction.user == self.caller:
            self.status = GameStatus.cancelled
            await self.finalize(interaction)
        else:
            await interaction.response.send_message("Отменить игру может только её создатель.")
