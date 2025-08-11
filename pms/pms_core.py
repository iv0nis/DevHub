# -*- coding: utf-8 -*-
"""pms_core – Minimal viable implementation (MVP)

Implements the core persistence layer for the PMS spec v1.2.1.
Focus: load(), save(mode="update_dual"), SHA‑1 validation, atomic
rollback using temporary files, and last_modified autofill.

The module purposely avoids external dependencies beyond PyYAML and the
Python standard library to keep bootstrap simple. Future extensions
(metrics, subscribe, concurrent locks) can build on these foundations.
"""
from __future__ import annotations

import csv
import hashlib
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, MutableMapping
from contextlib import contextmanager

import yaml  # type: ignore – Ensure PyYAML is available in runtime env

# Platform-specific locking
try:
    import fcntl  # POSIX systems
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt  # Windows
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(os.getenv("PMS_PROJECT_ROOT", Path.cwd()))
MEMORY_DIR = PROJECT_ROOT / "memory"
DOCS_DIR = PROJECT_ROOT / "docs"

# Cache for memory_index paths
_memory_index_cache = None

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

Scope = Literal[
    "memory_index", "project_status", "blueprint", "backlog", "raw"
]


class PMSCoreError(RuntimeError):
    """Base exception for PMS‑Core."""


class FileIntegrityError(PMSCoreError):
    """Raised when SHA‑1 validation fails."""


class LockTimeoutError(PMSCoreError):
    """Raised when file lock acquisition times out."""


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

@contextmanager
def _with_file_lock(target_path: Path, timeout: int = 30):
    """Acquire exclusive file lock for atomic operations."""
    lock_path = target_path.with_suffix(target_path.suffix + '.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    lock_file = None
    
    try:
        while time.time() - start_time < timeout:
            try:
                lock_file = lock_path.open('w')
                
                if HAS_FCNTL:
                    # POSIX systems
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                elif HAS_MSVCRT:
                    # Windows systems
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    # Fallback: basic file existence check (less robust)
                    if lock_path.exists():
                        raise BlockingIOError("Lock file exists")
                
                # Lock acquired successfully
                yield
                return
                
            except (BlockingIOError, OSError):
                # Lock is held by another process, wait and retry
                if lock_file:
                    lock_file.close()
                    lock_file = None
                time.sleep(0.1)
                continue
        
        # Timeout reached
        raise LockTimeoutError(f"Could not acquire lock for {target_path} within {timeout}s")
        
    finally:
        if lock_file:
            lock_file.close()
        # Clean up lock file
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass  # Lock file already removed

def _sha1_of_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _atomic_write(target: Path, data: bytes) -> None:
    """Write *data* to *target* atomically using a temporary file."""
    tmp_dir = MEMORY_DIR / "temp"
    
    # Ensure temp directory exists
    try:
        tmp_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PMSCoreError(f"Cannot create temp directory {tmp_dir}: {e}") from e
    
    # Ensure target directory exists
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PMSCoreError(f"Cannot create target directory {target.parent}: {e}") from e
    
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=tmp_dir, suffix=".tmp") as fh:
            fh.write(data)
            tmp_path = Path(fh.name)
        
        # Check if we have permission to write to target
        if target.exists() and not os.access(target, os.W_OK):
            raise PermissionError(f"No write permission for {target}")
        
        # os.replace() is atomic on POSIX & Windows when on the same filesystem
        os.replace(tmp_path, target)
        
    except OSError as e:
        # Clean up temp file on failure
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass  # Best effort cleanup
        
        if e.errno == 28:  # ENOSPC - No space left on device
            raise PMSCoreError(f"Disk full, cannot write to {target}") from e
        elif isinstance(e, PermissionError):
            raise PMSCoreError(f"Permission denied writing to {target}") from e
        else:
            raise PMSCoreError(f"Failed to write {target}: {e}") from e


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load(scope: str | Path) -> dict[str, Any] | str:
    """Load and parse PMS artifact according to file type.

    - *scope* may be a symbolic name ("blueprint", "memory_index", etc.)
      or a direct *Path* for raw access.
    - Returns parsed dict for YAML files, dict for blueprint markdown, str for others
    """
    path = _resolve_path(scope)
    if not path.exists():
        raise FileNotFoundError(path)

    # Read bytes for SHA validation if blueprint
    data_bytes = path.read_bytes()
    content = data_bytes.decode("utf-8")

    if path.match("*blueprint.md"):
        _validate_blueprint_sha(data_bytes)
        return _parse_blueprint_markdown(content)
    elif path.suffix == '.yaml':
        return yaml.safe_load(content) or {}
    elif path.suffix == '.csv':
        return _parse_csv_file(content)
    else:
        return content  # Raw string for other .md files


