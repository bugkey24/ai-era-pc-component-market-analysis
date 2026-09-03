"""Logger module — named-logger factory (see docs/02 file structure).

Re-exported from :mod:`src.utils.helpers` to keep the documented layout
(``src/utils/logger.py``) while avoiding duplicate implementations.
"""

from .helpers import setup_logger

__all__ = ["setup_logger"]
