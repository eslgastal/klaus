"""
    lodgeit.lib.diff
    ~~~~~~~~~~~~~~~~

    Render a nice diff between two things.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""

from difflib import SequenceMatcher

from klaus.utils import escape_html as e


def highlight_line(old_line, new_line):
    """Highlight inline changes in both lines."""
    # Preserve trailing newlines - strip before comparison and restore after.
    # This ensures newlines are not highlighted as changes and allows the
    # no_newline detection to work correctly.
    old_nl = b"\n" if old_line.endswith(b"\n") else b""
    new_nl = b"\n" if new_line.endswith(b"\n") else b""
    old_line = old_line.rstrip(b"\n")
    new_line = new_line.rstrip(b"\n")

    start = 0
    limit = min(len(old_line), len(new_line))
    while start < limit and old_line[start] == new_line[start]:
        start += 1
    end = -1
    limit -= start
    while -end <= limit and old_line[end] == new_line[end]:
        end -= 1
    end += 1
    if start or end:

        def do(line, tag):
            last = end + len(line)
            return b"".join(
                [
                    line[:start],
                    b"<",
                    tag,
                    b">",
                    line[start:last],
                    b"</",
                    tag,
                    b">",
                    line[last:],
                ]
            )

        old_line = do(old_line, b"del")
        new_line = do(new_line, b"ins")

    # Restore trailing newlines
    return old_line + old_nl, new_line + new_nl


def render_diff(a, b, n=3):
    """Parse the diff an return data for the template."""
    actions = []
    chunks = []
    for group in SequenceMatcher(None, a, b).get_grouped_opcodes(n):
        lines = []

        def add_line(old_lineno, new_lineno, action, line):
            actions.append(action)
            lines.append(
                {
                    "old_lineno": old_lineno,
                    "new_lineno": new_lineno,
                    "action": action,
                    "line": line,
                    "no_newline": not line.endswith(b"\n"),
                }
            )

        chunks.append(lines)
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for c, line in enumerate(a[i1:i2]):
                    add_line(i1 + c, j1 + c, "unmod", e(line))
            elif tag == "insert":
                for c, line in enumerate(b[j1:j2]):
                    add_line(None, j1 + c, "add", e(line))
            elif tag == "delete":
                for c, line in enumerate(a[i1:i2]):
                    add_line(i1 + c, None, "del", e(line))
            elif tag == "replace":
                old_lines = a[i1:i2]
                new_lines = b[j1:j2]
                # Apply inline highlighting for paired lines
                num_pairs = min(len(old_lines), len(new_lines))
                for c in range(num_pairs):
                    old_hl, new_hl = highlight_line(e(old_lines[c]), e(new_lines[c]))
                    add_line(i1 + c, None, "del", old_hl)
                    add_line(None, j1 + c, "add", new_hl)
                # Add remaining unpaired lines without inline highlighting
                for c, line in enumerate(old_lines[num_pairs:]):
                    add_line(i1 + num_pairs + c, None, "del", e(line))
                for c, line in enumerate(new_lines[num_pairs:]):
                    add_line(None, j1 + num_pairs + c, "add", e(line))
            else:
                raise AssertionError("unknown tag %s" % tag)

    return actions.count("add"), actions.count("del"), chunks
