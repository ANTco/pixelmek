import model

from board import Board
from cocos.director import director
from cocos.euclid import Point2
from cocos.rect import Rect
from ui import Interface


class Battle(object):
    RANGE_SHORT = 6
    RANGE_MEDIUM = 24
    RANGE_LONG = 42

    BATTLE = None

    def __init__(self):
        Battle.BATTLE = self
        self.board = None
        self.scroller = None

        self.player_list = []

        self.unit_list = []
        self.unit_turn = -1

        self.sel_cell_pos = None

    def setBoard(self, board):
        self.board = board

    def setScroller(self, scroller):
        self.scroller = scroller

    def addUnit(self, battle_unit):
        self.unit_list.append(battle_unit)

    def updateUnitsTurnOrder(self):
        # TODO: implement a better way to determine initiative for unit turn order
        self.unit_list = sorted(self.unit_list, key=lambda x: x.getTurnMove(), reverse=True)

    def addPlayer(self, player):
        self.player_list.append(player)

    def clearSelectedCell(self):
        prev_cell = self.getSelectedCell()
        if prev_cell is not None:
            prev_cell.remove_indicators()

        self.sel_cell_pos = None

    def setSelectedCellPosition(self, col, row):
        if col < 0 or row < 0 or col >= Board.numCols or row >= Board.numRows:
            return

        prev_cell = self.getSelectedCell()
        if prev_cell is not None:
            prev_cell.show_action_indicator(show=False)
            prev_cell.show_range_to_display(show=False)

        self.sel_cell_pos = col, row
        new_cell = self.getSelectedCell()

        if new_cell is not None:
            new_cell.show_action_indicator()
            new_cell.show_range_to_display()

            cell_unit = self.getUnitAtCell(col, row)
            if cell_unit == self.getTurnUnit():
                Interface.UI.updateTargetUnitStats(None)
            else:
                Interface.UI.updateTargetUnitStats(cell_unit,
                                                   is_friendly=self.isFriendlyUnit(self.getTurnPlayer(), cell_unit))

            # only refocus if getting too close to edge of display (within 3 Tiles of each side)
            window_size = director.get_window_size()
            view_width = window_size[0] - Board.BOARD.TILE_SIZE * 6
            view_height = window_size[1] - Board.BOARD.TILE_SIZE * 6

            view_bottom_left = self.scroller.screen_to_world(Board.BOARD.TILE_SIZE * 3, Board.BOARD.TILE_SIZE * 3)
            view_rect = Rect(view_bottom_left[0], view_bottom_left[1], view_width, view_height)

            cell_screen_pos = Board.board_to_layer(col, row)
            cell_rect = Rect(cell_screen_pos[0], cell_screen_pos[1], Board.BOARD.TILE_SIZE, Board.BOARD.TILE_SIZE)

            if not cell_rect.intersects(view_rect):
                self.scroller.set_focus(cell_screen_pos[0] + Board.BOARD.TILE_SIZE // 2,
                                        cell_screen_pos[1] + Board.BOARD.TILE_SIZE // 2)

    def getSelectedCellPosition(self):
        return self.sel_cell_pos

    def getSelectedCell(self):
        if self.sel_cell_pos is None:
            return None

        return self.board.get_cell(*self.sel_cell_pos)

    def getTurnPlayer(self):
        turn_unit = self.getTurnUnit()
        if turn_unit is None:
            return None

        return turn_unit.getPlayer()

    def getTurnUnit(self):
        if self.unit_turn < 0:
            return None

        return self.unit_list[self.unit_turn]

    def isTurnUnit(self, battle_unit):
        return battle_unit is not None and battle_unit is self.getTurnUnit()

    def getTurnUnitCell(self):
        turn_unit = self.getTurnUnit()
        if turn_unit is not None:
            return self.getCellAt(turn_unit.col, turn_unit.row)

    def isTurnUnitCell(self, cell):
        turn_unit = self.getTurnUnit()
        if turn_unit is not None and cell is not None:
            turn_unit_cell = self.getTurnUnitCell()
            return cell is turn_unit_cell

        return False

    def getUnitCell(self, battle_unit):
        if battle_unit is None:
            return None

        return self.board.get_cell(battle_unit.col, battle_unit.row)

    def nextTurn(self):
        prev_unit = self.getTurnUnit()
        if prev_unit is not None:
            prev_unit.sprite.stop()

        for cell in self.board.cellMap.itervalues():
            cell.remove_indicators()

        self.unit_turn += 1
        if self.unit_turn >= len(self.unit_list):
            self.unit_turn = 0

        next_unit = self.getTurnUnit()

        if next_unit.isDestroyed():
            while next_unit.isDestroyed():
                self.unit_turn += 1
                if self.unit_turn >= len(self.unit_list):
                    self.unit_turn = 0

                next_unit = self.getTurnUnit()

        # initialize the unit for its next turn
        # TODO: account for critical and heat effects on move
        next_unit.move = next_unit.mech.move

        next_unit.sprite.sulk()

        self.showRangeIndicators()
        self.showUnitIndicators()

        self.setSelectedCellPosition(next_unit.col, next_unit.row)

        turn_cell_pos = Board.board_to_layer(next_unit.col, next_unit.row)
        if turn_cell_pos is not None:
            turn_cell_pos = turn_cell_pos[0] + Board.TILE_SIZE // 2, turn_cell_pos[1] + Board.TILE_SIZE // 2

        self.scroller.set_focus(*turn_cell_pos)

        Interface.UI.updatePlayerUnitStats(next_unit)

    def showRangeIndicators(self):
        turn_unit = self.getTurnUnit()
        cells_in_range = self.getCellsInRange(turn_unit.col, turn_unit.row, turn_unit.move)
        for cell_pos in cells_in_range:
            cell = self.getCellAt(*cell_pos)
            cell_range = cells_in_range[cell_pos]
            if self.isCellAvailable(*cell_pos):
                cell.show_move_indicator()
                cell.range_to_display = cell_range
            elif self.isTurnUnitCell(cell):
                cell.show_player_indicator()

    def showUnitIndicators(self, visible=True):
        for battle_unit in self.unit_list:
            show_indicator = visible and not self.isTurnUnit(battle_unit)
            battle_unit.sprite.showIndicator(visible=show_indicator)

    def getCellsInRange(self, col, row, max_dist):
        cells = {}
        self._recurseCellsInRange(col, row, 0, max_dist, cells)
        return cells

    def _recurseCellsInRange(self, col, row, dist, max_dist, cells):
        cell = (col, row)
        if dist > max_dist or (cell in cells and dist >= cells[cell]) \
                or col < 0 or row < 0 or col >= Board.numCols or row >= Board.numRows:
            return

        if dist >= 0:
            cells[cell] = dist

        # TODO: distinguish between LOS related range and move related range recursion

        # allow passing through friendly unit occupied cells
        turn_unit = self.getTurnUnit()
        turn_player = turn_unit.getPlayer()

        cell_unit = self.getUnitAtCell(col, row)
        is_friendly_occupied = False
        if cell_unit is not None:
            is_friendly_occupied = self.isFriendlyUnit(turn_player, cell_unit)

        if dist == 0 or self.isCellAvailable(col, row) or \
                (cell_unit is not None and is_friendly_occupied):
            self._recurseCellsInRange(col, row + 1, dist + 1, max_dist, cells)
            self._recurseCellsInRange(col, row - 1, dist + 1, max_dist, cells)
            self._recurseCellsInRange(col + 1, row, dist + 1, max_dist, cells)
            self._recurseCellsInRange(col - 1, row, dist + 1, max_dist, cells)

    def isCellAvailable(self, col, row):
        if self.board is None:
            return False

        if col < 0 or row < 0 or col >= self.board.numCols or row >= self.board.numRows:
            return False

        # check to see if any units occupy the space
        for battle_unit in self.unit_list:
            if battle_unit.col == col and battle_unit.row == row \
                    and not battle_unit.isDestroyed():
                return False

        loc = (col, row)
        cell_data = self.board.boardMap.get(loc)

        if cell_data is None:
            return True

        # TODO: check cell data to see if it is passable terrain object, such as trees, rocks, etc

        return False

    def getCellAt(self, col, row):
        return self.board.get_cell(col, row)

    def getUnitAtCell(self, col, row):
        if self.board is None:
            return None

        if col < 0 or row < 0 or col >= Board.numCols or row >= Board.numRows:
            return None

        # find the unit that occupies the space
        for battle_unit in self.unit_list:
            if battle_unit.col == col and battle_unit.row == row \
                    and not battle_unit.isDestroyed():
                return battle_unit

        return None

    @staticmethod
    def getNumRows():
        return Board.numRows

    @staticmethod
    def getNumCols():
        return Board.numCols

    @staticmethod
    def getCellDistance(cell_1, cell_2):
        point_1 = Point2(cell_1[0], cell_1[1])
        point_2 = Point2(cell_2[0], cell_2[1])

        return point_1.distance(point_2)

    @staticmethod
    def getDistanceRange(cell_distance):
        if cell_distance <= Battle.RANGE_SHORT:
            return model.Weapon.RANGE_SHORT

        elif cell_distance <= Battle.RANGE_MEDIUM:
            return model.Weapon.RANGE_MEDIUM

        elif cell_distance <= Battle.RANGE_LONG:
            return model.Weapon.RANGE_LONG

        return model.Weapon.RANGE_EXTREME

    @staticmethod
    def isFriendlyUnit(player, battle_unit):
        if player is None or battle_unit is None \
                or player.team == -1:
            return False

        return player.team == battle_unit.getTeam()

    @staticmethod
    def isEnemyUnit(player, battle_unit):
        return not Battle.isFriendlyUnit(player, battle_unit)


class BattleMech(object):
    def __init__(self, player, mech, col, row):
        self.player = player
        self.mech = mech
        self.sprite = None

        # setup values which are dynamic in battle
        self.col = col
        self.row = row

        self.skill = mech.skill
        self.move = mech.move
        self.jump = mech.get_jump()
        self.short = mech.short
        self.medium = mech.medium
        self.long = mech.long

        self.heat = 0
        self.shutdown = False

        self.armor = int(mech.armor)
        self.structure = int(mech.structure)

        # critical hit effects
        self.crit_engine = 0    # +1 Heat when weapons fire, 2nd hit: Unit destroyed
        self.crit_mp = 0        # 1/2 Move (MV), minimum loss of 2 MV each, can be 0 (immobile)
        self.crit_to_hit = 0    # +2 To-Hit each for weapons fire
        self.crit_weapons = 0   # -1 Damage each for weapons fire

    def __repr__(self):
        return "%s(name='%s %s', location=[%s,%s])" % (
            self.__class__.__name__, self.mech.name, self.mech.variant, self.col, self.row
        )

    def getPlayer(self):
        return self.player

    def getTeam(self):
        if self.player is None:
            return -1

        return self.player.team

    def setSprite(self, sprite):
        self.sprite = sprite

    def getName(self):
        return self.mech.name

    def getVariant(self):
        return self.mech.variant

    def getSprite(self):
        return self.sprite

    def getImagePath(self):
        return self.mech.image_path

    def getSize(self):
        return self.mech.size

    def getTurnMove(self):
        turn_move = self.mech.move

        if self.crit_mp > 0:
            # reduce move based on critical hits
            for i in range(self.crit_mp):
                if turn_move > 0:
                    move_reduce = round(turn_move / 2.0)
                    if move_reduce < 2.0:
                        # minimum of 2 MV reduction per critical
                        move_reduce = 2.0

                    turn_move -= int(move_reduce)

        if self.heat > 0:
            # reduce move based on heat
            turn_move -= (self.heat * 2)

        if turn_move < 0:
            return 0

        return turn_move

    def getTurnJump(self):
        return self.mech.get_jump()

    def isDestroyed(self):
        return self.structure <= 0

    def isShutdown(self):
        return self.shutdown

    def applyDamage(self, damage):
        # returns a number >0 only if there is excess damage after being destroyed
        if damage <= 0:
            return 0
        elif self.armor == 0 and self.structure == 0:
            return damage

        remaining_damage = damage

        if self.armor > 0:
            if remaining_damage > self.armor:
                # all armor will be destroyed
                remaining_damage -= self.armor
                self.armor = 0
            else:
                # only some armor is destroyed
                self.armor -= remaining_damage
                remaining_damage = 0

        if remaining_damage > 0 and self.structure > 0:
            if remaining_damage > self.structure:
                # all structure will be destroyed
                remaining_damage -= self.structure
                self.structure = 0
            else:
                # only some structure is destroyed
                self.structure -= remaining_damage
                remaining_damage = 0

        return remaining_damage


class Player(object):

    def __init__(self, callsign, team=-1, is_bot=False):
        self.callsign = callsign
        self.team = team
        self.is_bot = is_bot
