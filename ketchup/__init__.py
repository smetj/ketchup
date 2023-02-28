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

import json
import re
import sys
from typing import Iterator, List

import arrow
import click
import yaml
from jsonpath import JSONPath
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from rich import box
from rich.console import Console
from rich.table import Table
from slack_sdk import WebClient

CONFIG_SCHEMA = {
    "type": "array",
    "minLength": 1,
    "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string"},
            "enable": {"type": "boolean"},
            "channels": {"type": "array", "minLength": 1},
            "days_back": {"type": "integer"},
            "done_marker": {"type": "string"},
            "field": {"type": "string"},
            "ignore_users": {"type": "array"},
            "query": {"type": "string"},
            "regex_substring": {"type": ["string", "null"]},
            "regex_filter": {"type": "string"},
        },
        "required": [
            "name",
            "enable",
            "channels",
            "days_back",
            "done_marker",
            "field",
            "ignore_users",
            "query",
            "regex_substring",
            "regex_filter",
        ],
    },
}


def validate_config(config):

    try:
        validate(config, CONFIG_SCHEMA)
    except ValidationError as err:
        first_line = str(err).split("\n")[0]
        print(f"Invalid config file. Reason: {first_line}")
        sys.exit(1)


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
    table.add_column("Type", justify="left", style="red")

    for item in remove_leading_dupes(data, 3):
        table.add_row(*item)

    return table


def build_slack_query(
    search_term: str,
    channels: List[str],
    after_date: str,
    ignore_users: List[str],
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

    if ignore_users != []:
        query_ignore_users = " ".join([f"-from:{user}" for user in ignore_users])
    else:
        query_ignore_users = ""

    query = f"{search_term} {query_channels} after:{after_date} -has:{done_marker} {query_ignore_users}"
    return query


def query_slack(
    token: str, query: str, field: str, dump_responses: bool
) -> Iterator[tuple[str, str, str, str, str]]:
    """
    Query slack

    Args:
        - token: The User OAuth token to authenticate, requires search:read
        - query: The query to execute
        - field: The field selector in JSONpath syntax to select the field to return.

    Yields:
        - A record containing date, channel_name, username, permalink, message

    """

    client = WebClient(token=token)

    for item in client.search_messages(query=query):

        for message in item["messages"]["matches"]:
            if dump_responses:
                print(json.dumps(message))
            yield (
                arrow.get(float(message["ts"])).format("YYYY-MM-DD"),
                message["channel"]["name"],
                message["username"],
                message["permalink"],
                JSONPath(field).parse(message)[0],
            )


@click.command()
@click.option(
    "--token",
    required=True,
    envvar="KETCHUP_TOKEN",
    help="The Slack token to authenticate. Requires scope search:read.",
)
@click.option(
    "--config",
    "config_file",
    required=True,
    envvar="KETCHUP_QUERY_FILE",
    help="The config file containing the queries to execute.",
)
@click.option(
    "--dump_responses",
    required=False,
    is_flag=True,
    envvar="KETCHUP_DUMP_RESPONSES",
    help="When defined dumps the Slack message format. Useful to debug the JSONpath syntax.",
)
def main(token, config_file, dump_responses):

    with open(config_file, "r") as config_fh:
        config = yaml.safe_load(config_fh)

    validate_config(config)

    results = []

    for search in config:

        if search["enable"]:
            slack_query = build_slack_query(
                search_term=search["query"],
                channels=search["channels"],
                after_date=arrow.utcnow()
                .shift(days=0 - int(search["days_back"]))
                .format("YYYY-MM-DD"),
                ignore_users=search["ignore_users"],
                done_marker=search["done_marker"],
            )

            for date, channel, username, permalink, message in query_slack(
                token, slack_query, search["field"], dump_responses
            ):
                if re.search(search["regex_filter"], message):
                    if search["regex_substring"] is not None:
                        try:
                            message = re.search(search["regex_substring"], message).group(1)
                        except Exception as err:
                            message += f" (unable to extract 1st group of regex {search['regex_substring']} Reason: {err})"

                    # remove empty lines
                    message = re.sub(r"\n\s*\n", "\n", message)
                    results.append(
                        [
                            date,
                            channel,
                            username,
                            make_clickable(permalink, message),
                            search["name"],
                        ]
                    )

    table = build_table(results)

    console = Console()
    console.print(table)


if __name__ == "__main__":
    main()
