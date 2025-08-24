#!/bin/bash

# ⚠️ ⚠️ ⚠️ CRITICAL WARNING FOR AI AGENTS ⚠️ ⚠️ ⚠️
#
# THIS FILE IS STRICTLY FORBIDDEN FROM MODIFICATION BY AI AGENTS
#
# - DO NOT modify this script under ANY circumstances
# - DO NOT comment out any checks or warnings
# - DO NOT add conditional bypasses or workarounds
# - DO NOT change linting rules or configurations
#
# This script enforces project quality standards and must remain unchanged.
# Any violations will result in immediate termination of agent execution.
# If linting fails, FIX THE CODE, not this script.
#
# ⚠️ ⚠️ ⚠️ END CRITICAL WARNING ⚠️ ⚠️ ⚠️

source "$(dirname "${BASH_SOURCE[0]}")"/_check_repo.sh
source "$(dirname "${BASH_SOURCE[0]}")"/_check_venv.sh

# Turn on error checking for the init section.
set -e

# Set the max line lenghth
LEN=100
JOBS=8

FILES=$(git ls-files '*.py')
FILES_FILTERED=$(git ls-files '*.py' | grep -v tests)
if [[ "x$1" != "x" ]]; then
		FILES="$*"
    FILES_FILTERED="$*"
fi

declare -a EXCLUDE DIRS
EXCLUDE=(".venv")
DIRS=(".")
EXCLUDE_opt=""
for dir in "${DIRS[@]}"; do
		for excl in "${EXCLUDE[@]}"; do
				EXCLUDE_opt+="--exclude ${dir}/${excl} "
		done
done

declare -a PYLINT_PLUGINS
PYLINT_PLUGINS=(
		"pylint.extensions.bad_builtin"
		"pylint.extensions.broad_try_clause"
		"pylint.extensions.check_elif"
		"pylint.extensions.code_style"
		"pylint.extensions.comparison_placement"
		"pylint.extensions.confusing_elif"
		"pylint.extensions.consider_ternary_expression"
		"pylint.extensions.dict_init_mutate"
		"pylint.extensions.docparams"
		"pylint.extensions.docstyle"
		"pylint.extensions.empty_comment"
		"pylint.extensions.eq_without_hash"
		"pylint.extensions.for_any_all"
		"pylint.extensions.magic_value"
		"pylint.extensions.mccabe"
		"pylint.extensions.overlapping_exceptions"
		"pylint.extensions.redefined_loop_name"
		"pylint.extensions.redefined_variable_type"
		"pylint.extensions.set_membership"
		"pylint.extensions.typing"
		"pylint.extensions.while_used"
		"pylint_htmf"
#		"pylint_ml"
		"pylint_pydantic"
#		"pylint_pytest"
)
PYLINT_plugopt=""
for plug in "${PYLINT_PLUGINS[@]}"; do
		if [[ ${PYLINT_plugopt} == "" ]]; then
				PYLINT_plugopt="--load-plugins=${plug}"
		else
				PYLINT_plugopt+=",${plug}"
		fi
done

source .venv/bin/activate

function wrap_local_cmd {
		# We run all the local commands with uv run, this:
		#  - forces the correct python
		#  - makes sure all the packages are correct
		#  - runs in an isolated environment in case there are changes in the outside
		#echo "linter: $1"
		uv run --quiet --all-extras --isolated --locked "$@"
		return $?
}

FAILED=0
function fail_bad {
    wrap_local_cmd "$@"
		if [[ $? != 0 ]]; then
				FAILED=1
		fi
}
function fail_ok {
		wrap_local_cmd "$@"
}

# Runs a command and only shows its output if it fails.
function run_silent_on_pass {
    local cmd_output
    # Create a temporary file to hold the command's output.
    cmd_output=$(mktemp)

    # Run the command, redirecting both stdout and stderr to the temp file.
    # The return code is captured for the final check.
    "$@" >"$cmd_output" 2>&1
    local exit_code=$?

    # If the command failed (exit_code is not 0), print the captured output.
    if [[ ${exit_code} -ne 0 ]]; then
        cat "$cmd_output"
    fi

    # Clean up the temporary file.
    rm "$cmd_output"

    # Return the original exit code of the command.
    return ${exit_code}
}

