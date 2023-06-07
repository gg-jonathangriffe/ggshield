"""
This module defines options which should be available on all iac scan subcommands.

To use it:
- Add the `@add_common_iac_scan_options()` decorator after all the `click.option()`
    calls of the command function.
- Add a `**kwargs: Any` argument to the command function.

The `kwargs` argument is required because due to the way click works,
`add_common_options()` adds an argument for each option it defines.
"""
from pathlib import Path
from typing import Any, Callable, Sequence

import click

from ggshield.cmd.common_options import add_common_options, json_option
from ggshield.iac.policy_id import POLICY_ID_PATTERN, validate_policy_id


AnyFunction = Callable[..., Any]

_exit_zero_option = click.option(
    "--exit-zero",
    is_flag=True,
    help="Always return 0 (non-error) status code.",
)

_minimum_severity_option = click.option(
    "--minimum-severity",
    "minimum_severity",
    type=click.Choice(("LOW", "MEDIUM", "HIGH", "CRITICAL")),
    help="Minimum severity of the policies.",
)


def _validate_exclude(_ctx: Any, _param: Any, value: Sequence[str]) -> Sequence[str]:
    invalid_excluded_policies = [
        policy_id for policy_id in value if not validate_policy_id(policy_id)
    ]
    if len(invalid_excluded_policies) > 0:
        raise ValueError(
            f"The policies {invalid_excluded_policies} do not match the pattern '{POLICY_ID_PATTERN.pattern}'"
        )
    return value


_ignore_policy_option = click.option(
    "--ignore-policy",
    "--ipo",
    "ignore_policies",
    multiple=True,
    help="Policies to exclude from the results.",
    callback=_validate_exclude,
)

_ignore_path_option = click.option(
    "--ignore-path",
    "--ipa",
    "ignore_paths",
    default=None,
    type=click.Path(),
    multiple=True,
    help="Do not scan the specified paths.",
)

_directory_argument = click.argument(
    "directory",
    type=click.Path(exists=True, readable=True, path_type=Path, file_okay=False),
    required=False,
)


def add_iac_scan_common_options() -> Callable[[AnyFunction], AnyFunction]:
    def decorator(cmd: AnyFunction) -> AnyFunction:
        add_common_options()(cmd)
        _exit_zero_option(cmd)
        _minimum_severity_option(cmd)
        _ignore_policy_option(cmd)
        _ignore_path_option(cmd)
        _directory_argument(cmd)
        json_option(cmd)
        return cmd

    return decorator
