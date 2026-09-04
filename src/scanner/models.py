from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Finding:
    category: str
    severity: Severity
    title: str
    detail: str
    recommendation: str
