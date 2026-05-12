from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class TacticalScheme:
    positions: Dict[int, int]

    def required_players(self) -> Dict[int, int]:
        return self.positions