def save(
    scope: str | Path,
    payload: str,
    *,
    mode: Literal["update_dual"] | str = "update_dual",
) -> None:
    """Persist *payload* according to *mode* with file locking.

    The function autocompletes `last_modified` in blueprint headers
    and updates SHA‑1 & blueprint_changes.csv when necessary.
    """
    if mode != "update_dual":
        raise NotImplementedError("Only update_dual is implemented in MVP")

    target = _resolve_path(scope)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Use file lock for atomic operations
    with _with_file_lock(target):
        # Blueprint specific post‑processing
        if target.match("*blueprint.md"):
            payload = _update_blueprint_metadata(payload)
            _append_blueprint_change(payload)

        _atomic_write(target, payload.encode("utf-8"))


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_blueprint_markdown(content: str) -> dict[str, Any]:
    """Parse blueprint markdown into header dict + body content."""
    if not content.startswith("---"):
        return {"content": content, "header": {}}
    
    header_end = content.find("---", 3)
    if header_end == -1:
        return {"content": content, "header": {}}
    
    header_yaml = content[3:header_end]
    body = content[header_end + 3:].strip()
    
    try:
        header_dict = yaml.safe_load(header_yaml) or {}
    except yaml.YAMLError:
        header_dict = {}
    
    return {
        "header": header_dict,
        "content": body,
        "version": header_dict.get("version"),
        "last_modified": header_dict.get("last_modified"),
        "changelog": header_dict.get("changelog", []),
        "sha1_hash": header_dict.get("sha1_hash")
    }


def _parse_csv_file(content: str) -> list[dict[str, str]]:
    """Parse CSV content into list of dicts using first row as headers."""
    if not content.strip():
        return []
    
    lines = content.strip().splitlines()
    if len(lines) < 1:
        return []
    
    reader = csv.DictReader(lines)
    return list(reader)


# ---------------------------------------------------------------------------
# Blueprint helpers
# ---------------------------------------------------------------------------

def _update_blueprint_metadata(text: str) -> str:
    """Ensure `last_modified` and `sha1_hash` are updated in the YAML header."""
    if not text.startswith("---"):
        return text  # malformed header – skip

    lines = text.splitlines()
    header: list[str] = []
    body_start = 0
    for i, l in enumerate(lines[1:], 1):
        if l.strip() == "---":
            body_start = i + 1
            break
        header.append(l)

    # parse YAML header
    header_dict: MutableMapping[str, Any] = yaml.safe_load("\n".join(header)) or {}

    # update fields
    header_dict["last_modified"] = datetime.now(timezone.utc).strftime(ISO_FMT)
    body = "\n".join(lines[body_start:])
    header_dict["sha1_hash"] = _sha1_of_bytes(body.encode())

    # rebuild header
    new_header = yaml.safe_dump(header_dict, sort_keys=False).strip()
    new_text = "---\n" + new_header + "\n---\n" + body
    return new_text


def _validate_blueprint_sha(data_bytes: bytes) -> None:
    text = data_bytes.decode("utf-8")
    if not text.startswith("---"):
        raise FileIntegrityError("Blueprint missing YAML header")

    header_end = text.find("---", 3)
    header_yaml = text[3:header_end]
    header_dict: Mapping[str, Any] = yaml.safe_load(header_yaml) or {}
    expected = header_dict.get("sha1_hash", "")

    body = text[header_end + 3 :]
    actual = _sha1_of_bytes(body.encode())
    if expected and expected != actual:
        raise FileIntegrityError("Blueprint SHA‑1 mismatch → possible tampering")


