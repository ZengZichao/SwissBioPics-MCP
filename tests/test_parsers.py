"""Unit tests for parsing helper functions in swissbiopics_mcp.server."""
from __future__ import annotations

import pytest

from swissbiopics_mcp.server import (
    SWISSBIOPICS_BASE,
    SVG_CACHE_PREFIX,
    _parse_cell_type_detail,
    _parse_cell_types_from_homepage,
    _parse_search_results,
    _parse_suggestions,
    _parse_svg_locations,
)


# ---------------------------------------------------------------------------
# _parse_cell_types_from_homepage
# ---------------------------------------------------------------------------
class TestParseCellTypesFromHomepage:
    def test_basic_extraction(self):
        html = (
            '<div data-name="Animal_cells.svg" data-title="Animal cell" '
            'data-target="name/Animal_cell">...</div>'
        )
        result = _parse_cell_types_from_homepage(html)
        assert len(result) == 1
        assert result[0]["title"] == "Animal cell"
        assert result[0]["svg_file"] == "Animal_cells.svg"
        assert result[0]["target_path"] == "name/Animal_cell"
        assert result[0]["url"] == f"{SWISSBIOPICS_BASE}/name/Animal_cell"

    def test_multiple_cell_types(self):
        html = (
            '<div data-name="Animal_cells.svg" data-title="Animal cell" '
            'data-target="name/Animal_cell"></div>'
            '<div data-name="Plant_cells.svg" data-title="Plant cell" '
            'data-target="name/Plant_cell"></div>'
            '<div data-name="Rod-shaped_bacteria.svg" data-title="Rod-shaped bacteria" '
            'data-target="name/Rod-shaped_bacteria:_one_membrane_(Gram+)"></div>'
        )
        result = _parse_cell_types_from_homepage(html)
        assert len(result) == 3
        assert result[0]["title"] == "Animal cell"
        assert result[1]["title"] == "Plant cell"
        assert result[2]["title"] == "Rod-shaped bacteria"

    def test_deduplication_by_target(self):
        html = (
            '<div data-name="Animal_cells.svg" data-title="Animal cell" '
            'data-target="name/Animal_cell"></div>'
            '<div data-name="Animal_cells.svg" data-title="Animal cell (dup)" '
            'data-target="name/Animal_cell"></div>'
        )
        result = _parse_cell_types_from_homepage(html)
        assert len(result) == 1

    def test_empty_html(self):
        assert _parse_cell_types_from_homepage("") == []

    def test_no_matches(self):
        html = "<html><body><p>No cell types here</p></body></html>"
        assert _parse_cell_types_from_homepage(html) == []

    def test_strips_whitespace(self):
        html = (
            '<div data-name="  Animal_cells.svg  " data-title="  Animal cell  " '
            'data-target="  name/Animal_cell  "></div>'
        )
        result = _parse_cell_types_from_homepage(html)
        assert result[0]["title"] == "Animal cell"
        assert result[0]["svg_file"] == "Animal_cells.svg"
        assert result[0]["target_path"] == "name/Animal_cell"


# ---------------------------------------------------------------------------
# _parse_search_results
# ---------------------------------------------------------------------------
class TestParseSearchResults:
    def test_basic_search_results(self):
        html = """
        <html><body>
        <span class="weak"> 3 matching pages </span>
        <table>
        <tr>
            <a href="/8719"><span><img src="/prime/cache1/Animal_cells.svg"/>
            <span class="edit_ok">Animal cell</span></span></a>
            <span class="loc">Mitochondrion</span>
            <span class="loc">Nucleus</span>
        </tr>
        <tr>
            <a href="/1234"><span><img src="/prime/cache1/Plant_cells.svg"/>
            <span class="edit_ok">Plant cell</span></span></a>
            <span class="loc">Chloroplast</span>
        </tr>
        </table>
        </body></html>
        """
        data = _parse_search_results(html)
        assert data["total"] == 3
        assert len(data["results"]) == 2

        r0 = data["results"][0]
        assert r0["cell_id"] == "8719"
        assert r0["title"] == "Animal cell"
        assert r0["url"] == f"{SWISSBIOPICS_BASE}/8719"
        assert r0["svg_url"] == f"{SWISSBIOPICS_BASE}/prime/cache1/Animal_cells.svg"
        assert "Mitochondrion" in r0["matched_locations"]
        assert "Nucleus" in r0["matched_locations"]

        r1 = data["results"][1]
        assert r1["cell_id"] == "1234"
        assert r1["title"] == "Plant cell"
        assert r1["matched_locations"] == ["Chloroplast"]

    def test_no_results(self):
        html = '<html><body><span class="weak"> 0 matching pages </span></body></html>'
        data = _parse_search_results(html)
        assert data["total"] == 0
        assert data["results"] == []

    def test_empty_html(self):
        data = _parse_search_results("")
        assert data["total"] == 0
        assert data["results"] == []

    def test_result_without_svg(self):
        html = """
        <span class="weak"> 1 matching page </span>
        <tr>
            <a href="/8719"><span><img src="/something/else.png"/>
            <span class="edit_ok">Animal cell</span></span></a>
        </tr>
        """
        data = _parse_search_results(html)
        assert len(data["results"]) == 1
        assert data["results"][0]["svg_url"] is None

    def test_locations_with_nested_tags(self):
        html = """
        <tr>
            <a href="/8719"><span><img src="/prime/cache1/test.svg"/>
            <span class="edit_ok">Animal cell</span></span></a>
            <span class="loc"><b>Mitochondrion</b></span>
        </tr>
        """
        data = _parse_search_results(html)
        assert data["results"][0]["matched_locations"] == ["Mitochondrion"]

    def test_singular_matching_pages(self):
        html = '<span class="weak"> 1 matching page </span>'
        data = _parse_search_results(html)
        assert data["total"] == 1


