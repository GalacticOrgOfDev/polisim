from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import uuid


@dataclass
class Policy:
    id: str
    title: str
    source_path: str
    pages: int = 0
    keywords: List[str] = None
    snippet: str = ""
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "keywords": self.keywords or [],
            "metadata": self.metadata or {},
        }

    @staticmethod
    def from_pdf(path: str, title: Optional[str] = None, keywords: Optional[List[str]] = None, snippet: str = "", pages: int = 0) -> "Policy":
        return Policy(
            id=str(uuid.uuid4()),
            title=title or path,
            source_path=path,
            pages=pages,
            keywords=keywords or [],
            snippet=snippet,
            metadata={},
        )
