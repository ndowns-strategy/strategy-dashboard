"""Strategy dashboard authoring from Python: REST login + the editor's own actions. See README.md."""
from .constants import KPI_ZONE, UNIT, VIS, ZONE  # noqa: F401
from .session import Session  # noqa: F401
from .transport import Connection, StrategyError  # noqa: F401
from .util import bgr  # noqa: F401
