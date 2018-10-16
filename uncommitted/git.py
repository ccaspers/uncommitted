import re

from .runner import run

git_submodule = re.compile(br"\s(\S*)\s\(.*\)")


def status(path, ignore_set, options):
    """Run git status.

    Returns a 2-element tuple:
    * Text lines describing the status of the repository.
    * List of subrepository paths, relative to the repository itself.
    """
    # Check whether current branch is dirty:
    lines = [
        l
        for l in run(("git", "status", "-s", "-b"), cwd=path)
        if (options.untracked or not l.startswith(b"?")) and not l.startswith(b"##")
    ]

    # Check all branches for unpushed commits:
    lines += [l for l in run(("git", "branch", "-v"), cwd=path) if (b" [ahead " in l)]

    # Check for non-tracking branches:
    if options.non_tracking:
        lines += [
            l
            for l in run(
                (
                    "git",
                    "for-each-ref",
                    "--format=[%(refname:short)]%(upstream)",
                    "refs/heads",
                ),
                cwd=path,
            )
            if l.endswith(b"]")
        ]

    if options.stash:
        lines += [l for l in run(("git", "stash", "list"), cwd=path)]

    discovered_submodules = []
    for l in run(("git", "submodule", "status"), cwd=path):
        match = git_submodule.search(l)
        if match:
            discovered_submodules.append(match.group(1))

    return lines, discovered_submodules
