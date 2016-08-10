import events
import include
import model
import os
import pygame
import sprites

from battle import *
from board import *
from cocos.director import director
from random import randint

from resources import Resources

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

mech_list = []

for root, dirs, f_names in os.walk(DATA_DIR+'/mechs/'):
    for f_name in f_names:
        mech = include.IncludeLoader(open(os.path.join(root, f_name), 'r')).get_data()
        print("Loaded %s:" % mech.full_name())
        print("  " + str(mech))
        mech_list.append(mech)

# sort list alphabetically by name
mech_list = sorted(mech_list, key=lambda x: x.name)

# director must be initialized before any cocos elements can be created
director.init(width=480, height=400, resizable=True, autoscale=False)
director.show_FPS = True
board = Board()
battle = Battle()
battle.setBoard(board)
key_events = events.KeyboardEvents(battle)
mouse_events = events.MouseEvents(battle)

# initialize the audio mixer
pygame.mixer.init(44100, -16, 2, 2048)
pygame.mixer.set_num_channels(32)

# fill out the test board with mechs
col = randint(0, battle.getNumCols())
row = randint(0, battle.getNumRows())

for mech in mech_list:
    while not battle.isCellAvailable(col, row):
        col = randint(0, battle.getNumCols()-1)
        row = randint(0, battle.getNumRows()-1)

    battle_mech = BattleMech(mech, col, row)
    battle.addUnit(battle_mech)

    sprite = sprites.MechSprite(battle_mech)
    battle_mech.setSprite(sprite)
    # TODO: Z order should be based on the number of rows in the board
    sprite_z = (battle.getNumRows() - row) * 10
    board.add(sprite.indicator, z=sprite_z)
    board.add(sprite.shadow, z=sprite_z+1)
    board.add(sprite, z=sprite_z+2)

# only sulk during the unit's turn
next_unit = battle.getTurnUnit()
next_unit.sprite.sulk()
next_unit.sprite.indicator.visible = True

scroller = cocos.layer.ScrollingManager()
scroller.add(board, z=0)
scroller.add(key_events, z=-1)
scroller.add(mouse_events, z=1)

battle.setScroller(scroller)

# TODO: focus on an actual unit
scroller.set_focus(150, 150)

scene = cocos.scene.Scene()
scene.add(scroller, z=1)

# preload all sound and image resources
Resources.preload()

director.run(scene)
