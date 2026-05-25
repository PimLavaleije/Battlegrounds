import copy
from game.data.minions import ALL_MINIONS, TOKENS


class Minion:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.tier = data["tier"]
        self.tribe = data.get("tribe")
        self.token = data.get("token", False)

        self.base_attack = data["attack"]
        self.base_health = data["health"]
        self.attack = data["attack"]
        self.health = data["health"]
        self.max_health = data["health"]

        self.abilities = list(data.get("abilities", []))
        self.taunt = "taunt" in self.abilities
        self.divine_shield = "divine_shield" in self.abilities
        self.reborn = "reborn" in self.abilities
        self.poisonous = "poisonous" in self.abilities
        self.windfury = "windfury" in self.abilities
        self.cleave = "cleave" in self.abilities
        self.zapp = "zapp_targeting" in self.abilities

        self.deathrattle = data.get("deathrattle")
        self.battlecry = data.get("battlecry")
        self.passive = data.get("passive")
        self.end_of_turn = data.get("end_of_turn")

        self.description = data.get("description", "")
        self.golden = False
        self.dead = False
        self.reborn_used = False
        self.uid = id(self)  # uniek id voor frontend tracking

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

    # ── Serialisatie ────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "tribe": self.tribe,
            "attack": self.attack,
            "health": self.health,
            "max_health": self.max_health,
            "golden": self.golden,
            "token": self.token,
            "taunt": self.taunt,
            "divine_shield": self.divine_shield,
            "reborn": self.reborn,
            "poisonous": self.poisonous,
            "windfury": self.windfury,
            "cleave": self.cleave,
            "zapp": self.zapp,
            "abilities": self.abilities,
            "deathrattle": self.deathrattle,
            "battlecry": self.battlecry,
            "description": self.description,
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
        m.attack = d["attack"]
        m.health = d["health"]
        m.max_health = d.get("max_health", d["health"])
        m.golden = d.get("golden", False)
        m.divine_shield = d.get("divine_shield", "divine_shield" in data.get("abilities", []))
        m.taunt = d.get("taunt", "taunt" in data.get("abilities", []))
        m.reborn = d.get("reborn", "reborn" in data.get("abilities", []))
        m.poisonous = d.get("poisonous", "poisonous" in data.get("abilities", []))
        m.windfury = d.get("windfury", "windfury" in data.get("abilities", []))
        m.cleave = d.get("cleave", "cleave" in data.get("abilities", []))
        m.uid = d.get("uid", id(m))
        return m

    def clone(self) -> "Minion":
        d = self.to_dict()
        return Minion.from_dict(d)
