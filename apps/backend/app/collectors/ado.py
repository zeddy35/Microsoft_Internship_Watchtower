"""Azure DevOps collector stub — same interface as collectors.github, to be
filled in if ADO access is granted during the internship. ADO_ORG/ADO_PROJECT/
ADO_PAT are read directly from the environment rather than Settings since
they're optional and unrelated to the GitHub-based demo path.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


async def collect_all() -> None:
    """No-op until ADO_ORG/ADO_PROJECT/ADO_PAT are configured and this is implemented."""
    if not (os.environ.get("ADO_ORG") and os.environ.get("ADO_PROJECT") and os.environ.get("ADO_PAT")):
        logger.info("Azure DevOps collector not configured, skipping")
        return

    logger.warning("Azure DevOps collector is not yet implemented")
