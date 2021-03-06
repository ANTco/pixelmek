import cocos
import pyglet
import settings
import actions

from battle import Battle
from cocos.director import director
from cocos.menu import *
from cocos.scenes import *
from ui import Interface


class MainMenu(Menu):
    def __init__(self, scroller):
        super(MainMenu, self).__init__("PixelMek")

        self.scroller = scroller

        self.font_title['font_name'] = 'Convoy'
        self.font_title['font_size'] = 50
        self.font_item['font_name'] = 'Convoy'
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = 'Convoy'
        self.font_item_selected['font_size'] = 40

        menus = []

        battle_item = MenuItem('Battle', self.on_battle)
        menus.append(battle_item)

        settings_item = MenuItem('Settings', self.on_settings)
        menus.append(settings_item)

        exit_item = MenuItem('Exit', self.do_exit)
        menus.append(exit_item)

        self.create_menu(menus)

    def on_battle(self):
        print("Battle!")
        scene = cocos.scene.Scene()
        scene.add(self.scroller)
        scene.add(Interface.UI)
        director.push(scene)

        Battle.BATTLE.nextTurn()
        actions.setActionReady(True)

    def on_settings(self):
        print("Settings...")
        scene = cocos.scene.Scene()
        scene.add(settings.SettingsMenu())
        director.push(FlipX3DTransition(scene, duration=0.5))

    def do_exit(self):
        print("Quitter!")
        pyglet.app.exit()

    def on_quit(self):
        print("Back to the game if it's on...")
