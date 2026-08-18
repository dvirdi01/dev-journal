import subprocess

from journal_cli.git_utils import detect_project


# --project should always win, no git involved at all
def test_explicit_project_overrides_everything(tmp_path):
    assert detect_project("my-explicit-project") == "my-explicit-project"


# repo folder name deliberately differs from remote name, to prove
# the remote URL is actually being read, not just the folder name
def test_repo_with_remote_uses_remote_name(tmp_path, monkeypatch):
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/someuser/some-repo.git"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(repo_dir)

    assert detect_project(None) == "some-repo"


# local-only repo (no remote) — legitimate case, falls back to folder name
def test_repo_without_remote_uses_folder_name(tmp_path, monkeypatch):
    repo_dir = tmp_path / "local-only-repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    monkeypatch.chdir(repo_dir)

    assert detect_project(None) == "local-only-repo"


# not a git repo at all — also falls back to folder name (with a warning)
def test_non_git_directory_falls_back_to_folder_name(tmp_path, monkeypatch):
    non_repo_dir = tmp_path / "not-a-repo"
    non_repo_dir.mkdir()
    monkeypatch.chdir(non_repo_dir)

    assert detect_project(None) == "not-a-repo"
