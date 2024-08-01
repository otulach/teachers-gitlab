#!/bin/bash

# Get release notes from change log file.

set -ueo pipefail

get_changelog_for() {
    # Find text between header lines and remove those header lines
    sed -n -e "/^## v${1} - 20[0-9][0-9]-[01][0-9]-[0123][0-9]$/,/^## v/{/^## v/d;p}"
}

strip_empty_lines() {
    # https://unix.stackexchange.com/a/552195
    sed -e '/./,$!d' -e :a -e '/^\n*$/{$d;N;ba' -e '}'
}

if [ -z "${1:-}" ]; then
    version="$( python3 -c 'import tomllib, sys; print(tomllib.loads(sys.stdin.read())["project"]["version"])' <pyproject.toml )"
else
    version="$1"
fi

echo '```'
echo "pip install teachers-gitlab==$version"
echo '```'
echo

get_changelog_for "$version" < "CHANGELOG.md" | strip_empty_lines
