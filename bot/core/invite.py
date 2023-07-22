import enum
import importlib
from typing import Any, Optional, TypeVar, Union

from discord import ui
from discord.ext import commands
import discord

from .errors import RoomFilled, AlreadyParticipating
from .game import Game

T = TypeVar("T", bound=commands.Bot)

class RoomState(enum.Enum):
    waiting = 1
    game_in_progress = 2
    inactive = 3

class Room:
    def __init__(self, game: Game, host: discord.Member, manager: "RoomManager"):
        self.manager = manager
        self.game = game
        self.participants = [host]
        self.host = host
        self.state = RoomState.waiting
        self.view: Optional["RoomView"] = None
        self.attached_data: Any = None

    @classmethod
    async def create(cls, context: Union[discord.Interaction, commands.Context[T]], game: Game) -> "Room":
        """Create a new room and send its render as a response in the given context.
        
        Arguments:
            interaction: 
            game:
        """
        if isinstance(context, discord.Interaction):
            context = await commands.Context.from_interaction(context)

        room = cls(
            game=game, 
            host=context.author, 
            manager=context.bot.rooms
        )
        room.view = RoomView(room)

        if game.name == 'Мафия':
            mafia = importlib.import_module('bot.games.mafia.selects')
            room.view.add_item(mafia.OpenSettings(room).button)

        msg = await context.send(
            view=room.view,
            embed=room.view.render()
        )
        room.view.message = msg

        return room

    async def wait(self):
        """Waits for the underlying view to stop.
        """
        if self.view is None:
            return
        await self.view.wait()

    async def add_participant(self, participant: discord.Member):
        """Adds a new participant to the game.
        Doesn't do anything if the member passed is already participating in the game.
        If the member is the first participant, makes them a host.

        Arguments:
            participant: The member to add

        Raises:
            RoomFilled if the room already contains maximal number of players.
            AlreadyParticipating if the user is already a part of other room.
        """
        if self.game.max_players and len(self.participants) == self.game.max_players:
            raise RoomFilled
        elif self.manager.check_user(participant):
            raise AlreadyParticipating
        
        if participant not in self.participants:
            self.participants.append(participant)

            if self.host is None:
                self.host = participant

    async def remove_participant(self, participant: discord.Member):
        """Removes the participant from the game.
        This function automatically reassigns room ownership in case the member to remove is the host.
        Doesn't do anything if the member passed is not participating in the game.
        
        Arguments:
            participant: The member to remove
        """
        if participant in self.participants:
            self.participants.remove(participant)

            if participant == self.host:
                if self.participants:
                    self.host = self.participants[0]
                else:
                    self.host = None
    

class RoomView(ui.View):
    def __init__(self, room: Room):
        super().__init__(timeout=600.0)
        self.room = room
        self.message: Optional[discord.Message] = None
        self.active_interaction: Optional[discord.Interaction] = None

    async def finalize(self, interaction: Optional[discord.Interaction] = None):
        self.clear_items()

        if self.room.state == RoomState.game_in_progress:
            label = "Игра начата"
        else:
            label = "Игра отменена"
        self.add_item(
                discord.ui.Button(
                    label=label, style=discord.ButtonStyle.grey, disabled=True
                )
        )
        
        if interaction:
            await interaction.response.edit_message(view=self, embed=self.render())
        else:
            assert self.message is not None
            await self.message.edit(view=self)

        self.active_interaction = interaction
        self.stop()

    def render(self) -> discord.Embed:
        description = self.room.game.description + " Начать игру может только ведущий, нажав на соответствующую кнопку."
        
        description += f"\n\n**Участники**:"
        if max_players := self.room.game.max_players:
            description += f" [{len(self.room.participants)}/{max_players}]"

        for player in self.room.participants:
            if player == self.room.host:
                description += "\n<:host:1009182501325000887>"
            else:
                description += "\n<:user:966009692117667882>"

            description += f" {player.mention}"

        embed = discord.Embed(
            title=self.room.game.emoji + " " + self.room.game.name,
            description=description,
            color=discord.Color(self.room.game.color)
        )

        return embed

    @ui.button(label="Присоединиться к игре", style=discord.ButtonStyle.green)
    async def entry(self, interaction: discord.Interaction, _):
        try:
            await self.room.add_participant(interaction.user)
        except RoomFilled:
            await interaction.response.send_message("<:error:1001451516969877504> Эта комната уже наполнена.", ephemeral=True)
        except AlreadyParticipating:
            await interaction.response.send_message("<:error:1001451516969877504> Вы уже участвуете в другой игре.", ephemeral=True)
        else:
            await interaction.response.edit_message(embed=self.render())

    @ui.button(label="Покинуть игру", style=discord.ButtonStyle.red)
    async def exit(self, interaction: discord.Interaction, _):
        if interaction.user == self.room.host:
            await interaction.response.send_message('Ведущий не может покинуть игру', ephemeral=True)
        elif interaction.user not in self.room.participants:
            await interaction.response.send_message('Вы не присоединялись к данной игре', ephemeral=True)
        else:
            await self.room.remove_participant(interaction.user)
            await interaction.response.edit_message(embed=self.render())

    @ui.button(
        label="Начать игру", 
        style=discord.ButtonStyle.blurple, 
        emoji="<:host:1009182501325000887>"
    )
    async def begin(self, interaction: discord.Interaction, _):
        if interaction.user == self.room.host:
            self.room.state = RoomState.game_in_progress
            await self.finalize(interaction)
        else:
            await interaction.response.send_message("Начать игру может только владелец комнаты.", ephemeral=True)
    
    @ui.button(
        label="Отменить игру", 
        style=discord.ButtonStyle.grey,
        emoji="<:host:1009182501325000887>"
    )
    async def cancel(self, interaction: discord.Interaction, _):
        if interaction.user == self.room.host:
            self.room.state = RoomState.inactive
            await self.finalize(interaction)
        else:
            await interaction.response.send_message("Отменить игру может только владелец комнаты.", ephemeral=True)

class RoomManager:
    def __init__(self):
        self.rooms: list[Room] = []

    def add(self, room: Room):
        self.rooms.append(room)

    def delete(self, room: Room):
        self.rooms.remove(room)

    def check_user(self, user: discord.Member) -> bool:
        for room in self.rooms:
            if user in room.participants:
                return True
        return False

    def __iter__(self):
        return iter(self.rooms)
