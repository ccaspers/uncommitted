import re

globchar = re.compile(br"([][*?])")


def escape(s):
    """Escape the characters special to locate(1) globbing."""
    return globchar.sub(br"\\\1", s)
