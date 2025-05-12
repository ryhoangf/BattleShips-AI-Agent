import random

class Ship:
    def __init__(self, size):
        self.size = size
        self.row = random.randrange(0,9)
        self.col = random.randrange(0,9)
        self.orientation = random.choice(["h", "v"])
        self.indexes = self.compute_indexes()
    
    def compute_indexes(self):
        start_index = self.row * 10 + self.col
        if self.orientation == "h":
            return [start_index + i for i in range(self.size)]
        elif self.orientation == "v":
            return [start_index + i*10 for i in range(self.size)]

s = Ship(size = 3)
print(s. row)
print(s.col)
print(s.orientation)
print(s.indexes)