# ketchup

A CLI to keep track of unhandled Slack questions.

Keeping track of unanswered questions on Slack can be time consuming, tedious
and difficult to keep track of. This tool allows to query for questions across
multiple channels which haven't been marked as handled using some emoji.

## Installation

### Directly from source

```
python setup.py install
```

### Directly from Github using pip

Install the latest version:
```
pip install git+https://github.com/smetj/ketchup.git
```

Install a specific version:
```
pip install git+https://github.com/smetj/ketchup.git@v0.1.2
```


## Usage
```
Usage: ketchup [OPTIONS]

Options:
  --token TEXT         The Slack token to authenticate. Requires scope
                       search:read.  [required]
  --query TEXT         The Slack query term.
  --channels TEXT      A comma separate list of Slack channels to query.
                       [required]
  --days-back INTEGER  The number of days to go back when querying.
  --ignore-users TEXT  A comma separated list of users to exclude from the
                       search results.
  --done-marker TEXT   The emoji used to ignore otherwise matching messages.
  --regex-filter TEXT  An additional (regex) filter to apply to the returned
                       messages.
  --help               Show this message and exit.
```

## Misc

- Each option is available as an environment variable such as `KETCHUP_TOKEN`.
- By default `ketchup` queries for messages containing a `?`. This can be
  overridden by `--query`.
- By default `ketchup` considers a question handled when the otherwise
  matching message is tagged with the `:done:` emoji.
- `--regex-filter` is an regex based filter applied to the returned query
  results for additional filtering. The default value is `\?(\s+|$)` which
  basically means `?` should be followed with at least some whites space
  character or a the end of a line and therefor not part of some URL or
  something similar.

## CAVEAT

The default values of `ketchup` may or may not catch all the questions users
ask on a channel. Your mileage might vary. You have been warned.

## Bugs and support

Just submit a Github issue or create a PR.
