

from datetime import datetime
from typing import Optional

from gws_core import BaseModelDTO


class SaveProjectDTO(BaseModelDTO):
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    project_manager_id: Optional[str] = None
