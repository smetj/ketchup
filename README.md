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
pip install git+https://github.com/smetj/ketchup.git@0.2.0
```


## Usage
```
Usage: ketchup [OPTIONS]

Options:
  --token TEXT      The Slack token to authenticate. Requires scope
                    search:read.  [required]
  --config TEXT     The config file containing the queries to execute.
                    [required]
  --dump_responses  When defined dumps the Slack message format. Useful to
                    debug the JSONpath syntax.
  --help            Show this message and exit.
```


## Configuration format

Ketchup requires a YAML configuration file using the following format:

```yaml
- name: User
  enable: true
  channels:
    - support-channel
  days_back: 7
  done_marker: ':done:'
  field: $.text
  ignore_users:
    - smetj
  query: '?'
  regex_substring: null
  regex_filter: \?(\s+|$)
- name: PR
  enable: true
  channels:
    - github-messages
  days_back: 7
  done_marker: ':done:'
  field: $.attachments.0.title
  ignore_users: []
  query: Pull request opened by
  regex_substring: '\d\s(.*)?>'
  regex_filter: .*
```

### Parameters

- `name`: A name used to identify the query result in the overview.
- `enable`: Enables the query when set to `true` otherwise it's skipped.
- `channels`: A list of channels to query. Should contain at least one entry.
- `days_back`: Defines the amount of days back to query for results.
- `done_marker`: The emoji which indicates to ignore a message.
- `field`: Which field to show in the overview in JSONPath format.
- `ignore_users`: A list of users to ignore. Can be empty.
- `query`: The term to query for in Slack.
- `regex_substring`: The sub-string to extract from a message. Can be useful to
  cleanup output of predictable messages.
- `regex_filter`: An filter which has to match the content of the field found
  by `field`.

## Tips

- The `field` value requires [JSONPath
  format](https://www.baeldung.com/guide-to-jayway-jsonpath). Use the
  `--dump_responses` parameter to get insight into the complete message to
  which the JSONPath query runs.

## CAVEAT

The default values of `ketchup` may or may not catch all the questions users
ask on a channel. Your mileage might vary.

## Bugs and support

Just submit a Github issue or create a PR.