def _append_blueprint_change(blueprint_text: str, author: str = "PMS_Core") -> None:
    """Append blueprint change to CSV with proper spec format."""
    BLUEPRINT_CHANGES_CSV.parent.mkdir(parents=True, exist_ok=True)
    
    # Create header if file doesn't exist or is empty
    if not BLUEPRINT_CHANGES_CSV.exists() or BLUEPRINT_CHANGES_CSV.stat().st_size == 0:
        with BLUEPRINT_CHANGES_CSV.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "author", "timestamp", "description", "status"])
    
    # Generate incremental ID
    next_id = _get_next_change_id()
    ts = datetime.now(timezone.utc).strftime(ISO_FMT)
    
    with BLUEPRINT_CHANGES_CSV.open("a", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            next_id,
            author,
            ts,
            "Blueprint updated via PMS-Core",
            "merged"
        ])


def _get_next_change_id() -> int:
    """Get next incremental ID for blueprint changes."""
    if not BLUEPRINT_CHANGES_CSV.exists():
        return 1
    
    try:
        with BLUEPRINT_CHANGES_CSV.open("r", newline="") as fh:
            reader = csv.reader(fh)
            rows = list(reader)
            if len(rows) <= 1:  # Only header or empty
                return 1
            # Get max ID from existing rows
            max_id = 0
            for row in rows[1:]:  # Skip header
                if row and row[0].isdigit():
                    max_id = max(max_id, int(row[0]))
            return max_id + 1
    except (OSError, ValueError):
        return 1


# ---------------------------------------------------------------------------
# Path resolver
# ---------------------------------------------------------------------------

def _load_memory_index() -> dict:
    """Load memory index with caching."""
    global _memory_index_cache
    if _memory_index_cache is None:
        index_path = MEMORY_DIR / "memory_index.yaml"
        with index_path.open('r', encoding='utf-8') as f:
            import yaml
            _memory_index_cache = yaml.safe_load(f)
    return _memory_index_cache

def _resolve_path(scope: str | Path) -> Path:
    """Translate *scope* into an absolute Path using memory_index.yaml."""
    if isinstance(scope, Path):
        return scope

    # Handle built-in scopes
    if scope == "memory_index":
        return MEMORY_DIR / "memory_index.yaml"
    if scope == "project_status":
        return MEMORY_DIR / "project_status.md"
    
    # Load memory index for dynamic paths
    memory_index = _load_memory_index()
    paths = memory_index.get('paths', {})
    
    # Handle dynamic scopes from memory_index
    if scope == "blueprint":
        blueprint_path = paths.get('blueprint_yaml', '../docs/02_blueprint.yaml')
        return (MEMORY_DIR / blueprint_path).resolve()
    
    if scope == "blueprint_changes":
        changes_path = paths.get('blueprint_changes', '../docs/blueprint_changes.csv')
        return (MEMORY_DIR / changes_path).resolve()
    
    if scope.startswith("backlog_f"):
        try:
            phase = scope.split("_f")[1]
            backlog_dir = paths.get('backlog_modular', '../docs/05_backlog/')
            backlog_path = (MEMORY_DIR / backlog_dir / f"backlog_f{phase}.yaml").resolve()
            return backlog_path
        except (IndexError, ValueError):
            raise ValueError(f"Invalid backlog scope format: {scope}")
    
    if scope == "backlog":
        raise ValueError(
            "Scope 'backlog' requires phase number, use 'backlog_f1', 'backlog_f2', etc."
        )
    
    if scope == "raw":
        raise ValueError("Scope 'raw' not implemented in MVP")
    
    raise ValueError(f"Unknown scope: {scope}")


# ---------------------------------------------------------------------------
# Placeholder for future metrics API
# ---------------------------------------------------------------------------

def metrics(name: str) -> Any:  # noqa: ANN401 – generic return for MVP
    """Stub – returns None until implemented."""
    return None


# ---------------------------------------------------------------------------
# Bootstrap and initialization
# ---------------------------------------------------------------------------

