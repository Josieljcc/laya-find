"""Deprecated: use ``laya_find.py --policy strict``.

Kept as a thin wrapper for old commands. Prefer:

  .\\.venv\\Scripts\\python.exe examples\\laya_find.py --policy strict ...

See examples/README.md and examples/LAYA_FIND.md.
"""

from __future__ import annotations

import sys

if __package__:
    from examples.laya_find import main
else:
    from laya_find import main


if __name__ == "__main__":
    raise SystemExit(main(["--policy", "strict", *sys.argv[1:]]))
