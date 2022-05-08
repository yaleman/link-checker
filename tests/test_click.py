""" tests using click """

from typing import Any

from click.testing import CliRunner
from link_checker import cli


def test_click() -> None:
    """ tests the help function """

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result

def test_local(simplehttpserver: Any) -> None: # pylint: disable=unused-argument
    """ testing """
    runner = CliRunner()
    result = runner.invoke(cli, ["http://localhost:8000"] )
    assert result
    print(result.output)
