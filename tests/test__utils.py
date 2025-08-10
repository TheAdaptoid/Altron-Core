import os
import tempfile
import pytest
from unittest import mock
from storage import database


class DummyDirNotFound(Exception):
    pass


# Patch DirectoryNotFoundError for __validate_dir tests
@pytest.fixture(autouse=True)
def patch_dir_not_found(monkeypatch):
    monkeypatch.setattr("src.storage._utils.DirectoryNotFoundError", DummyDirNotFound)
    yield


def test___validate_dir_exists(tmp_path):
    dir_path = str(tmp_path)
    database.__validate_dir(dir_path)  # Should not raise


def test___validate_dir_not_exists():
    with pytest.raises(DummyDirNotFound):
        database.__validate_dir("/nonexistent_dir_12345")


def test_create_file_success(tmp_path):
    file_path = tmp_path / "newfile.txt"
    database.create_file(str(file_path), "hello world")
    assert file_path.read_text() == "hello world"


def test_create_file_dir_not_exists(monkeypatch):
    monkeypatch.setattr(
        "src.storage._utils.__validate_dir",
        lambda d: (_ for _ in ()).throw(DummyDirNotFound(d)),
    )
    with pytest.raises(DummyDirNotFound):
        database.create_file("/nonexistent_dir/file.txt", "data")


def test_create_file_already_exists(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("existing")
    with pytest.raises(FileExistsError):
        database.create_file(str(file_path), "new content")


def test_read_file_success(tmp_path):
    file_path = tmp_path / "readme.txt"
    file_path.write_text("abc123")
    content = database.read_file(str(file_path))
    assert content == "abc123"


def test_read_file_not_exists(tmp_path):
    file_path = tmp_path / "nofile.txt"
    with pytest.raises(FileNotFoundError):
        database.read_file(str(file_path))


def test_replace_file_success(tmp_path):
    file_path = tmp_path / "replace.txt"
    file_path.write_text("old")
    database.replace_file(str(file_path), "new")
    assert file_path.read_text() == "new"


def test_replace_file_not_exists(tmp_path):
    file_path = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        database.replace_file(str(file_path), "data")


def test_delete_file_success(tmp_path):
    file_path = tmp_path / "delete.txt"
    file_path.write_text("bye")
    database.delete_file(str(file_path))
    assert not file_path.exists()


def test_delete_file_not_exists(tmp_path):
    file_path = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        database.delete_file(str(file_path))


def test_create_file_calls_validate_dir(monkeypatch, tmp_path):
    called = {}

    def fake_validate_dir(d):
        called["dir"] = d

    monkeypatch.setattr(database, "__validate_dir", fake_validate_dir)
    file_path = tmp_path / "abc.txt"
    database.create_file(str(file_path), "x")
    assert called["dir"] == str(tmp_path)


def test_create_file_writes_content(monkeypatch, tmp_path):
    file_path = tmp_path / "abc.txt"
    monkeypatch.setattr(database, "__validate_dir", lambda d: None)
    with mock.patch("builtins.open", mock.mock_open()) as m:
        database.create_file(str(file_path), "hello")
        m.assert_called_once_with(str(file_path), "w")
        handle = m()
        handle.write.assert_called_once_with("hello")
