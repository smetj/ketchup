#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  MIT License
#
#  Copyright (c) 2023 Jelle Smet
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import re
from typing import Iterator, List

import arrow
import click
from rich import box
from rich.console import Console
from rich.table import Table
from slack_sdk import WebClient


def remove_leading_dupes(data, level: int):
    """
    Removes repeating values within the same column.

    Args:
        - data: The table to remove leading dupes from.
        - level: How many columns deep to remove leading dupes.

    Returns:
        - The provided dataset without any leading dupes.
    """

    data.sort(key=lambda t: [t[x] for x in range(level)])

    for index in range(level):
        lead = None
        for item in data:
            if item[index] != lead:
                lead = item[index]
            else:
                if index == 0 or item[index - 1] == "":
                    item[index] = ""
    return data


def make_clickable(url: str, text: str) -> str:
    """
    Create a clickable link for the terminal using ANSI escape codes.

    Args:
        - url: The URL address.
        - text: The links text to display.

    Returns:
        - The link and text in ANSI escaped format.
    """

    return f"[link={url}]{text}[/link]"


def build_table(data: List[List[str]]) -> Table:
    """
    Converts `data` into a  table.

    Args:
        - data: The data to populate the table.

    Returns:
        - The table representation of the provided data.

    """

    table = Table(
        title="Slack questions to catch up with.", box=box.ASCII, show_lines=True
    )
    table.add_column("Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Channel", style="magenta")
    table.add_column("User", justify="left", style="green")
    table.add_column("Message", justify="left", style="green")

    for item in remove_leading_dupes(data, 3):
        table.add_row(*item)

    return table


def build_slack_query(
    search_term: str,
    channels: List[str],
    after_date: str,
    ignore_users: str,
    done_marker: str,
) -> str:
    """
    Builds a Slack search query using the provided parameters.

    Args:
        - search_term: The term to search for.
        - channels: The channels to query for `term`.
        - after_date: Limit the results to messages newer than the provided
          date (YYYY-MM-DD).
        - ignore_users: Exclude matching messages for the provided users.
        - done_marker: Exclude messages tagged with this emoji.

    Returns:
        - The Slack search query.
    """

    query_channels = " ".join([f"in:{channel}" for channel in channels])
    query_ignore_users = " ".join([f"-from:{user}" for user in ignore_users])
    return f"{search_term} {query_channels} after:{after_date} -has:{done_marker} {query_ignore_users}"


def query_slack(token: str, query: str) -> Iterator[tuple[str, str, str, str, str]]:
    """
    Query slack

    Args:
        - token: The User OAuth token to authenticate, requires search:read
        - query: The query to execute

    Yields:
        - A record containing date, channel_name, username, permalink, message

    """

    client = WebClient(token=token)

    for item in client.search_messages(query=query):
        for message in item["messages"]["matches"]:
            text = " ".join(message["text"].split())
            yield (
                arrow.get(float(message["ts"])).format("YYYY-MM-DD"),
                message["channel"]["name"],
                message["username"],
                message["permalink"],
                text,
            )


@click.command()
@click.option(
    "--token",
    required=True,
    envvar="KETCHUP_TOKEN",
    help="The Slack token to authenticate. Requires scope search:read.",
)
@click.option(
    "--query",
    default="?",
    envvar="KETCHUP_QUERY",
    help="The Slack query term.",
)
@click.option(
    "--channels",
    required=True,
    envvar="KETCHUP_CHANNELS",
    help="A comma separate list of Slack channels to query.",
)
@click.option(
    "--days-back",
    default=7,
    envvar="KETCHUP_DAYS_BACK",
    help="The number of days to go back when querying.",
)
@click.option(
    "--ignore-users",
    envvar="KETCHUP_IGNORE_USERS",
    default="",
    help="A comma separated list of users to exclude from the search results.",
)
@click.option(
    "--done-marker",
    envvar="KETCHUP_DONE_MARKER",
    default=":done:",
    help="The emoji used to ignore otherwise matching messages.",
)
@click.option(
    "--regex-filter",
    envvar="KETCHUP_REGEX_FILTER",
    default=r"\?(\s+|$)",
    help="An additional (regex) filter to apply to the returned messages.",
)
def main(token, query, channels, days_back, ignore_users, done_marker, regex_filter):

    results = []

    query = build_slack_query(
        search_term="?",
        channels=[channel.strip() for channel in channels.split(",")],
        after_date=arrow.utcnow().shift(days=-7).format("YYYY-MM-DD"),
        ignore_users=[user.strip() for user in ignore_users.split(",")],
        done_marker=done_marker,
    )

    for date, channel, username, permalink, message in query_slack(
        token,
        query,
    ):
        if re.search(regex_filter, message):
            results.append(
                [date, channel, username, make_clickable(permalink, message)]
            )

    table = build_table(results)

    console = Console()
    console.print(table)


if __name__ == "__main__":
    main()
