from pydantic import BaseModel
from typing import List, Optional

class Issue(BaseModel):
    type: str
    description: str
    location: Optional[str] = None
    severity: str = "medium"

class AnalysisResult(BaseModel):
    document: str
    issues: List[Issue]
    status: str = "completed"