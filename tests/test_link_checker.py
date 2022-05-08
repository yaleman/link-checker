""" blep """

from link_checker import handle_relative_link

def test_handle_relative_link() -> None:
    """ tests handle_relative_link """

    result = handle_relative_link(
        "https://google.com:12345/foo/bar",
        "/hello"
    )

    assert result == "https://google.com:12345/hello"

    result = handle_relative_link(
        "http://google.com/foo/bar",
        "/hello"
    )

    assert result == "http://google.com/hello"