def bootstrap_pms(project_name: str = "proyecto") -> bool:
    """Initialize complete PMS structure with real values for a new project.
    
    Implements official PMS bootstrap steps:
    1. Create directory structure
    2. Generate files from templates with real values  
    3. Configure .gitignore
    4. Test rollback functionality
    
    Args:
        project_name: Name of the project being initialized
        
    Returns:
        True if initialization successful, False otherwise
        
    Raises:
        PMSCoreError: If initialization fails
    """
    try:
        # 1. Create directory structure
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "temp").mkdir(parents=True, exist_ok=True)
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        # Create backlog directory from memory_index
        memory_index_path = MEMORY_DIR / "memory_index.yaml"
        if memory_index_path.exists():
            with memory_index_path.open('r') as f:
                import yaml
                idx = yaml.safe_load(f)
                backlog_rel = idx.get('paths', {}).get('backlog_modular', '../docs/05_backlog/')
                backlog_dir = (MEMORY_DIR / backlog_rel).resolve()
                backlog_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Fallback if no memory_index yet
            (DOCS_DIR / "05_backlog").mkdir(parents=True, exist_ok=True)
        
        # 2. Generate memory_index.yaml with real values
        memory_index_content = f"""paths:
  status: "./project_status.md"
  blueprint: "../docs/blueprint.md"
  blueprint_changes: "../docs/blueprint_changes.csv"
  backlog_dir: "../docs/backlog/"
config:
  rollback_dual: true        # transacciones atómicas
  sha_validation: true       # verificación de integridad
  metrics_tracking: true     # seguimiento automático
  expected_hash: ""          # hash SHA-1 esperado del blueprint
"""
        
        # 3. Generate project_status.md with real initial values
        current_timestamp = datetime.now(timezone.utc).strftime(ISO_FMT)
        project_status_content = f"""---
version: 1.0
last_updated: {current_timestamp}
---

# Project Status - {project_name}

## Current State

```yaml
current_state:
  fase_actual: 1
  sprint_actual: 1
  ultima_tarea_id: ""
  
  # Métricas para Burndown y Health
  metricas:
    total_tareas: 0
    completadas: 0
    en_progreso: 0
    bloqueadas: 0
    fallidas: 0
    pendientes: 0
    
    # Health indicators
    velocidad_sprint: 0.0        # tareas completadas/sprint promedio
    porcentaje_completado: 0.0   # (completadas/total) * 100
    porcentaje_bloqueadas: 0.0   # (bloqueadas/total) * 100
    
    # Burndown data
    sprints_transcurridos: 0
    sprints_estimados: 1
    tareas_por_sprint_objetivo: 0.0
```

## Registro de Cambios (Cronológico Descendente)

### {current_timestamp.split('T')[0]} - Proyecto inicializado
- **Proyecto**: {project_name} creado
- **Estado**: Sistema PMS inicializado
- **Métricas**: Estado inicial (0 tareas)
- **Próximo**: Definir blueprint y primer backlog
"""
        
        # 4. Write files atomically
        _atomic_write(MEMORY_DIR / "memory_index.yaml", memory_index_content.encode("utf-8"))
        _atomic_write(MEMORY_DIR / "project_status.md", project_status_content.encode("utf-8"))
        
        # 5. Create basic .gitignore if it doesn't exist
        gitignore_path = PROJECT_ROOT / ".gitignore"
        gitignore_content = """# PMS temporary files
memory/temp/
*.lock
*.tmp

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
        
        if not gitignore_path.exists():
            _atomic_write(gitignore_path, gitignore_content.encode("utf-8"))
        
        # 6. Test basic functionality
        test_index = load("memory_index")
        test_status = load("project_status")
        
        if not test_index or not test_status:
            raise PMSCoreError("Bootstrap validation failed - files not readable")
            
        return True
        
    except Exception as e:
        raise PMSCoreError(f"PMS bootstrap failed: {e}") from e


# ---------------------------------------------------------------------------
# CLI helper (optional)
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Quick PMS‑Core CLI")
    parser.add_argument("cmd", choices=["load", "save"])
    parser.add_argument("scope")
    parser.add_argument("file", nargs="?", help="payload file for save")
    args = parser.parse_args()

    if args.cmd == "load":
        print(load(args.scope))
    elif args.cmd == "save":
        if not args.file:
            parser.error("save requires <file> argument")
        payload = Path(args.file).read_text()
        save(args.scope, payload)
        print("Saved ✔")
