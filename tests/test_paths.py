import sys

from core import paths


def test_portable_exe_uses_folder_next_to_exe(tmp_path, monkeypatch):
    exe_dir, bundle = tmp_path / "Mon App", tmp_path / "_MEI123"
    (bundle / "data").mkdir(parents=True)
    (bundle / "data" / "templates.json").write_text("{}")
    exe_dir.mkdir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "RecyclarrConfigurator.exe"))
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)

    assert paths.app_dir() == exe_dir
    # First launch offline: falls back to the copy bundled inside the exe
    assert paths.data_file("templates.json") == bundle / "data" / "templates.json"
    # Once the startup sync wrote data next to the exe, that copy wins
    (exe_dir / "data").mkdir()
    (exe_dir / "data" / "templates.json").write_text("{}")
    assert paths.data_file("templates.json") == exe_dir / "data" / "templates.json"
