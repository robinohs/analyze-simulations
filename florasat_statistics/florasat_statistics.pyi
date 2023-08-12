from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Hop:
    typ: str
    id: int
    lat: float
    lon: float
    alt: int

    def to_ecef(self) -> Tuple[float, float, float]:
        pass
    def distance(self, other: Hop) -> float:
        pass

@dataclass
class Route:
    pid: int
    length: int
    hops: List[Hop]

def load_routes(read_path: str) -> List[Route]:
    pass

def process_routes(routes_fp: str, path: str, file_path: str):
    pass
