import sys
from subprocess import CalledProcessError, check_output


def run(command, **kw):
    """Run `command`, catch any exception, and return lines of output."""
    # Windows low-level subprocess API wants str for current working
    # directory.
    if sys.platform == "win32":
        _cwd = kw.get("cwd", None)
        if _cwd is not None:
            kw["cwd"] = _cwd.decode()
    try:
        # In Python 3, iterating over bytes yield integers, so we call
        # `splitlines()` to force Python 3 to give us lines instead.
        return check_output(command, **kw).splitlines()
    except CalledProcessError:
        return ()
    except FileNotFoundError:
        print(
            "The {} binary was not found. Skipping directory {}.\n".format(
                command[0], kw["cwd"].decode("UTF-8")
            )
        )
        return ()
