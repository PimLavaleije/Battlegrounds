import copy
from game.data.minions import ALL_MINIONS, TOKENS


def _safe_stat(value, default=0):
    """Return an int-like stat value. Spreadsheet blanks/None become 0 so gameplay code does not crash."""
    if value is None:
        return default
    return value


class Minion:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.tier = data["tier"]
        self.tribe = data.get("tribe")
        self.types = list(data.get("types", []))
        if not self.types and self.tribe:
            self.types = [t.strip() for t in self.tribe.split("/")]
        self.token = data.get("token", False)

        # Some generated spreadsheet rows can have missing stats, for example Egg of the Endtimes.
        # The game engine expects numeric stats, so normalize missing values to 0.
        self.base_attack = _safe_stat(data.get("attack"), 0)
        self.base_health = _safe_stat(data.get("health"), 0)
        self.attack = _safe_stat(data.get("attack"), 0)
        self.health = _safe_stat(data.get("health"), 0)
        self.max_health = _safe_stat(data.get("health"), 0)

        self.abilities = list(data.get("abilities", []))
        self.taunt = "taunt" in self.abilities
        self.divine_shield = "divine_shield" in self.abilities
        self.reborn = "reborn" in self.abilities
        self.poisonous = "poisonous" in self.abilities or "venomous" in self.abilities
        self.venomous = "venomous" in self.abilities
        self.windfury = "windfury" in self.abilities
        self.cleave = "cleave" in self.abilities
        self.zapp = "zapp_targeting" in self.abilities
        self.megawindfury = "megawindfury" in self.abilities

        self.deathrattle = copy.deepcopy(data.get("deathrattle"))
        self.battlecry = copy.deepcopy(data.get("battlecry"))
        self.passive = copy.deepcopy(data.get("passive"))
        self.end_of_turn = copy.deepcopy(data.get("end_of_turn"))
        self.start_of_turn = copy.deepcopy(data.get("start_of_turn"))
        self.rally = copy.deepcopy(data.get("rally"))
        self.spellcraft = copy.deepcopy(data.get("spellcraft"))
        self.avenge = copy.deepcopy(data.get("avenge"))

        self.description = data.get("description", "")
        self.golden_description = data.get("golden_description", "")
        self.golden = data.get("golden", False)
        self.dead = data.get("dead", False)
        self.reborn_used = data.get("reborn_used", False)
        self.uid = data.get("uid", id(self))  # uniek id voor frontend tracking

    # ── Schade & leven ──────────────────────────────────────
    def take_damage(self, amount: int) -> dict:
        """Returns info over wat er gebeurde."""
        if amount <= 0:
            return {"shielded": False, "damage": 0}
        if self.divine_shield:
            self.divine_shield = False
            return {"shielded": True, "damage": 0, "shield_broken": True}
        self.health -= amount
        return {"shielded": False, "damage": amount}

    def is_dead(self) -> bool:
        return self.health <= 0 and not self.dead

    def heal(self, amount: int):
        self.health = min(self.health + amount, self.max_health)

    # ── Golden ──────────────────────────────────────────────
    def make_golden(self):
        self.golden = True
        self.attack = self.base_attack * 2
        self.health = self.base_health * 2
        self.max_health = self.base_health * 2

        # Use the real golden text from the data file when available.
        if self.golden_description:
            self.description = self.golden_description

        # Windfury → mega-windfury (4 aanvallen)
        if self.windfury:
            self.megawindfury = True
            if "megawindfury" not in self.abilities:
                self.abilities.append("megawindfury")

        # Verdubbel numerieke waarden in deathrattle-effecten voor legacy structured effects.
        if self.deathrattle:
            self.deathrattle = self._double_effect_values(self.deathrattle)

    @staticmethod
    def _double_effect_values(effect: dict) -> dict:
        d = copy.deepcopy(effect)
        dtype = d.get("type")
        # Summon-types omzetten naar summon_count met verdubbeld aantal
        if dtype == "summon":
            d["type"] = "summon_count"
            d["count"] = 2
        elif dtype == "summon_two":
            d["type"] = "summon_count"
            d["count"] = 4
        else:
            for key in ("attack", "health", "amount", "count"):
                if key in d and d[key] is not None:
                    d[key] *= 2
        return d

    # ── Serialisatie ────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "tribe": self.tribe,
            "types": self.types,
            "attack": self.attack,
            "health": self.health,
            "max_health": self.max_health,
            "golden": self.golden,
            "token": self.token,
            "taunt": self.taunt,
            "divine_shield": self.divine_shield,
            "reborn": self.reborn,
            "poisonous": self.poisonous,
            "venomous": self.venomous,
            "windfury": self.windfury,
            "megawindfury": self.megawindfury,
            "cleave": self.cleave,
            "zapp": self.zapp,
            "abilities": self.abilities,
            "deathrattle": self.deathrattle,
            "battlecry": self.battlecry,
            "passive": self.passive,
            "end_of_turn": self.end_of_turn,
            "start_of_turn": self.start_of_turn,
            "rally": self.rally,
            "spellcraft": self.spellcraft,
            "avenge": self.avenge,
            "description": self.description,
            "golden_description": self.golden_description,
            "dead": self.dead,
            "reborn_used": self.reborn_used,
        }

    @staticmethod
    def from_id(minion_id: str) -> "Minion":
        data = ALL_MINIONS.get(minion_id)
        if not data:
            raise ValueError(f"Onbekende minion id: {minion_id}")
        return Minion(copy.deepcopy(data))

    @staticmethod
    def from_dict(d: dict) -> "Minion":
        """Herstel een Minion van een geserialiseerde dict (voor combat kopieën)."""
        data = copy.deepcopy(ALL_MINIONS.get(d["id"], d))
        m = Minion(data)
        m.attack = _safe_stat(d.get("attack"), m.attack)
        m.health = _safe_stat(d.get("health"), m.health)
        m.max_health = _safe_stat(d.get("max_health", d.get("health")), m.max_health)
        m.golden = d.get("golden", False)
        m.description = d.get("description", m.description)
        m.golden_description = d.get("golden_description", m.golden_description)
        m.types = list(d.get("types", m.types))
        m.divine_shield = d.get("divine_shield", "divine_shield" in data.get("abilities", []))
        m.taunt = d.get("taunt", "taunt" in data.get("abilities", []))
        m.reborn = d.get("reborn", "reborn" in data.get("abilities", []))
        m.poisonous = d.get("poisonous", "poisonous" in data.get("abilities", []) or "venomous" in data.get("abilities", []))
        m.venomous = d.get("venomous", "venomous" in data.get("abilities", []))
        m.windfury = d.get("windfury", "windfury" in data.get("abilities", []))
        m.megawindfury = d.get("megawindfury", "megawindfury" in data.get("abilities", []))
        m.cleave = d.get("cleave", "cleave" in data.get("abilities", []))
        m.zapp = d.get("zapp", "zapp_targeting" in data.get("abilities", []))
        m.dead = d.get("dead", False)
        m.reborn_used = d.get("reborn_used", False)
        m.uid = d.get("uid", id(m))
        m.rally = copy.deepcopy(d.get("rally", data.get("rally")))
        m.start_of_turn = copy.deepcopy(d.get("start_of_turn", data.get("start_of_turn")))
        m.spellcraft = copy.deepcopy(d.get("spellcraft", data.get("spellcraft")))
        m.avenge = copy.deepcopy(d.get("avenge", data.get("avenge")))
        return m

    def clone(self) -> "Minion":
        d = self.to_dict()
        return Minion.from_dict(d)
