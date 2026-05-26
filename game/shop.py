import random
from game.minion import Minion
from game.data.minions import MINIONS, POOL_SIZE, SHOP_SIZE, get_minions_for_tier
from game.data.spells import SPELLS_BY_TIER


class ShopManager:
    """Beheert de gedeelde minion pool voor één game."""

    def __init__(self):
        # Pool: {minion_id: count}
        self.pool: dict[str, int] = {}
        for mid, data in MINIONS.items():
            self.pool[mid] = POOL_SIZE.get(data["tier"], 15)

    # ── Pool beheer ─────────────────────────────────────────
    def take_from_pool(self, minion_id: str) -> bool:
        if self.pool.get(minion_id, 0) > 0:
            self.pool[minion_id] -= 1
            return True
        return False

    def return_to_pool(self, minion: Minion):
        if minion and not minion.token:
            base_id = minion.id
            self.pool[base_id] = self.pool.get(base_id, 0) + (2 if minion.golden else 1)

    def return_shop_to_pool(self, shop: list):
        for slot in shop:
            if slot is not None and not isinstance(slot, dict):
                self.return_to_pool(slot)

    # ── Shop generatie ───────────────────────────────────────
    def generate_shop(self, tavern_tier: int, hero: dict | None = None) -> list[Minion | None]:
        size = SHOP_SIZE.get(tavern_tier, 3)
        available = [mid for mid, data in MINIONS.items()
                     if data["tier"] <= tavern_tier and self.pool.get(mid, 0) > 0]

        # Millificent: garanteer minstens 1 Mech
        needs_mech = (hero and hero.get("ability", {}).get("effect") == "always_mech_in_shop")
        mechs = [m for m in available if MINIONS[m].get("tribe") == "Mech"]

        if not available:
            return [None] * size

        shop = []
        forced_mech = False

        for i in range(size):
            if needs_mech and not forced_mech and mechs:
                pool = mechs
                forced_mech = True
            else:
                pool = available

            if not pool:
                shop.append(None)
                continue

            chosen_id = random.choice(pool)
            if self.take_from_pool(chosen_id):
                shop.append(Minion.from_id(chosen_id))
                # Verwijder uit available zodat we geen duplicaten pakken per generate
                available = [m for m in available if m != chosen_id or self.pool.get(m, 0) > 0]
                if chosen_id in mechs:
                    mechs = [m for m in mechs if m != chosen_id or self.pool.get(m, 0) > 0]
            else:
                shop.append(None)

        # Add 1 spell slot for tavern tier 2+
        if tavern_tier >= 2:
            tier_spells = []
            for t in range(1, min(tavern_tier, 6) + 1):
                tier_spells.extend(SPELLS_BY_TIER.get(t, []))
            if tier_spells:
                spell = random.choice(tier_spells)
                shop.append({**spell, "type": "spell", "cost": 3})

        return shop
