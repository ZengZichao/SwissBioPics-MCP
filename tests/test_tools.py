"""Unit tests for MCP tool functions (with mocked HTTP)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from swissbiopics_mcp.server import (
    SWISSBIOPICS_BASE,
    SVG_CACHE_PREFIX,
    get_cell_svg,
    get_cell_type_detail,
    get_cell_types,
    get_location_detail,
    get_search_suggestions,
    get_subcellular_locations,
    get_swissbiopics_info,
    search_locations,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
HOMEPAGE_HTML = (
    '<div data-name="Animal_cells.svg" data-title="Animal cell" '
    'data-target="name/Animal_cell"></div>'
    '<div data-name="Plant_cells.svg" data-title="Plant cell" '
    'data-target="name/Plant_cell"></div>'
)

SEARCH_HTML = """
<span class="weak"> 2 matching pages </span>
<tr>
    <a href="/8719"><span><img src="/prime/cache1/Animal_cells.svg"/>
    <span class="edit_ok">Animal cell</span></span></a>
    <span class="loc">Mitochondrion</span>
</tr>
<tr>
    <a href="/1234"><span><img src="/prime/cache1/Plant_cells.svg"/>
    <span class="edit_ok">Plant cell</span></span></a>
    <span class="loc">Chloroplast</span>
</tr>
"""

DETAIL_HTML = (
    '<h1 class="ctitle">Animal cell</h1>'
    '<div data-name="Animal_cells.svg"></div>'
)

SUGGEST_HTML = (
    '<span>mitochondrion</span>'
    '<span>mitochondrial inner membrane</span>'
)

SAMPLE_SVG = b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <g class="subcellular_location" id="SL0173">
    <text class="subcell_name">Mitochondrion</text>
    <text class="subcell_description">Spherical or rod-shaped organelle.</text>
  </g>
  <g class="subcellular_location" id="SL0243">
    <text class="subcell_name">Secreted</text>
    <text class="subcell_description">Protein secreted outside the cell.</text>
  </g>
</svg>
"""

SAMPLE_SVG_STR = SAMPLE_SVG.decode("utf-8")

HELP_HTML = """
<h3>What is SwissBioPics?</h3>
<p>A library of interactive biological images.</p>
<h3>How can I use SwissBioPics?</h3>
<p>Via the website or NPM package.</p>
<p>Creative Commons Attribution 4.0 International (CC BY 4.0)</p>
"""


