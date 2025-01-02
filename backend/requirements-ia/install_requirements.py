#!/usr/bin/env python
import os
import re
import subprocess
import sys
from pathlib import Path

env_requirements_map = {
    "SAM2": "sam2.in",
    "ZIM": "zim.in",
}
# Match quote, allow everything but that quote inside, then match the quote again
SINGLE_QUOTE_REGEX = r"'[^']*?'"
DOUBLE_QUOTE_REGEX = r'"[^"]*?"'
IF_PARSE_REGEX = re.compile(
    rf"--if[= ](?P<if_statement>{SINGLE_QUOTE_REGEX}|{DOUBLE_QUOTE_REGEX})"
)
DEFAULT_SCOPE = {"os": os, "sys": sys}


def eval_if_statement(line: str, scope: dict | None = None):
    """
    Matches the statement inside `--if="..."` / `--if='...'` blocks and evaluates them
    into a bool expression
    """
    # pylint: disable=eval-used
    if "--if=" not in line:
        return True
    if not (parsed := IF_PARSE_REGEX.search(line)):
        raise ValueError(f"Invalid --if statement: {line}")
    if_statement = parsed.group("if_statement")[1:-1]
    return eval(if_statement, scope or DEFAULT_SCOPE)


def normalize_requirement(req: str) -> str:
    """Removes commented lines and strips"""
    return req.split("#", 1)[0].strip()


def install_requirements():
    here = Path(__file__).resolve().parent
    reqs_text = [
        here.joinpath(req).read_text(encoding="utf-8")
        for (env, req) in env_requirements_map.items()
    ]
    all_reqs = "\n".join(reqs_text)

    # Pip doesn't allow `--no-deps` per requirement, so do 2 batches: one where
    # --no-deps can be set at toplevel, and all other requirements that *can* install
    # deps (see https://github.com/pypa/pip/issues/9948)
    allow_sub_deps, no_sub_deps = [], []
    for req in all_reqs.splitlines():
        if not req or req.startswith("#") or not eval_if_statement(req):
            continue
        normalized = normalize_requirement(req)
        if "--no-deps" in req:
            no_sub_deps.append(normalized)
        else:
            allow_sub_deps.append(normalized)
    cmd_prefix = [sys.executable, "-m", "pip", "install"]
    if no_sub_deps:
        subprocess.run([*cmd_prefix, "--no-deps", *no_sub_deps], check=True)
    if allow_sub_deps:
        subprocess.run([*cmd_prefix, *allow_sub_deps], check=True)


if __name__ == "__main__":
    install_requirements()
