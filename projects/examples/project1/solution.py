"""
Clone of 2048 game.
"""
import random      
    
# Directions, DO NOT MODIFY
UP = 1
DOWN = 2
LEFT = 3
RIGHT = 4

# Offsets for computing tile indices in each direction.
# DO NOT MODIFY this dictionary.    
OFFSETS = {UP: (1, 0), 
           DOWN: (-1, 0), 
           LEFT: (0, 1), 
           RIGHT: (0, -1)} 
   
def merge(line):
    """
    Helper function that merges a single row or column in 2048
    """
    result = [0] * len(line)
    merged = False
    pos = 0
    for tile in line:
        if tile > 0:
            if pos == 0:
                result[pos] = tile
                pos += 1
            elif not merged and tile == result[pos-1]:
                result[pos-1] *= 2
                merged = True
            else:
                result[pos] = tile
                merged = False
                pos += 1
    return result
