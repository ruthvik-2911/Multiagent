from dataclasses import dataclass

@dataclass
class EnterpriseDocument:
    source: str
    title: str
    content: str
    metadata: dict
