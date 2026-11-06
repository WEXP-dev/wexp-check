"""wexp_check: an appraiser for draft-sergeev-wexp-core-02 (semantics wexp-core-2),
written from the published text; the author did not read wexp-ref or any WEXP corpus expectations.
"""
from .core import appraise

__version__ = "0.1.0"
__all__ = ["appraise", "__version__"]
