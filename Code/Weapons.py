# Weapons.py
import GlobalConstants as GC
import configuration as cf
import Engine

# === WEAPON TRIANGLE OBJECT ==================================================
class Weapon_Triangle(object):
    def __init__(self, fn):
        self.types = []
        self.advantage = {}
        self.disadvantage = {}
        self.name_to_index = {}
        self.index_to_name = {}
        self.magic_types = set()

        self.parse_file(fn)

    def number(self):
        return len(self.types)

    def parse_file(self, fn):
        with open(fn) as fp:
            lines = fp.readlines()

        for index, line in enumerate(lines):
            split_line = line.strip().split(';')
            name = split_line[0]
            advantage = split_line[1].split(',')
            disadvantage = split_line[2].split(',')
            magic = True if split_line[3] == 'M' else False
            # Ascend
            self.types.append(name)
            self.name_to_index[name] = index
            self.index_to_name[index] = name
            self.advantage[name] = advantage
            self.disadvantage[name] = disadvantage
            if magic:
                self.magic_types.add(name)

        self.name_to_index['Consumable'] = len(lines)
        self.index_to_name[len(lines)] = 'Consumable'

    def compute_advantage(self, weapon1, weapon2):
        """ Returns two-tuple describing advantage """
        if not weapon1 and not weapon2:
            return (0, 0) # If either does not have a weapon, neither has advantage
        if not weapon1:
            return (0, 2)
        if not weapon2:
            return (2, 0)
        if weapon1.ignore_weapon_advantage or weapon2.ignore_weapon_advantage:
            return (0, 0)

        weapon1_advantage, weapon2_advantage = 0, 0
        if weapon2.TYPE in self.advantage[weapon1.TYPE]:
            weapon1_advantage += 1
        if weapon2.TYPE in self.disadvantage[weapon1.TYPE]:
            weapon1_advantage -= 1
        if weapon1.TYPE in self.advantage[weapon2.TYPE]:
            weapon2_advantage += 1
        if weapon1.TYPE in self.disadvantage[weapon2.TYPE]:
            weapon2_advantage -= 1

        # Handle reverse (reaver) weapons
        if weapon1.reverse or weapon2.reverse:
            return (-2*weapon1_advantage, -2*weapon2_advantage)
        else:
            return (weapon1_advantage, weapon2_advantage)

    def isMagic(self, item):
        if item.magic or item.magic_at_range or item.TYPE in self.magic_types:
            return True
        return False

class Weapon_Advantage(object):
    class Advantage(object):
        def __init__(self, damage, resist, accuracy, avoid, crit, evade, attackspeed):
            self.damage = damage
            self.resist = resist
            self.accuracy = accuracy
            self.avoid = avoid
            self.crit = crit
            self.evade = evade
            self.attackspeed = attackspeed

    def __init__(self, fn):
        self.wadv_dict = {}
        self.parse_file(fn)

    def parse_file(self, fn):
        with open(fn) as fp:
            lines = [l.strip() for l in fp.readlines()]

        for index, line in enumerate(lines):
            if line.startswith('#'):
                continue
            split_line = line.split()
            weapon_type = split_line[0]
            weapon_rank = split_line[1]
            stats = [int(x) for x in split_line[2:]]
            if weapon_type not in self.wadv_dict:
                self.wadv_dict[weapon_type] = {}
            self.wadv_dict[weapon_type][weapon_rank] = self.Advantage(*stats)

        assert 'All' in self.wadv_dict
        assert 'All' in self.wadv_dict['All']

    def get_advantage(self, weapon, wexp):
        if weapon:
            weapon_type = weapon.TYPE
            weapon_wexp = wexp[TRIANGLE.name_to_index[weapon.TYPE]]
            weapon_rank = EXP.number_to_letter(weapon_wexp)
            if weapon_type in self.wadv_dict:
                if weapon_rank in self.wadv_dict[weapon_type]:
                    return self.wadv_dict[weapon_type][weapon_rank]
                else:
                    return self.wadv_dict[weapon_type]['All']
            else:
                if weapon_rank in self.wadv_dict['All']:
                    return self.wadv_dict['All'][weapon_rank]
                else:
                    return self.wadv_dict['All']['All']
        else:
            return 0

    def get_disadvantage(self, weapon, wexp):
        if cf.CONSTANTS['weapon_adv_flip']:
            return self.get_advantage(weapon, wexp)
        else:
            return 0

class Weapon_Exp(object):
    def __init__(self, fn):
        self.wexp_dict = {}
        self.sorted_list = []
        self.parse_file(fn)

    def parse_file(self, fn):
        with open(fn) as fp:
            lines = fp.readlines()

        for index, line in enumerate(lines):
            split_line = line.strip().split(';')
            letter = split_line[0]
            number = int(split_line[1])
            self.wexp_dict[letter] = number

        self.sorted_list = sorted(self.wexp_dict.items(), key=lambda x: x[1])

    def number_to_letter(self, wexp):
        current_letter = "--"
        for letter, number in self.sorted_list:
            if wexp >= number:
                current_letter = letter
            else:
                break
        return current_letter

    # Returns a float between 0 and 1 desribing how closes number is to next tier from previous tier
    def percentage(self, wexp):
        current_percentage = 0.0
        # print(wexp, self.sorted_list)
        for index, (letter, number) in enumerate(self.sorted_list):
            if index + 1 >= len(self.sorted_list):
                current_percentage = 1.0
                break
            elif wexp >= number:
                difference = float(self.sorted_list[index+1][1] - number)
                if wexp - number >= difference:
                    continue
                current_percentage = (wexp - number)/difference
                # print('WEXP', wexp, number, difference, current_percentage)
                break
        return current_percentage

class Icon(object):
    def __init__(self, name=None, idx=None, grey=False):
        if name:
            self.name = name
            self.idx = TRIANGLE.name_to_index[self.name]
        else:
            self.name = None
            self.idx = idx
        self.set_grey(grey)

    def set_grey(self, grey):
        self.grey = grey
        self.create_image()

    def create_image(self):
        # Weapon Icons Pictures
        if self.grey:
            weaponIcons = GC.ITEMDICT['Gray_Wexp_Icons']
        else:
            weaponIcons = GC.ITEMDICT['Wexp_Icons']
        self.image = Engine.subsurface(weaponIcons, (0, 16*self.idx, 16, 16))

    def draw(self, surf, topleft, cooldown=False):
        surf.blit(self.image, topleft)

TRIANGLE = Weapon_Triangle(Engine.engine_constants['home'] + "Data/weapon_triangle.txt")
EXP = Weapon_Exp(Engine.engine_constants['home'] + "Data/weapon_exp.txt")
ADVANTAGE = Weapon_Advantage(Engine.engine_constants['home'] + 'Data/weapon_advantage.txt')
