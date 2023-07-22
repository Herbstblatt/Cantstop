from itertools import cycle
import random
from collections import defaultdict
import copy
import asyncio
from typing import List, Union

import discord
from discord import ui

from .field import Field, Point
from .constants import *

class ForwardButton(ui.Button):
    view: "Game"
    
    def __init__(self, first_column, second_column=None, **kwards):
        super().__init__(style=discord.ButtonStyle.primary)
        self.first_column = first_column
        self.second_column = second_column

    def setup(self):
        self.first_column_ability = self.view.is_able_to_move(self.first_column)
        if self.second_column:
            self.second_column_ability = self.view.is_able_to_move(self.second_column)
        else:
            self.second_column_ability = None

        if self.second_column:
            if self.first_column_ability and self.second_column_ability:
                self.label = f"Continue on {self.first_column} and {self.second_column}"
            elif self.first_column_ability:
                self.label = f"Continue on {self.first_column}"
            elif self.second_column_ability:
                self.label = f"Continue on {self.second_column}"
            else:
                self.label = f"Continue on {self.first_column} and {self.second_column}"
                self.disabled = True
        else:
            self.label = f"Continue on {self.first_column}"
            if not self.first_column_ability:
                self.disabled = True

    async def callback(self, interaction):
        if interaction.user != self.view.current_player:
            await interaction.response.send_message("Nice try, but that's not your turn", ephemeral=True)
            return
        
        color = self.view.players_colors[self.view.current_player]

        if self.first_column == self.second_column:
            self.move_point(self.first_column, color, value=2)
        else:
            if self.first_column_ability:
                self.move_point(self.first_column, color)
            if self.second_column_ability:
                self.move_point(self.second_column, color)
            
        self.view.update_content()
        await self.view.ask_continue(interaction)

    def move_point(self, column, color, value=1):
        self.view.current_field[column].move(color, value=value)

        if column not in self.view.active_columns:
            self.view.active_columns.append(column)

        if self.view.current_field[column].taken:
            self.view.current_taken_columns[self.view.current_player] += 1

class StopButton(ui.Button):
    view: "Game"

    def __init__(self, **kwards):
        super().__init__(style=discord.ButtonStyle.grey, label="Stop")

    async def callback(self, interaction):
        if interaction.user != self.view.current_player:
            await interaction.response.send_message("Nice try, but that's not your turn", ephemeral=True)
            return
        await self.view.next_turn(interaction)

class ContinueButton(ui.Button):
    view: "Game"

    def __init__(self, **kwards):
        super().__init__(style=discord.ButtonStyle.blurple, label="Continue")

    async def callback(self, interaction):
        if interaction.user != self.view.current_player:
            await interaction.response.send_message("Nice try, but that's not your turn", ephemeral=True)
            return
        await self.view.continue_turn(interaction)

class Game(ui.View):
    children: List[Union[ForwardButton, StopButton, ContinueButton]]

    def __init__(self, players):
        super().__init__(timeout=None)
        random.shuffle(players)
        self.players_order = cycle(players)
        self.current_player = next(self.players_order)

        points = [Point(key) for key in POINTS.keys()]
        random.shuffle(points)
        self.players_colors = dict(zip(players, points))

        self.field = Field()
        self.current_field = copy.deepcopy(self.field)
        self.taken_columns = defaultdict(int)
        self.current_taken_columns = copy.copy(self.taken_columns)
        self.active_columns = []

        self.update_content()
        self.add_forward_buttons()
        
    def update_content(self):    
        self.content = "Players:\n"
        for player, color in self.players_colors.items():
            if player == self.current_player:
                self.content += ACTIVE_PLAYER
            else:
                self.content += NOTHING
            self.content += f" {str(player)} ({self.taken_columns[player]} {POINTS[color.value]})\n"
        self.content += f"\nColumns that {self.current_player} is on now: "
        self.content += ", ".join([str(col) for col in self.active_columns])
        self.content += "\n"
        self.content += self.current_field.render()

    def roll_dice(self):
        dice = [random.randint(1, 6) for i in range(4)]
        self.content += "\n\n"
        self.content += " ".join([DICE[n] for n in dice])
        return dice

    def add_forward_buttons(self):
        dice = self.roll_dice()
        self.clear_items()
        variants = [
            [dice[0] + dice[1], dice[2] + dice[3]],
            [dice[0] + dice[2], dice[1] + dice[3]],
            [dice[0] + dice[3], dice[1] + dice[2]]
        ]
        if len(self.active_columns) != 2:
            self.add_item(ForwardButton(*variants[0]))
            self.add_item(ForwardButton(*variants[1]))
            self.add_item(ForwardButton(*variants[2]))
        else:
            for variant in variants:
                if (variant[0] in self.active_columns) or (variant[1] in self.active_columns):
                    self.add_item(ForwardButton(*variant))
                else:
                    self.add_item(ForwardButton(variant[0]))
                    self.add_item(ForwardButton(variant[1]))
        
        for child in self.children:
            assert isinstance(child, ForwardButton)
            child.setup()

    def is_able_to_move(self, column):
        if self.current_field[column].taken:
            return False
        if len(self.active_columns) <= 2:
            return True
        return column in self.active_columns

    def check_winner(self):
        for player, columns in self.current_taken_columns.items():
            if columns >= 3:
                return player

    async def ask_continue(self, interaction):
        self.clear_items()
        self.add_item(ContinueButton(style=discord.ButtonStyle.blurple))
        self.add_item(StopButton(style=discord.ButtonStyle.grey))
        await interaction.response.edit_message(view=self, content=self.content)

    async def check_turn_ability(self, interaction):
        if all(child.disabled for child in self.children):
            await asyncio.sleep(2)
            await self.next_turn(interaction, reset=True)

    async def continue_turn(self, interaction):
        if winner := self.check_winner():
            await self.finalize(interaction, winner)
            return
        
        self.add_forward_buttons()
        await interaction.response.edit_message(view=self, content=self.content)
        await self.check_turn_ability(interaction)

    async def next_turn(self, interaction: discord.Interaction, *, reset: bool = False):
        if winner := self.check_winner():
            await self.finalize(interaction, winner)
            return

        if not reset:
            self.field = self.current_field
            self.taken_columns = self.current_taken_columns

        self.current_field = copy.deepcopy(self.field)
        self.current_taken_columns = copy.copy(self.taken_columns)
        self.current_player = next(self.players_order)

        self.active_columns = []
        self.update_content()
        self.add_forward_buttons()
        if not reset:
            await interaction.response.edit_message(view=self, content=self.content)
        else:
            await interaction.edit_original_response(view=self, content=self.content)

        await self.check_turn_ability(interaction)

    async def finalize(self, interaction, winner):
        self.clear_items()
        self.current_player = None
        self.taken_columns = self.current_taken_columns
        self.update_content()
        
        await interaction.response.edit_message(view=self, content=self.content)
        await interaction.followup.send(f"The game has ended! {winner.mention} won! :tada:")
        self.stop()


