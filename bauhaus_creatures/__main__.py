#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Oliver Zeit
Description:
    Generates images with 3x3 "bauhaus creatures".
'''

import argparse as AP
import os
from PIL import Image
import random
import sys
import time

"""
Grid:

0 1 2
3 4 5
6 7 8

n ... north
e ... east
s ... south
w ... west

Read:
    "0s": 3
as:
    "If you are on position 0 and going s (south), you land on position 3"
"""
MOVEMENTS = {
        "0e": 1,
        "0s": 3,
        "1e": 2,
        "1s": 4,
        "1w": 0,
        "2s": 5,
        "2w": 1,
        "3n": 0,
        "3e": 4,
        "3s": 6,
        "4n": 1,
        "4e": 5,
        "4s": 7,
        "4w": 3,
        "5n": 2,
        "5s": 8,
        "5w": 4,
        "6n": 3,
        "6e": 7,
        "7n": 4,
        "7e": 8,
        "7w": 6,
        "8n": 5,
        "8w": 7
}

def valid_moves(position):
    return sorted([direction[1] for direction in MOVEMENTS.keys() if int(direction[0]) == position])

def valid_constrained_moves(position, last_pos):
    return [move[1] for move in MOVEMENTS.keys() if move.startswith(str(last_pos)) and MOVEMENTS[move] == position]


def next(position, directions):
    return set([MOVEMENTS[key] for key in [str(position) + dr for dr in directions if str(position) + dr in MOVEMENTS]])

CREATURE_DIM = 3
TILES_PER_CREATURE = CREATURE_DIM * CREATURE_DIM
class Algo(object):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo

    def creature(self):
        stack = set()
        last_pos = -1
        position = 4 #random.choice(range(TILES_PER_CREATURE))
        tile_positions = {}
        tile_count = 0
        while True:
            moves = valid_moves(position)
            if last_pos != -1:
                moves = valid_constrained_moves(position, last_pos)
            possible_tiles = self.repo.all_tiles_supporting(moves)
            if not possible_tiles and not stack:
                break
            tile = None
            if possible_tiles:
                tile = random.choice(possible_tiles)
                tile_positions[position] = tile
                tile_count += 1
            # if rand() < (#leftoverspots / #totalspots) -> continue
            if tile_count >= 3 and (random.random() >= ((TILES_PER_CREATURE - len(tile_positions.keys())) / float(TILES_PER_CREATURE))):
                break
            if tile:
                stack |= next(position, tile.connectors)
            if stack:
                last_pos = position
                position = random.choice(list(stack))
                stack.discard(position)
        return Creature(tile_positions)

    def render(self, size, pad=0):
        tilesize = self.repo.tilesize()
        creature_size = CREATURE_DIM * tilesize + 2 * pad
        size_px = tuple([creature_size * dim for dim in size])
        img = Image.new('RGBA', size_px)
        for x in range(size[0]):
            for y in range(size[1]):
                creature = self.creature()
                img.paste(creature.render(pad), (x * creature_size, y * creature_size))
        return img

class Creature(object):
    def __init__(self, tile_positions):
        super().__init__()
        self._tile_positions = tile_positions
        self.tilesize = list(tile_positions.values())[0].image.size[0]

    def _offsets(self, position, tilesize):
        return [(position % 3) * tilesize, (position // 3) * tilesize]

    def render(self, pad=0):
        tilesize = self.tilesize
        img = Image.new('RGBA', (3 * tilesize + 2 * pad, 3 * tilesize + 2 * pad))
        for pos, tile in self._tile_positions.items():
            tilesize = tile.image.size[0]
            offsets = [offset + pad for offset in self._offsets(pos, tilesize)]
            img.paste(tile.image, offsets)
        return img

class Tile(object):
    def __init__(self, filepath):
        super().__init__()
        parts = filepath.split('/')[-1].split('.')[0].split('_')
        self.name = parts[0]
        self.image = Image.open(filepath)
        self.connectors = set(parts[1])

    def __str__(self):
        return '%s(%s)' % (self.name, ''.join(self.connectors))


class TileRepository(object):
    def __init__(self, location):
        super().__init__()
        tile_files = []
        for (dirpath, dirnames, filenames) in os.walk(location):
            tile_files.extend([dirpath + fn for fn in filenames])
            break
        self.tiles = [Tile(filepath) for filepath in tile_files]
        for tile in self.tiles:
            print(tile)

    def tilesize(self):
        return self.tiles[0].image.size[0]

    def all_tiles_supporting(self, directions):
        tiles = []
        directions = set(directions)
        for tile in self.tiles:
            if bool(tile.connectors & directions):
                tiles.append(tile)
        return tiles


def main(args):
    tile_repo = TileRepository('tiles/')
    for pos in range(9):
        print(valid_moves(pos))
    print(tile_repo.tilesize())
    algo = Algo(tile_repo)
    img = algo.render(args.dimension, args.padding)
    img.save(args.output)


if __name__ == "__main__":
    parser = AP.ArgumentParser(description="Greeter program.")
    parser.add_argument("-v", "--verbose",
                        action="store_true", default=False,
                        help="Verbose output.")
    parser.add_argument("-d", "--dimension",
                        type=str, default="35x17",
                        help="Size of the image in creatures (each creatures is 3x3 tiles large).")
    parser.add_argument("-o", "--output",
                        type=str, default=None,
                        help="Output filename. Default: <width>x<height>x<seed>.")
    parser.add_argument("-p", "--padding",
                        type=int, default=0,
                        help="Pads each creature with this amount of pixels in every direction.")
    parser.add_argument("-s", "--seed",
                        type=int, default=None,
                        help="Seed for the RNG, default is invocation time based. If no seed is provided, the used seed gets printed to STDOUT.")
    args = parser.parse_args()

    if args.seed is None:
        args.seed = int(time.time())
        print(args.seed)
    if args.output is None:
        args.output = args.dimension + "x" + str(args.seed) + ".png"
    args.dimension = [int(dim) for dim in args.dimension.split("x")]
    random.seed(args.seed)

    main(args)
