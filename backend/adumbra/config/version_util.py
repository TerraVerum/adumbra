import json
import shutil
import subprocess
from pathlib import Path


def git_or_cached(
    command: tuple[str, ...],
    cache_file: str | Path | None = None,
    cache_key: str | None = None,
    refresh_cache=False,
) -> str:
    """
    Executes a git command or retrieves the result from a cache file.

    Also caches local calls to the function, so no file reads / git calls are needed
    when the same command is called in-process.

    **NOTE**: If `git` is not installed, the function will return an empty string -- so
    ensure a valid cache is provided in this case (i.e., fetching git commands from a
    docker container without git installed).

    Parameters
    ----------
    command
        The git command to execute. Can be a single command string or a list of command
        parts.
    cache_file
        The path to the cache file where command results are stored.
    cache_key
        The key to use in the cache file. If not provided, the command will be used as
        the key.
    refresh_cache
        If True, the cache will be force-refreshed by executing the command again, by
        default False.
    Returns
    -------
    str
        The output of the git command, either from the cache or from executing the
        command.
    """
    if not command or command[0] != "git":
        raise ValueError("Only git commands are supported.")
    if cache_file is None:
        # `adumbra` folder by default
        cache_file = Path(__file__).resolve().parent.parent / "git_cache.json"
    if cache_key is None:
        cache_key = command if isinstance(command, str) else " ".join(command)

    cache_file = Path(cache_file)
    cache: dict[str, str] = (
        json.loads(cache_file.read_text(encoding="utf-8"))
        if cache_file.exists()
        else {}
    )
    git_exists = shutil.which("git") is not None
    if git_exists and (refresh_cache or cache_key not in cache):
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=False)
        cache[cache_key] = result.stdout.strip()
        cache_file.write_text(json.dumps(cache, indent=2))
    return cache.get(cache_key, "")


class VersionControl:

    def __init__(self, root: str | Path | None = None):
        """
        Initialize the VersionUtil object.

        Parameters
        ----------
        root
            The root directory of the repository. If not provided, defaults to
            `adumbra`'s git directory.
        """

        if root is None:
            # We don't need to navigate all the way, since git looks for the .git folder
            # anyway
            root = Path(__file__).resolve().parent
        self.root = Path(root)

    def _run_git_command(self, *command: str, key: str):
        resolved_root = self.root.resolve().as_posix()
        return git_or_cached(("git", "-C", resolved_root, *command), cache_key=key)

    def get_tag(self):
        return self._run_git_command("describe", "--abbrev=0", "--tags", key="tag")

    def get_commits_behind(self):
        branch = self._run_git_command(
            "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", key="branch"
        )
        current_version = self._run_git_command(
            "rev-parse", "HEAD", key="current_version"
        )

        # Example command return:
        # <hash>        refs/heads/{branch}
        # so we split and get just the hash
        latest_version = self._run_git_command(
            "ls-remote", *branch.split("/"), key="latest_version"
        ).split()[0]
        result = self._run_git_command(
            "rev-list",
            "--count",
            f"{current_version}..{latest_version}",
            key="commits_behind",
        )
        try:
            return int(result)
        except ValueError:
            # When encountering errors, assume the branch is up-to-date by default
            return 0

    def is_latest(self):
        return self.get_commits_behind() == "0"


if __name__ == "__main__":
    vc = VersionControl()
    print(f"Version information for {vc.root}:")
    print(f"Tag: {vc.get_tag()}")
    print(f"Commits behind remote: {vc.get_commits_behind()}")
