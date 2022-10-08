""" Checks a given links' links to see if they're valid. """

import asyncio
import sys
from typing import List, Optional, Union
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup # type: ignore[import]
import bs4.element # type: ignore[import]
import click
from loguru import logger


def setup_logging(debug: bool = False) -> None:
    """sets up logging"""
    if not debug:
        logger.remove()
        logger.add(sink=sys.stdout, level="INFO")


def handle_relative_link(
    original_link: str,
    relative_path: str,
) -> str:
    """hand it the original link and a relative link and it'll make a new one"""

    parsed_original = urlparse(original_link)

    if parsed_original.port:
        port_str = f":{parsed_original.port}"
    else:
        port_str = ""
    new_link = f"{parsed_original.scheme}://{parsed_original.hostname}{port_str}{relative_path}"
    return new_link


def find_links(
    original_link: str,
    page_content: bytes,
    object_type: str = "a",
) -> List[bs4.element.Tag]:
    """finds the links and checks them"""
    soup = BeautifulSoup(page_content, "lxml")
    links = soup.find_all(object_type)
    results_to_return = []
    for link in links:
        if not link.has_attr("href") or link.get("href").startswith("#"):
            logger.debug("Skipping this as it's not an external link: {}", link)
            continue
        if link["href"].strip() == original_link.strip():
            logger.debug("Skipping this as it's the original link: {}", link["href"])
            continue
        if link["href"].strip().lower().startswith("/"):
            results_to_return.append(handle_relative_link(original_link, link["href"]))
            continue

        if not link["href"].strip().lower().startswith("http"):
            logger.warning("Skipping this as it's not a http(s): {}", link["href"])
            continue
        results_to_return.append(link["href"])
    return results_to_return


async def check_link(
    target_link: Union[bs4.element.Tag, str], method: str = "HEAD"
) -> bool:
    """checks an individual link"""

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"
    }
    try:
        async with aiohttp.ClientSession() as check_session:
            async with check_session.request(
                method, target_link, headers=headers
            ) as response:
                if response.status <= 400:
                    logger.success(
                        "{} {}",
                        response.status,
                        target_link,
                    )
                    return True
                if response.status == 405:
                    logger.warning(
                        "{} {} - HEAD refused - retrying with GET",
                        response.status,
                        target_link,
                    )
                    if method == "HEAD":
                        result = await check_link(target_link, method="GET")
                        return result
                if response.status == 999:
                    logger.warning(
                        "{} {} - probably linkedin being weird - retrying with get",
                        response.status,
                        target_link,
                    )
                    if method == "HEAD":
                        result = await check_link(target_link, method="GET")
                        return result
                logger.error(
                    "{} = {} {}",
                    method,
                    response.status,
                    target_link,
                )
                return False
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Failed to pull {}: {} - {}", target_link, type(error), error)
    return False


async def process_page(target_url: str) -> None:
    """checks the page"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(target_url) as response:
                logger.debug("Status: {}", response.status)
                html = await response.content.read()
                logger.debug("Body: {}", html[:15])
                response.raise_for_status()
        except aiohttp.client_exceptions.ClientConnectorSSLError as ssl_error:
            logger.error("Failed HTTPS connection to '{}': {}", target_url, ssl_error)
            return

        links = find_links(target_url, html)

        link_results = await asyncio.gather(*[check_link(link) for link in links])
        logger.debug(link_results)


@click.command()
@click.argument("url")
def cli(url: Optional[str] = None) -> None:
    """Link checker pulls a given URL then goes looking for links off that page, then checks if they load."""
    if url is None:
        return
    asyncio.run(process_page(url))
