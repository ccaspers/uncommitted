"""The 'uncommitted' command-line tool itself."""

import os
import sys
from argparse import ArgumentParser

from . import git
from .finder import find_repos

USAGE = """usage: %%prog [options] path [path...]

  Checks the status of all git, Subversion, and Mercurial repositories
  beneath the paths given on the command line.  Any repositories with
  uncommitted or unpushed changes are printed to standard out, along
  with the status of the files inside."""


SYSTEMS = {b".git": (b"Git", git.status)}
DOTDIRS = set(SYSTEMS)


class ErrorCannotLocate(Exception):
    """Signal that we cannot successfully run the locate(1) binary."""


linesep = os.linesep.encode("ascii")


def output(thing):
    """Replacement for print() that outputs bytes."""
    os.write(1, thing + linesep)


def scan(repos, options):
    """Given a repository list [(path, vcsname), ...], scan each of them."""
    ignore_set = set()
    repos = repos[::-1]  # Create a queue we can push and pop from
    while repos:
        directory, dotdir = repos.pop()
        ignore_this = any(pat in directory for pat in options.ignore_patterns)
        if ignore_this:
            if options.verbose:
                output(b"Ignoring repo: %s" % directory)
                output(b"")
            continue

        vcsname, get_status = SYSTEMS[dotdir]
        lines, subrepos = get_status(directory, ignore_set, options)

        # We want to tackle subrepos immediately after their repository,
        # so we put them at the front of the queue.
        subrepos = [(os.path.join(directory, r), dotdir) for r in subrepos]
        repos.extend(reversed(subrepos))

        if lines is None:  # signal that we should ignore this one
            continue
        if lines or options.verbose:
            output(b"%s - %s" % (directory, vcsname))
            for line in lines:
                output(line)
            output(b"")


def main():
    parser = ArgumentParser(usage=USAGE)
    parser.add_argument(
        "directory",
        type=str,
        default=".",
        nargs="?",
        help="print every repository whether changed or not",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print every repository whether changed or not",
    )
    parser.add_argument(
        "-n",
        "--non-tracking",
        action="store_true",
        help="print non-tracking branches (git only)",
    )
    parser.add_argument(
        "-u",
        "--untracked",
        action="store_true",
        help="print untracked files (git only)",
    )
    parser.add_argument(
        "-s", "--stash", action="store_true", help="print stash (git only)"
    )
    parser.add_argument(
        "-i",
        dest="ignore_patterns",
        default=[],
        nargs="*",
        help="ignore any directory paths that contain the specified string",
    )
    parser.add_argument(
        "--ignore-svn-states",
        help="ignore SVN states given as a string of status codes (SVN only)",
    )

    args = parser.parse_args()

    if not args:
        parser.print_help()
        exit(2)

    if sys.version_info[0] >= 3:
        # Turn string arguments back into their original bytes.
        fix = os.fsencode
        args.directory = fix(args.directory)
        args.ignore_patterns = [fix(s) for s in args.ignore_patterns]

    repos = set()

    path = os.path.abspath(args.directory)
    if not os.path.isdir(path):
        sys.stderr.write("Error: not a directory: %s\n" % (path,))
        sys.exit(3)
    paths = find_repos(path, patterns=DOTDIRS)
    repos.update(paths)

    repos = sorted(repos)
    scan(repos, args)