# ---------------------------------------------------------------------------
# _parse_cell_type_detail
# ---------------------------------------------------------------------------
class TestParseCellTypeDetail:
    def test_basic_detail(self):
        html = (
            '<h1 class="ctitle">Animal cell</h1>'
            '<div data-name="Animal_cells.svg"></div>'
        )
        info = _parse_cell_type_detail(html)
        assert info["title"] == "Animal cell"
        assert info["svg_file"] == "Animal_cells.svg"
        assert info["svg_url"] == f"{SWISSBIOPICS_BASE}{SVG_CACHE_PREFIX}Animal_cells.svg"

    def test_missing_title(self):
        html = '<div data-name="Animal_cells.svg"></div>'
        info = _parse_cell_type_detail(html)
        assert info["title"] == "Unknown"
        assert info["svg_file"] == "Animal_cells.svg"

    def test_missing_svg_file(self):
        html = '<h1 class="ctitle">Animal cell</h1>'
        info = _parse_cell_type_detail(html)
        assert info["title"] == "Animal cell"
        assert info["svg_file"] == ""
        assert info["svg_url"] == ""

    def test_empty_html(self):
        info = _parse_cell_type_detail("")
        assert info["title"] == "Unknown"
        assert info["svg_file"] == ""

    def test_title_with_attributes(self):
        html = (
            '<h1 id="title" class="ctitle special">Animal cell</h1>'
            '<div data-name="test.svg"></div>'
        )
        info = _parse_cell_type_detail(html)
        assert info["title"] == "Animal cell"


# ---------------------------------------------------------------------------
# _parse_svg_locations
# ---------------------------------------------------------------------------
class TestParseSvgLocations:
    SAMPLE_SVG = b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <g class="subcellular_location" id="SL0173">
    <text class="subcell_name">Mitochondrion</text>
    <text class="subcell_description">Spherical or rod-shaped organelle found in eukaryotic cells.</text>
  </g>
  <g class="subcellular_location" id="SL0243">
    <text class="subcell_name">Secreted</text>
    <text class="subcell_description">Protein secreted into the extracellular space.</text>
  </g>
  <g class="other" id="SL9999">
    <text class="subcell_name">Should not appear</text>
  </g>
</svg>
"""

    def test_basic_extraction(self):
        locations = _parse_svg_locations(self.SAMPLE_SVG)
        assert len(locations) == 2
        assert locations[0]["sl_id"] == "SL0173"
        assert locations[0]["name"] == "Mitochondrion"
        assert "Spherical" in locations[0]["description"]
        assert locations[1]["sl_id"] == "SL0243"
        assert locations[1]["name"] == "Secreted"

    def test_accepts_string_input(self):
        locations = _parse_svg_locations(self.SAMPLE_SVG.decode("utf-8"))
        assert len(locations) == 2

    def test_empty_svg(self):
        locations = _parse_svg_locations(b"<svg></svg>")
        assert locations == []

    def test_invalid_xml(self):
        locations = _parse_svg_locations(b"<not valid xml<<<")
        assert locations == []

    def test_empty_input(self):
        locations = _parse_svg_locations(b"")
        assert locations == []

    def test_deduplication_by_sl_id(self):
        svg = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <g class="subcellular_location" id="SL0173">
    <text class="subcell_name">Mitochondrion</text>
    <text class="subcell_description">First</text>
  </g>
  <g class="subcellular_location" id="SL0173">
    <text class="subcell_name">Duplicate</text>
    <text class="subcell_description">Second</text>
  </g>
</svg>
"""
        locations = _parse_svg_locations(svg)
        assert len(locations) == 1
        assert locations[0]["name"] == "Mitochondrion"

    def test_location_without_name_skipped(self):
        svg = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <g class="subcellular_location" id="SL0001">
    <text class="subcell_description">No name here</text>
  </g>
</svg>
"""
        locations = _parse_svg_locations(svg)
        assert locations == []

    def test_location_without_description(self):
        svg = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <g class="subcellular_location" id="SL0173">
    <text class="subcell_name">Mitochondrion</text>
  </g>
</svg>
"""
        locations = _parse_svg_locations(svg)
        assert len(locations) == 1
        assert locations[0]["description"] == ""

    def test_nested_groups(self):
        """Locations may be inside nested <g> elements."""
        svg = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <g class="layer">
    <g class="subcellular_location" id="SL0173">
      <text class="subcell_name">Mitochondrion</text>
      <text class="subcell_description">Found in eukaryotes.</text>
    </g>
  </g>
</svg>
"""
        locations = _parse_svg_locations(svg)
        assert len(locations) == 1
        assert locations[0]["name"] == "Mitochondrion"


# ---------------------------------------------------------------------------
# _parse_suggestions
# ---------------------------------------------------------------------------
class TestParseSuggestions:
    def test_basic_suggestions(self):
        html = (
            '<span>mitochondrion</span>'
            '<span>mitochondrial inner membrane</span>'
            '<span>mitochondrial matrix</span>'
        )
        suggestions = _parse_suggestions(html)
        assert len(suggestions) == 3
        assert "mitochondrion" in suggestions
        assert "mitochondrial inner membrane" in suggestions

    def test_empty_html(self):
        assert _parse_suggestions("") == []

    def test_strips_inner_tags(self):
        html = '<span><b>mitochondrion</b></span>'
        suggestions = _parse_suggestions(html)
        assert suggestions == ["mitochondrion"]

    def test_skips_empty_spans(self):
        html = '<span>   </span><span>mitochondrion</span>'
        suggestions = _parse_suggestions(html)
        assert suggestions == ["mitochondrion"]
