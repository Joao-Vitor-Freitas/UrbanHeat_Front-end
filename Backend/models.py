from dataclasses import dataclass
from datetime import datetime

@dataclass
class Medicao:
    sensor_id: str
    temperatura: float
    umidade: float
    data_hora: datetime