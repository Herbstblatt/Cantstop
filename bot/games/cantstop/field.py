import enum
from contextlib import suppress
from .constants import *

class Point(enum.Enum):
    red = "red"
    yellow = "yellow"
    blue = "blue"
    green = "green"

def find_overlap(*colors):
    colors = [color.value for color in colors]
    for item in OVERLAPS:
        if sorted(item["colors"]) == sorted(colors):
            return item["value"]

class Field:
    def __init__(self):
        self._columns = {}
        for i in range(5):
            self._columns[i+2] = Column(length=3+i*2)
            self._columns[12 - i] = Column(length=3+i*2)
        self._columns[7] = Column(length=13)
    
    def __getitem__(self, key):
        return self._columns[key]

    def __iter__(self):
        return iter(self._columns)

    def render(self):
        rendered_columns = []
        for idx, column in sorted(self._columns.items()):
            if column.taken:
                rendered_column = ([POINTS[column[-1][0].value]] * len(column)) + ([SQUARE] * (13 - len(column)))
            else:
                rendered_column = []
                for item in column[:-1]:
                    if len(item) == 0:
                        rendered_column.append(NOTHING)
                    elif len(item) == 1:
                        rendered_column.append(POINTS[item[0].value])
                    else:
                        rendered_column.append(find_overlap(*item))
                rendered_column.append(NUMBERS[idx])
                while len(rendered_column) < 13:
                    rendered_column.append(SQUARE)

            rendered_column.reverse()
            rendered_columns.append(rendered_column)

        rendered_rows = list(zip(*rendered_columns))
        rendered_rows = [" ".join(item) for item in rendered_rows]
        return "\n".join(rendered_rows)

class Column:
    def __init__(self, length):
        self.length = length
        self._column = [[] for i in range(length)]
    
    def __repr__(self):
        return f"<Column length={self.length}>"

    def __getitem__(self, key):
        return self._column[key]

    def __len__(self):
        return self.length

    @property
    def taken(self):
        return len(self._column[-1]) > 0

    def move(self, point, value=1):
        if self.taken: # if the column is taken, we cannot move
            return
        
        for i, item in enumerate(self._column):
            if point in item:
                if (i + value) > (self.length - 1): # if the column is taken, we cannot move
                    return
                item.remove(point)
                self._column[i + value].append(point)
                return
        
        self._column[value - 1].append(point)