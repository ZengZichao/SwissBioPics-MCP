"""
SwissBioPics MCP Server — core module.

This module implements an MCP (Model Context Protocol) server that exposes
SwissBioPics data and functionality through a set of tools.

SwissBioPics (https://www.swissbiopics.org/) is a freely available library
of interactive biological images for visualizing subcellular location data,
developed by the Swiss-Prot group at the SIB Swiss Institute of Bioinformatics.

Available tools
---------------
1.  ``search_locations``      — Search for subcellular locations / cell types.
2.  ``get_search_suggestions`` — Get auto-complete suggestions for a query.
3.  ``get_cell_types``        — List all available cell types on SwissBioPics.
4.  ``get_cell_type_detail``  — Get details for a specific cell type by ID or name.
5.  ``get_cell_svg``          — Retrieve the SVG image of a cell type.
6.  ``get_subcellular_locations`` — Extract all subcellular locations from a cell type's SVG.
7.  ``get_location_detail``   — Get the description of a specific subcellular location by its SL ID.
8.  ``get_swissbiopics_info`` — Get general information about the SwissBioPics project.
"""

from __future__ import annotations

import re
import logging
from typing import Any
from urllib.parse import quote_plus

import httpx
from lxml import etree

from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Logging — must use stderr (never stdout) for stdio transport
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SWISSBIOPICS_BASE = "https://www.swissbiopics.org"
USER_AGENT = "SwissBioPics-MCP/0.1.0 (https://www.swissbiopics.org/)"
SVG_CACHE_PREFIX = "/prime/cache1/"
HTTP_TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# Initialize MCP server
# ---------------------------------------------------------------------------
mcp = MCPServer("swissbiopics")


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
async def _fetch(url: str, *, accept: str = "text/html") -> str | None:
    """Fetch text content from *url* with proper headers and error handling.

    Returns the response body as a string, or ``None`` on failure.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
    }
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code >= 400:
                logger.warning("HTTP %d for %s", resp.status_code, url)
                return None
            return resp.text
    except Exception as exc:
        logger.error("Request failed for %s: %s", url, exc)
        return None


async def _fetch_bytes(url: str) -> bytes | None:
    """Fetch raw bytes from *url*."""
    headers = {"User-Agent": USER_AGENT}
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code >= 400:
                logger.warning("HTTP %d for %s", resp.status_code, url)
                return None
            return resp.content
    except Exception as exc:
        logger.error("Request failed for %s: %s", url, exc)
        return None


async def _resolve_svg_content(cell_identifier: str) -> str | None:
    """Resolve and fetch the SVG content for a cell type.

    *cell_identifier* can be:
      - An SVG file name (e.g. ``Animal_cells.svg``) — fetched directly.
      - A numeric cell ID (e.g. ``8719``) — resolved via the detail page.
      - A name path (e.g. ``Animal_cell``) — resolved via the detail page.

    Returns the SVG content as a string, or ``None`` on failure.
    """
    if cell_identifier.lower().endswith(".svg"):
        svg_url = f"{SWISSBIOPICS_BASE}{SVG_CACHE_PREFIX}{cell_identifier}"
        return await _fetch(svg_url, accept="image/svg+xml")

    if cell_identifier.isdigit():
        page_url = f"{SWISSBIOPICS_BASE}/{cell_identifier}"
    else:
        page_url = f"{SWISSBIOPICS_BASE}/name/{cell_identifier}"

    html = await _fetch(page_url)
    if html is None:
        return None

    info = _parse_cell_type_detail(html)
    if not info["svg_file"]:
        return None

    return await _fetch(info["svg_url"], accept="image/svg+xml")


# ---------------------------------------------------------------------------
# HTML / SVG parsing helpers
# ---------------------------------------------------------------------------
_CELL_TYPE_RE = re.compile(
    r'data-name="([^"]+)"\s+data-title="([^"]+)"\s+data-target="([^"]+)"'
)


def _parse_cell_types_from_homepage(html: str) -> list[dict[str, str]]:
    """Extract the list of cell types from the homepage HTML."""
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in _CELL_TYPE_RE.finditer(html):
        svg_name = m.group(1).strip()
        title = m.group(2).strip()
        target = m.group(3).strip()
        if target in seen:
            continue
        seen.add(target)
        # Derive the numeric ID from the target path if possible
        # target looks like "name/Animal_cell" — we keep the name path
        results.append(
            {
                "title": title,
                "svg_file": svg_name,
                "target_path": target,
                "url": f"{SWISSBIOPICS_BASE}/{target}",
            }
        )
    return results


def _parse_search_results(html: str) -> dict[str, Any]:
    """Parse the HTML of a search results page into structured data."""
    # Count
    count_match = re.search(r'<span class="weak">\s*(\d+)\s*matching pages?\s*</span>', html)
    total = int(count_match.group(1)) if count_match else 0

    # Each result row: <tr> … <a href="/8719"> … <span class="edit_ok">Animal cell</span> …
    # Locations are listed in <span class="loc"> … </span>
    results: list[dict[str, Any]] = []

    # Split by <tr> to process each result row
    rows = re.split(r"<tr>", html)
    for row in rows:
        # Look for the cell-type link and title
        link_match = re.search(
            r'<a href="(/\d+)">\s*<span><img[^>]*/>\s*<span class="edit_ok">([^<]+)</span>',
            row,
        )
        if not link_match:
            continue
        cell_id = link_match.group(1).strip("/")
        title = link_match.group(2).strip()

        # Extract location highlights
        locations: list[str] = []
        for loc_match in re.finditer(r'<span class="loc">(.*?)</span>', row, re.DOTALL):
            raw = loc_match.group(1)
            # Strip tags, keep text
            text = re.sub(r"<[^>]+>", "", raw).strip().rstrip(",").strip()
            if text:
                locations.append(text)

        # Extract SVG file name from the thumbnail
        img_match = re.search(r'<img src="(/prime/cache1/[^"]+)"', row)
        svg_url = f"{SWISSBIOPICS_BASE}{img_match.group(1)}" if img_match else None

        results.append(
            {
                "cell_id": cell_id,
                "title": title,
                "url": f"{SWISSBIOPICS_BASE}/{cell_id}",
                "svg_url": svg_url,
                "matched_locations": locations,
            }
        )

    return {"total": total, "results": results}


def _parse_cell_type_detail(html: str) -> dict[str, str]:
    """Extract basic cell-type info from a detail page."""
    title_match = re.search(r'<h1[^>]*\bclass="[^"]*\bctitle\b[^"]*"[^>]*>([^<]+)</h1>', html)
    title = title_match.group(1).strip() if title_match else "Unknown"

    svg_match = re.search(r'data-name="([^"]+)"', html)
    svg_file = svg_match.group(1).strip() if svg_match else ""

    return {
        "title": title,
        "svg_file": svg_file,
        "svg_url": f"{SWISSBIOPICS_BASE}{SVG_CACHE_PREFIX}{svg_file}" if svg_file else "",
    }


def _parse_svg_locations(svg_content: str | bytes) -> list[dict[str, str]]:
    """Parse an SVG file and extract all subcellular locations.

    Each <g class="subcellular_location"> element contains:
      - an ``id`` attribute with the SL identifier (e.g. ``SL0173``)
      - a <text class="subcell_name"> child with the location name
      - a <text class="subcell_description"> child with the description
    """
    locations: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    try:
        if isinstance(svg_content, str):
            svg_content = svg_content.encode("utf-8")
        # lxml is lenient with HTML/SVG entities
        tree = etree.fromstring(svg_content)
    except Exception as exc:
        logger.error("Failed to parse SVG: %s", exc)
        return locations

    # Namespace is usually "http://www.w3.org/2000/svg" but we use local-name()
    for g in tree.iter():
        tag = etree.QName(g).localname if isinstance(g.tag, str) else ""
        if tag != "g":
            continue
        classes = g.get("class", "")
        if "subcellular_location" not in classes:
            continue
        sl_id = g.get("id", "")
        if not sl_id or sl_id in seen_ids:
            continue
        seen_ids.add(sl_id)

        name = ""
        description = ""
        for child in g:
            child_tag = etree.QName(child).localname if isinstance(child.tag, str) else ""
            if child_tag != "text":
                continue
            child_classes = child.get("class", "")
            text_val = (child.text or "").strip()
            if "subcell_name" in child_classes:
                name = text_val
            elif "subcell_description" in child_classes:
                description = text_val

        if name:
            locations.append(
                {
                    "sl_id": sl_id,
                    "name": name,
                    "description": description,
                }
            )

    return locations


def _parse_suggestions(html: str) -> list[str]:
    """Parse the suggestion API response (plain HTML spans)."""
    suggestions: list[str] = []
    for m in re.finditer(r"<span[^>]*>(.*?)</span>", html, re.DOTALL):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if text:
            suggestions.append(text)
    return suggestions


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_locations(query: str) -> str:
    """Search SwissBioPics for subcellular locations and cell types.

    The query supports advanced syntax:
      - ``spindle body`` or ``spindle AND body``  — both terms must be present (AND)
      - ``SL-0073 OR chromatophore``               — either term (OR)
      - ``"golgi stack"``                          — exact phrase
      - ``endosome -peroxisome``                   — exclude a term (NOT)
      - ``bact*``                                  — wildcard prefix
      - ``rhoptri~``                               — fuzzy search (allows ~2 typos)
      - Parentheses: ``lumen AND (SL0158 OR wall)``

    Args:
        query: Search query string using the syntax described above.

    Returns:
        A formatted summary of matching cell types and their locations.
    """
    if not query or not query.strip():
        return "Error: query must not be empty."

    url = f"{SWISSBIOPICS_BASE}/search?query={quote_plus(query)}"
    html = await _fetch(url)
    if html is None:
        return f"Error: failed to fetch search results for '{query}'."

    data = _parse_search_results(html)
    total = data["total"]
    results = data["results"]

    if total == 0 or not results:
        return f"No results found for '{query}'."

    lines = [f"Found {total} matching cell type(s) for '{query}':\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}  (ID: {r['cell_id']})")
        lines.append(f"   URL: {r['url']}")
        if r.get("svg_url"):
            lines.append(f"   SVG: {r['svg_url']}")
        if r["matched_locations"]:
            locs = "; ".join(r["matched_locations"][:8])
            lines.append(f"   Matched locations: {locs}")
        lines.append("")

    return "\n".join(lines).strip()


@mcp.tool()
async def get_search_suggestions(query: str) -> str:
    """Get auto-complete search suggestions for a partial query.

    This is useful for interactive search experiences — as the user types,
    you can call this tool to show matching terms from the SwissBioPics
    vocabulary.

    Args:
        query: A partial search term (e.g. ``mito``).

    Returns:
        A list of suggested completion terms.
    """
    if not query or not query.strip():
        return "Error: query must not be empty."

    url = f"{SWISSBIOPICS_BASE}/search/suggest?query={quote_plus(query)}"
    html = await _fetch(url, accept="text/html")
    if html is None:
        return f"Error: failed to fetch suggestions for '{query}'."

    suggestions = _parse_suggestions(html)
    if not suggestions:
        return f"No suggestions found for '{query}'."

    lines = [f"Suggestions for '{query}':"]
    for i, s in enumerate(suggestions, 1):
        lines.append(f"  {i}. {s}")
    return "\n".join(lines)


@mcp.tool()
async def get_cell_types() -> str:
    """List all available cell types on SwissBioPics.

    SwissBioPics includes cell types from all kingdoms of life:
    animal cells (muscle, neuron, epithelial, etc.), fungal cells,
    plant cells, archaeal cells, and various bacterial morphologies
    (rod, coccus, spiral, etc.).

    Returns:
        A formatted list of all cell types with their identifiers and URLs.
    """
    html = await _fetch(SWISSBIOPICS_BASE)
    if html is None:
        return "Error: failed to fetch the SwissBioPics homepage."

    cell_types = _parse_cell_types_from_homepage(html)
    if not cell_types:
        return "Error: could not parse cell types from the homepage."

    lines = [f"SwissBioPics — {len(cell_types)} available cell types:\n"]
    for i, ct in enumerate(cell_types, 1):
        lines.append(f"{i}. {ct['title']}")
        lines.append(f"   SVG file: {ct['svg_file']}")
        lines.append(f"   URL: {ct['url']}")
        lines.append("")

    return "\n".join(lines).strip()


@mcp.tool()
async def get_cell_type_detail(cell_identifier: str) -> str:
    """Get details for a specific cell type by its numeric ID or name.

    Args:
        cell_identifier: Either a numeric cell ID (e.g. ``8719``) or a
            cell-type name path (e.g. ``Animal_cell``,
            ``Rod-shaped_bacteria:_one_membrane_(Gram+)``).
            Numeric IDs can be found from search results or the cell-type list.

    Returns:
        Cell type title, SVG file name, SVG URL, and a link to the page.
    """
    if not cell_identifier or not cell_identifier.strip():
        return "Error: cell_identifier must not be empty."

    cell_identifier = cell_identifier.strip()

    # Decide whether it's numeric (e.g. "8719") or a name path (e.g. "Animal_cell")
    if cell_identifier.isdigit():
        url = f"{SWISSBIOPICS_BASE}/{cell_identifier}"
    else:
        url = f"{SWISSBIOPICS_BASE}/name/{cell_identifier}"

    html = await _fetch(url)
    if html is None:
        return f"Error: failed to fetch cell type '{cell_identifier}' (tried {url})."

    info = _parse_cell_type_detail(html)
    lines = [
        f"Cell type: {info['title']}",
        f"SVG file: {info['svg_file']}",
        f"SVG URL: {info['svg_url']}",
        f"Page URL: {url}",
    ]
    return "\n".join(lines)


@mcp.tool()
async def get_cell_svg(cell_identifier: str) -> str:
    """Retrieve the raw SVG image content of a cell type.

    The SVG contains the full interactive cell illustration with embedded
    subcellular location data (SL IDs, names, and descriptions as hidden
    text elements).

    Args:
        cell_identifier: Either a numeric cell ID (e.g. ``8719``) or a
            cell-type name (e.g. ``Animal_cell``).  You can also pass the
            SVG file name directly (e.g. ``Animal_cells.svg``).

    Returns:
        The raw SVG XML content as a string (may be large).
    """
    if not cell_identifier or not cell_identifier.strip():
        return "Error: cell_identifier must not be empty."

    cell_identifier = cell_identifier.strip()

    content = await _resolve_svg_content(cell_identifier)
    if content is None:
        return f"Error: failed to fetch SVG for '{cell_identifier}'."

    return content


@mcp.tool()
async def get_subcellular_locations(cell_identifier: str) -> str:
    """Extract all subcellular locations defined in a cell type's SVG.

    Each location includes an SL identifier (e.g. ``SL0173``), a human-readable
    name (e.g. ``Mitochondrion``), and a detailed description.

    Args:
        cell_identifier: Numeric cell ID (e.g. ``8719``), name path
            (e.g. ``Animal_cell``), or SVG file name (e.g. ``Animal_cells.svg``).

    Returns:
        A formatted list of all subcellular locations with SL IDs, names,
        and truncated descriptions.
    """
    if not cell_identifier or not cell_identifier.strip():
        return "Error: cell_identifier must not be empty."

    cell_identifier = cell_identifier.strip()

    content = await _resolve_svg_content(cell_identifier)
    if content is None:
        return f"Error: failed to fetch SVG for '{cell_identifier}'."

    locations = _parse_svg_locations(content)
    if not locations:
        return f"No subcellular locations found in SVG for '{cell_identifier}'."

    lines = [f"Subcellular locations in '{cell_identifier}' ({len(locations)} locations):\n"]
    for loc in locations:
        desc = loc["description"]
        if len(desc) > 120:
            desc = desc[:117] + "..."
        lines.append(f"  [{loc['sl_id']}] {loc['name']}")
        if desc:
            lines.append(f"      {desc}")
        lines.append("")

    return "\n".join(lines).strip()


@mcp.tool()
async def get_location_detail(sl_id: str, cell_identifier: str = "8719") -> str:
    """Get the detailed description of a specific subcellular location.

    Subcellular locations in SwissBioPics are identified by ``SL`` identifiers
    (e.g. ``SL0173`` for *Mitochondrion*).  This tool looks up the full
    description of a location as defined within a cell type's SVG.

    Args:
        sl_id: The subcellular-location identifier (e.g. ``SL0173``).
            Both ``SL0173`` and ``SL-0173`` formats are accepted.
        cell_identifier: The cell type to look up within.  Defaults to
            ``8719`` (Animal cell) which has the most comprehensive set of
            locations.  Can be a numeric ID, name, or SVG file name.

    Returns:
        The location's SL ID, name, and full description.
    """
    if not sl_id or not sl_id.strip():
        return "Error: sl_id must not be empty."

    sl_id = sl_id.strip().upper()
    # Normalise: remove the dash if present (SL-0173 -> SL0173)
    if sl_id.startswith("SL-"):
        sl_id = "SL" + sl_id[3:]
    elif not sl_id.startswith("SL"):
        sl_id = "SL" + sl_id

    cell_identifier = (cell_identifier or "8719").strip()

    content = await _resolve_svg_content(cell_identifier)
    if content is None:
        return f"Error: failed to fetch SVG for '{cell_identifier}'."

    locations = _parse_svg_locations(content)
    for loc in locations:
        if loc["sl_id"].upper() == sl_id:
            lines = [
                f"SL ID: {loc['sl_id']}",
                f"Name: {loc['name']}",
                f"Description: {loc['description'] or '(no description available)'}",
                f"Found in cell type: {cell_identifier}",
            ]
            return "\n".join(lines)

    return (
        f"Location '{sl_id}' was not found in cell type '{cell_identifier}'.\n"
        f"Use the ``get_subcellular_locations`` tool to see all available SL IDs "
        f"for this cell type."
    )


@mcp.tool()
async def get_swissbiopics_info() -> str:
    """Get general information about the SwissBioPics project.

    Returns a summary including the project description, license, citation,
    and links to key resources.

    Returns:
        A formatted information string about SwissBioPics.
    """
    html = await _fetch(f"{SWISSBIOPICS_BASE}/help")
    if html is None:
        # Fall back to known static info
        return _FALLBACK_INFO

    # Try to extract the "What is SwissBioPics?" section
    desc_match = re.search(
        r'<h3[^>]*>What is SwissBioPics\?</h3>\s*<p>(.*?)</p>',
        html, re.DOTALL,
    )
    desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip() if desc_match else ""

    cite_match = re.search(
        r'<h3[^>]*>How can I use SwissBioPics\?</h3>\s*<p>(.*?)</p>',
        html, re.DOTALL,
    )
    howto = re.sub(r'<[^>]+>', '', cite_match.group(1)).strip() if cite_match else ""

    license_match = re.search(
        r'Creative Commons Attribution 4\.0 International \(CC BY 4\.0\)',
        html,
    )
    license_info = "CC BY 4.0" if license_match else "See website"

    lines = [
        "SwissBioPics — Project Information",
        "=" * 40,
        "",
    ]
    if desc:
        lines.append(f"Description:\n  {desc}")
    lines.append("")
    lines.append(f"Website: {SWISSBIOPICS_BASE}")
    lines.append(f"License: {license_info}")
    lines.append("Citation:")
    lines.append("  SwissBioPics - an interactive library of cell images for the")
    lines.append("  visualization of subcellular location data.")
    lines.append("  PMID: 35411389 | DOI: 10.1093/database/baac026")
    lines.append("")
    if howto:
        lines.append(f"Usage:\n  {howto}")
    lines.append("")
    lines.append("NPM package: https://www.npmjs.com/package/@swissprot/swissbiopics-visualizer")
    lines.append("Developed by: Swiss-Prot group, SIB Swiss Institute of Bioinformatics")

    return "\n".join(lines)


_FALLBACK_INFO = """\
SwissBioPics — Project Information
========================================

Description:
  SwissBioPics is a freely available library of interactive biological
  images for visualizing subcellular location data. It includes cell types
  from all kingdoms of life — from muscle, neuronal and epithelial cells of
  animals to rods, cocci, clubs, spirals and other more exotic forms of
  bacteria and archaea.

Website: https://www.swissbiopics.org
License: CC BY 4.0 (Creative Commons Attribution 4.0 International)
Citation:
  SwissBioPics - an interactive library of cell images for the
  visualization of subcellular location data.
  PMID: 35411389 | DOI: 10.1093/database/baac026

NPM package: https://www.npmjs.com/package/@swissprot/swissbiopics-visualizer
Developed by: Swiss-Prot group, SIB Swiss Institute of Bioinformatics
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the MCP server on the stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
