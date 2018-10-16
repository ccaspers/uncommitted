import os
from shutil import which
from subprocess import CalledProcessError, check_output

from .util import escape

_LOCATE_EXISTS = which("locate") is not None


def find_repos_with_walk(path, patterns):
    """Walk a tree and return a sequence of (directory, dotdir) pairs."""
    repos = []

    # This is for detecting symlink loops and escaping them. This is similar to
    # http://stackoverflow.com/questions/36977259/avoiding-infinite-recursion-with-os-walk/36977656#36977656
    def inode(path):
        stats = os.stat(path)
        return stats.st_dev, stats.st_ino

    seen_inodes = {inode(path)}

    for dirpath, dirnames, filenames in os.walk(path, followlinks=True):
        inodes = [inode(os.path.join(dirpath, p)) for p in dirnames]
        dirnames[:] = [p for p, i in zip(dirnames, inodes) if i not in seen_inodes]
        seen_inodes.update(inodes)

        for dotdir in set(dirnames) & patterns:
            repos.append((dirpath, dotdir))
    return repos


def find_repos_with_locate(path, patterns):
    """Use locate to return a sequence of (directory, dotdir) pairs."""
    command = [b"locate", b"-0"]
    for dotdir in patterns:
        # Escaping the slash (using '\/' rather than '/') is an
        # important signal to locate(1) that these glob patterns are
        # supposed to match the full path, so that things like
        # '.hgignore' files do not show up in the result.
        command.append(br"%s\/%s" % (escape(path), escape(dotdir)))
        command.append(br"%s\/*/%s" % (escape(path), escape(dotdir)))
    try:
        paths = check_output(command).strip(b"\0").split(b"\0")
    except CalledProcessError:
        return []
    return [
        os.path.split(p) for p in paths if not os.path.islink(p) and os.path.isdir(p)
    ]


def find_repos(path, patterns=set()):
    if _LOCATE_EXISTS:
        func = find_repos_with_locate
    else:
        func = find_repos_with_walk
    return func(path, patterns)
