"""A guard on the Supported endpoints page.

The page is the first thing anyone evaluating the library reads, and it has gone stale twice:
once holding `10 / 11` for das-Face after the eleventh landed, and once still showing
`compare(CompareCredential2AudioInput)` for five endpoints after `compare` was split into
five named methods in 0.5.0.

Neither could be caught by anything: documentation is prose, and prose does not fail. This
checks the one part of it that is mechanical — the client column — against the clients
themselves. It reads files and runs no requests.
"""

import inspect
import re
from pathlib import Path

import pytest

from vericlient import DasfaceClient, DaspeakClient, VcspClient

PAGE = Path(__file__).parent.parent / "docs" / "supported_endpoints.md"

CLIENTS = [
    (DaspeakClient, "## das-Peak"),
    (VcspClient, "## VCSP"),
    (DasfaceClient, "## das-Face"),
]

# Named on the page for the endpoints they still serve, and deliberately absent from the
# client column: they are deprecated, and the page points at what replaced them.
DEPRECATED = {"compare"}


def _section(heading: str) -> str:
    return PAGE.read_text().split(heading)[1].split("\n## ")[0]


def _methods_named_in(section: str) -> set[str]:
    """Return every `method()` named in the client column of a section's table."""
    rows = re.findall(r"^\|[^|]+\|([^|]+)\|", section, re.MULTILINE)
    return set(re.findall(r"`(\w+)\(", " ".join(rows)))


@pytest.mark.parametrize(("client", "heading"), CLIENTS, ids=[h.removeprefix("## ") for _, h in CLIENTS])
def test_the_page_only_names_methods_that_exist(client, heading):
    """A method renamed in the code must not survive on the page under its old name."""
    named = _methods_named_in(_section(heading))
    assert named, f"no client methods found under {heading}; the table shape must have changed"

    missing = sorted(name for name in named if not hasattr(client, name))
    assert not missing, f"{heading} names methods {client.__name__} does not have: {missing}"


@pytest.mark.parametrize(("client", "heading"), CLIENTS, ids=[h.removeprefix("## ") for _, h in CLIENTS])
def test_every_public_method_appears_on_the_page(client, heading):
    """An endpoint added to a client must be added to the page as well."""
    public = {
        name for name, _ in inspect.getmembers(client, inspect.isfunction) if not name.startswith("_") and name not in DEPRECATED
    }
    named = _methods_named_in(_section(heading))

    missing = sorted(public - named)
    assert not missing, f"{client.__name__} has methods the page does not list: {missing}"


def test_the_summary_agrees_with_the_tables():
    """The counts at the top are written by hand; the tables below them are the evidence."""
    page = PAGE.read_text()
    summary = dict(re.findall(r"^\| (das-Peak|VCSP|das-Face) \|.*?\*\*(\d+) / \d+\*\*", page, re.MULTILINE))
    assert set(summary) == {"das-Peak", "VCSP", "das-Face"}, "the summary table lost a row"

    for name, heading in (("das-Peak", "## das-Peak"), ("VCSP", "## VCSP"), ("das-Face", "## das-Face")):
        rows = len(re.findall(r"^\| \`[A-Z]+ /v\d", _section(heading), re.MULTILINE))
        # das-Face lists two endpoints beyond its specification, marked on the page with a
        # dagger, so the count it claims is the rest.
        daggers = _section(heading).count("† |")
        assert rows - daggers == int(summary[name]), (
            f"{name}: the summary says {summary[name]} but the table lists {rows - daggers} specified endpoints"
        )
