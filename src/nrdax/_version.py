"""Single source of truth for the package version.

Kept distinct from the *dataset* version (which comes from the loaded registry's
``index.json``) and the *schema* version (``nrdax.vocab.NRDAX_SCHEMA_VERSION``).
See ``docs/data-model.md`` for the versioning policy.
"""

from __future__ import annotations

__version__ = "0.1.0"
