# commitizen runs plugin discovery at import time, so it must be fully
# imported before wyld_cz.base starts initializing, otherwise the entry
# point loader re-enters a partially initialized module.
import commitizen  # noqa: F401  # pylint: disable=unused-import

from .base import WyldCommitizen

__all__ = ['WyldCommitizen']
