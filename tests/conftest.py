import pytest


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBBOT_HOME", str(tmp_path))
    monkeypatch.setenv("JOBBOT_FORMS_DIR", str(tmp_path / "forms"))
    return tmp_path
