from __future__ import annotations

import os
import re
import unicodedata
from collections.abc import Callable
from pathlib import Path

import yaml

from jobbot.schema import Profile, profile_from_dict, profile_to_dict, validate

STEPS = (
    "identidade", "experiencias", "skills", "certificacoes_idiomas",
    "restricoes", "triagem", "comportamento",
)
STEP_FIELDS: dict[str, tuple[str, ...]] = {
    "identidade": ("name", "age", "state", "city", "linkedin", "github", "links"),
    "experiencias": ("experiences", "projects"),
    "skills": ("skills",),
    "certificacoes_idiomas": ("certifications", "languages", "education"),
    "restricoes": ("constraints",),
    "triagem": ("screening", "stretch_policy"),
    "comportamento": ("behavior",),
}


class ProfileError(Exception):
    pass


def home() -> Path:
    env = os.environ.get("JOBBOT_HOME")
    return Path(env) if env else Path.home() / ".jobbot"


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if not slug:
        raise ValueError(f"nome inválido para pasta de perfil: {name!r}")
    return slug


def profile_dir(name: str) -> Path:
    return home() / "profiles" / slugify(name)


def forms_dir() -> Path:
    """Visible folder for the forms the person fills in (never the hidden profile folder)."""
    env = os.environ.get("JOBBOT_FORMS_DIR")
    return Path(env) if env else Path.home() / "Downloads"


def reports_dir(name: str) -> Path:
    """Visible folder where the person keeps the mini reports of each stage."""
    env = os.environ.get("JOBBOT_REPORTS_DIR")
    return (Path(env) if env else Path.home() / "Documents" / "JobBot") / slugify(name)


def atomic_write(path: Path, data: str | bytes, private_dir: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if private_dir:
        os.chmod(path.parent, 0o700)  # profile holds phone, email and salary; never used on shared folders
    tmp = path.with_name(path.name + ".tmp")
    try:
        if isinstance(data, bytes):
            tmp.write_bytes(data)
        else:
            tmp.write_text(data, encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ProfileError(f"{path}: YAML inválido ({e})") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProfileError(f"{path}: esperado um mapa YAML")
    return data


def dump(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def save_profile(name: str, p: Profile) -> Path:
    path = profile_dir(name) / "profile.yaml"
    atomic_write(path, dump(profile_to_dict(p)))
    return path


def load_profile(name: str) -> Profile:
    path = profile_dir(name) / "profile.yaml"
    try:
        return profile_from_dict(read_yaml(path))
    except (ValueError, TypeError) as e:
        raise ProfileError(f"{path}: {e}") from e


def _done(name: str) -> list[str]:
    return list(read_yaml(profile_dir(name) / "state.yaml").get("done", []))


def put_step(name: str, step: str, data: dict) -> None:
    if step not in STEP_FIELDS:
        raise ValueError(f"etapa desconhecida: {step!r}")
    if not isinstance(data, dict):
        raise ValueError("dados da etapa devem ser um mapa YAML")
    foreign = set(data) - set(STEP_FIELDS[step])
    if foreign:
        raise ValueError(f"campos fora da etapa {step!r}: {sorted(foreign)}")
    current = load_profile(name)  # load first: corrupt file must abort
    new_name = str(data.get("name", ""))
    if step == "identidade" and current.name and new_name and \
            current.name.strip().casefold() != new_name.strip().casefold():
        raise ValueError(f"já existe outro perfil nesta pasta ({current.name!r}); use um nome diferente de {new_name!r}")
    try:
        merged = profile_from_dict({**profile_to_dict(current), **data})
    except ValueError as e:
        raise ValueError(f"etapa {step!r}: {e}") from e
    done = _done(name)
    save_profile(name, merged)
    if step not in done:
        done.append(step)
    atomic_write(profile_dir(name) / "state.yaml", dump({"done": done}))


_APPENDABLE = ("assessments", "targets", "courses_done", "applications")


def append_record(name: str, field: str, record: dict) -> None:
    """Append one B1 record (history is kept); the round-trip rejects unknown keys and bad shapes."""
    if field not in _APPENDABLE:
        raise ValueError(f"campo não aceita registros: {field!r}")
    data = profile_to_dict(load_profile(name))  # load first: corrupt file must abort
    data[field] = [*data[field], record]
    new = profile_from_dict(data)
    errors = validate(new)  # a bad record must never leave a profile that fails validate
    if errors:
        raise ValueError("; ".join(errors))
    save_profile(name, new)


def update_profile(name: str, change: Callable[[Profile], None]) -> None:
    """Apply `change` to a copy of the profile, validate, then save; any failure leaves the file untouched."""
    working = profile_from_dict(profile_to_dict(load_profile(name)))  # load first: corrupt file must abort
    change(working)
    new = profile_from_dict(profile_to_dict(working))
    errors = validate(new)
    if errors:
        raise ValueError("; ".join(errors))
    save_profile(name, new)


def upsert_job_type(name: str, record: dict) -> None:
    """Replace the job type with the same role (case-insensitive) or add it; validated before saving."""
    data = profile_to_dict(load_profile(name))
    role = str(record.get("role", "")).casefold()
    data["job_types"] = [t for t in data["job_types"] if str(t.get("role", "")).casefold() != role] + [record]
    new = profile_from_dict(data)
    errors = validate(new)
    if errors:
        raise ValueError("; ".join(errors))
    save_profile(name, new)


def next_step(name: str) -> str | None:
    done = set(_done(name))
    return next((s for s in STEPS if s not in done), None)
