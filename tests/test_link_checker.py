""" blep """

import pytest

from link_checker import check_link, handle_relative_link


def test_handle_relative_link() -> None:
    """tests handle_relative_link"""

    result = handle_relative_link("https://yaleman.org:12345/foo/bar", "/hello")

    assert result == "https://yaleman.org:12345/hello"

    result = handle_relative_link("http://yaleman.org/foo/bar", "/hello")

    assert result == "http://yaleman.org/hello"


@pytest.mark.asyncio
async def test_functionality() -> None:
    """tests it actually works"""

    result = await check_link("https://yaleman.org/")
    assert result
