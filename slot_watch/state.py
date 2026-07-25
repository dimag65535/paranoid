from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass
class WatchState:
    available: bool | None = None
    checked_at: str | None = None
    last_error: str | None = None


def load_state(path: Path) -> WatchState:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return WatchState(
            available=data.get("available"),
            checked_at=data.get("checked_at"),
            last_error=data.get("last_error"),
        )
    except FileNotFoundError:
        return WatchState()
    except (OSError, ValueError, TypeError):
        return WatchState()


def save_state(path: Path, state: WatchState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        json.dump(asdict(state), temporary, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)