# Turn off error checking, we manually check returns from here on out.
set +e

# Update the lock file if need, this is fast and keeps it up to date.
uv lock --quiet

# Initial black format pass, so that line numbers make sense in errors consistently.
fail_ok black -l ${LEN} -q ${FILES}

# Initial ruff pass to auto-fix things, no reporting.
fail_ok ruff check ${EXCLUDE_opt} --respect-gitignore --ignore F401 --output-format=concise --line-length=${LEN} --target-version=py312 --fix --no-unsafe-fixes --fix-only --silent ${FILES}

# No we report anything we could not auto-fix
fail_bad ruff check ${EXCLUDE_opt} --respect-gitignore --ignore F401 --output-format=concise --line-length=${LEN} --target-version=py312 --fix --no-unsafe-fixes --no-show-fixes --quiet ${FILES}

# Check the github workflows
if command -v actionline >/dev/null 2>&1; then
  fail_bad actionlint .github/workflows/*.yml
fi

# Reformat consistently after potential ruff fix changes, no we fail if we can't format.
fail_bad black -l ${LEN} -q ${FILES}

# Sort the imports.
fail_bad isort --profile google --py 312 --virtual-env .venv --remove-redundant-aliases --ac --srx --gitignore --ca --cs -e -q -l ${LEN} ${FILES}

# Flake8 is largely redundant but has some unique plugins we use.
fail_bad python -m flake8 --max-line-length=${LEN} --ignore=F401,W503,E128,E203,E501 --jobs=${JOBS} ${FILES}

# Bandit for security scanning.
fail_bad bandit -q -ll -c pyproject.toml ${FILES}

# Vulture for dead code identification.
fail_bad vulture --min-confidence=80 ${FILES}

# Pyright
fail_bad pyright ${FILES_FILTERED}

# Mypy in semi-strict mode.
fail_bad mypy  ${EXCLUDE_opt} --exclude-gitignore --sqlite-cache --strict --warn-redundant-casts --warn-unused-ignores --no-implicit-reexport --show-error-codes --show-column-numbers --warn-unreachable --disallow-untyped-decorators --disallow-any-generics --check-untyped-defs ${FILES_FILTERED}

# pylint for the rest.
fail_bad pylint \
				 --fail-on=W \
				 --jobs=${JOBS} \
				 --output-format=parseable \
				 --enable-all-extensions ${PYLINT_plugopt} \
				 --bad-functions=print \
				 --max-line-length=${LEN} \
				 --max-complexity=10 \
				 --min-similarity-lines=10 \
				 --ignore-long-lines='^\\s*(# )?<?https?://\\S+>?$' \
				 --disable=too-many-try-statements,no-else-return,suppressed-message,locally-disabled,empty-comment,no-self-use,protected-access,too-few-public-methods,consider-alternative-union-syntax,line-too-long \
				 --fail-under=9.5 \
				 ${FILES}

# Run pytest, capturing output and only showing it on failure.
run_silent_on_pass uv run --quiet --all-extras --isolated --locked pytest --no-cov -p no:allure_pytest -p no:allure_pytest_bdd -m smoke -c /dev/null
if [[ $? != 0 ]]; then
    FAILED=1
fi

if [[ $FAILED == 1 ]]; then
		echo "❌ FAILED running linters. You are not ready to commit."
		echo "  Treat all warnings as errors regardless of what you think their severity or importance is."
    echo "   - all lint warnings are CRITICAL in this project."
		echo "   - commits with ANY lint warnings will be denied automatically."
		echo "   - it is always possible to write lint free versions of code."
		exit 1
fi
echo "✅ All lint checks passed!"
exit 0