# ---------------------------------------------------------------------------
# search_locations
# ---------------------------------------------------------------------------
class TestSearchLocations:
    @pytest.mark.asyncio
    async def test_empty_query(self):
        result = await search_locations("")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_whitespace_query(self):
        result = await search_locations("   ")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_successful_search(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SEARCH_HTML
            result = await search_locations("mitochondrion")
        assert "2 matching cell type" in result
        assert "Animal cell" in result
        assert "Plant cell" in result
        assert "8719" in result
        # Verify URL was built correctly
        call_args = mock_fetch.call_args[0][0]
        assert call_args.startswith(f"{SWISSBIOPICS_BASE}/search?query=")

    @pytest.mark.asyncio
    async def test_no_results(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = '<span class="weak"> 0 matching pages </span>'
            result = await search_locations("nonexistent")
        assert "No results" in result

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await search_locations("test")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_url_encoding(self):
        """Verify query parameters are properly URL-encoded."""
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SEARCH_HTML
            await search_locations('"golgi stack"')
        url = mock_fetch.call_args[0][0]
        # The URL should NOT contain raw spaces or quotes
        assert " " not in url.split("query=")[1]
        assert '"' not in url


# ---------------------------------------------------------------------------
# get_search_suggestions
# ---------------------------------------------------------------------------
class TestGetSearchSuggestions:
    @pytest.mark.asyncio
    async def test_empty_query(self):
        result = await get_search_suggestions("")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_successful_suggestions(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SUGGEST_HTML
            result = await get_search_suggestions("mito")
        assert "mitochondrion" in result
        assert "mitochondrial inner membrane" in result

    @pytest.mark.asyncio
    async def test_no_suggestions(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ""
            result = await get_search_suggestions("xyz")
        assert "No suggestions" in result

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_search_suggestions("mito")
        assert "Error" in result


# ---------------------------------------------------------------------------
# get_cell_types
# ---------------------------------------------------------------------------
class TestGetCellTypes:
    @pytest.mark.asyncio
    async def test_successful_list(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = HOMEPAGE_HTML
            result = await get_cell_types()
        assert "2 available cell types" in result
        assert "Animal cell" in result
        assert "Plant cell" in result

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_cell_types()
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_parse_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "<html><body>No cell types</body></html>"
            result = await get_cell_types()
        assert "Error" in result


# ---------------------------------------------------------------------------
# get_cell_type_detail
# ---------------------------------------------------------------------------
class TestGetCellTypeDetail:
    @pytest.mark.asyncio
    async def test_empty_identifier(self):
        result = await get_cell_type_detail("")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_numeric_id(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = DETAIL_HTML
            result = await get_cell_type_detail("8719")
        assert "Animal cell" in result
        assert "Animal_cells.svg" in result
        url = mock_fetch.call_args[0][0]
        assert url == f"{SWISSBIOPICS_BASE}/8719"

    @pytest.mark.asyncio
    async def test_name_identifier(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = DETAIL_HTML
            result = await get_cell_type_detail("Animal_cell")
        assert "Animal cell" in result
        url = mock_fetch.call_args[0][0]
        assert url == f"{SWISSBIOPICS_BASE}/name/Animal_cell"

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_cell_type_detail("8719")
        assert "Error" in result


# ---------------------------------------------------------------------------
# get_cell_svg
# ---------------------------------------------------------------------------
class TestGetCellSvg:
    @pytest.mark.asyncio
    async def test_empty_identifier(self):
        result = await get_cell_svg("")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_direct_svg_filename(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_cell_svg("Animal_cells.svg")
        assert "<svg" in result or "SL0173" in result
        url = mock_fetch.call_args[0][0]
        assert url == f"{SWISSBIOPICS_BASE}{SVG_CACHE_PREFIX}Animal_cells.svg"

    @pytest.mark.asyncio
    async def test_numeric_id(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            # First call returns detail HTML, second returns SVG
            mock_fetch.side_effect = [DETAIL_HTML, SAMPLE_SVG_STR]
            result = await get_cell_svg("8719")
        assert "<svg" in result or "SL0173" in result

    @pytest.mark.asyncio
    async def test_name_identifier(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [DETAIL_HTML, SAMPLE_SVG_STR]
            result = await get_cell_svg("Animal_cell")
        assert "<svg" in result or "SL0173" in result

    @pytest.mark.asyncio
    async def test_detail_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_cell_svg("8719")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_svg_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [DETAIL_HTML, None]
            result = await get_cell_svg("8719")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_no_svg_file_in_detail(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = '<h1 class="ctitle">Test</h1>'
            result = await get_cell_svg("8719")
        assert "Error" in result


# ---------------------------------------------------------------------------
# get_subcellular_locations
# ---------------------------------------------------------------------------
class TestGetSubcellularLocations:
    @pytest.mark.asyncio
    async def test_empty_identifier(self):
        result = await get_subcellular_locations("")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_svg_filename(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_subcellular_locations("Animal_cells.svg")
        assert "SL0173" in result
        assert "Mitochondrion" in result
        assert "Secreted" in result
        assert "2 locations" in result

    @pytest.mark.asyncio
    async def test_numeric_id(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [DETAIL_HTML, SAMPLE_SVG_STR]
            result = await get_subcellular_locations("8719")
        assert "SL0173" in result

    @pytest.mark.asyncio
    async def test_no_locations_in_svg(self):
        empty_svg = '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = empty_svg
            result = await get_subcellular_locations("test.svg")
        assert "No subcellular locations" in result

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_subcellular_locations("test.svg")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_long_description_truncated(self):
        long_desc = "A" * 200
        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g class="subcellular_location" id="SL0001">'
            f'<text class="subcell_name">Test</text>'
            f'<text class="subcell_description">{long_desc}</text>'
            '</g></svg>'
        )
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = svg
            result = await get_subcellular_locations("test.svg")
        assert "..." in result


# ---------------------------------------------------------------------------
# get_location_detail
# ---------------------------------------------------------------------------
class TestGetLocationDetail:
    @pytest.mark.asyncio
    async def test_empty_sl_id(self):
        result = await get_location_detail("")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_find_location_by_sl_id(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_location_detail("SL0173", "Animal_cells.svg")
        assert "SL0173" in result
        assert "Mitochondrion" in result
        assert "Spherical" in result

    @pytest.mark.asyncio
    async def test_sl_id_with_dash(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_location_detail("SL-0173", "Animal_cells.svg")
        assert "SL0173" in result
        assert "Mitochondrion" in result

    @pytest.mark.asyncio
    async def test_sl_id_lowercase(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_location_detail("sl0173", "Animal_cells.svg")
        assert "SL0173" in result

    @pytest.mark.asyncio
    async def test_sl_id_without_prefix(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_location_detail("0173", "Animal_cells.svg")
        assert "SL0173" in result

    @pytest.mark.asyncio
    async def test_location_not_found(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = SAMPLE_SVG_STR
            result = await get_location_detail("SL9999", "Animal_cells.svg")
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_default_cell_identifier(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [DETAIL_HTML, SAMPLE_SVG_STR]
            result = await get_location_detail("SL0173")
        assert "Mitochondrion" in result
        # Verify default cell ID 8719 was used
        first_url = mock_fetch.call_args_list[0][0][0]
        assert first_url == f"{SWISSBIOPICS_BASE}/8719"

    @pytest.mark.asyncio
    async def test_location_without_description(self):
        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g class="subcellular_location" id="SL0001">'
            '<text class="subcell_name">Test Location</text>'
            '</g></svg>'
        )
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = svg
            result = await get_location_detail("SL0001", "test.svg")
        assert "no description available" in result


# ---------------------------------------------------------------------------
# get_swissbiopics_info
# ---------------------------------------------------------------------------
class TestGetSwissbiopicsInfo:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = HELP_HTML
            result = await get_swissbiopics_info()
        assert "SwissBioPics" in result
        assert "CC BY 4.0" in result

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_swissbiopics_info()
        assert "SwissBioPics" in result
        assert "CC BY 4.0" in result
        assert "PMID" in result

    @pytest.mark.asyncio
    async def test_fallback_on_partial_html(self):
        with patch("swissbiopics_mcp.server._fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "<html><body>Nothing useful</body></html>"
            result = await get_swissbiopics_info()
        assert "SwissBioPics" in result
