import os
import traceback
from typing import List

import click

from .dev_scan import scan_commit_range
from .git_shell import check_git_dir, get_list_commit_SHA


SUPPORTED_CI = "[GITLAB | TRAVIS | CIRCLE | GITHUB ACTIONS | BITBUCKET PIPELINES]"

NO_BEFORE = "0000000000000000000000000000000000000000"


def jenkins_range(verbose: bool) -> List[str]:  # pragma: no cover
    head_commit = os.getenv("GIT_COMMIT")
    previous_commit = os.getenv("GIT_PREVIOUS_COMMIT")

    if verbose:
        click.echo(
            f"\tGIT_COMMIT: {head_commit}" f"\nGIT_PREVIOUS_COMMIT: {previous_commit}"
        )

    if previous_commit:
        commit_list = get_list_commit_SHA(f"{previous_commit}...{head_commit}")
        if commit_list:
            return commit_list

    commit_list = get_list_commit_SHA(f"{head_commit}~1...")
    if commit_list:
        return commit_list

    raise click.ClickException(
        "Unable to get commit range. Please submit an issue with the following info:\n"
        "\tRepository URL: <Fill if public>\n"
        f"\tGIT_COMMIT: {head_commit}"
        f"\tGIT_PREVIOUS_COMMIT: {previous_commit}"
    )


def travis_range(verbose: bool) -> List[str]:  # pragma: no cover
    commit_range = os.getenv("TRAVIS_COMMIT_RANGE")
    commit_sha = os.getenv("TRAVIS_COMMIT", "HEAD")

    if verbose:
        click.echo(
            f"TRAVIS_COMMIT_RANGE: {commit_range}" f"\nTRAVIS_COMMIT: {commit_sha}"
        )

    if commit_range:
        commit_list = get_list_commit_SHA(commit_range)
        if commit_list:
            return commit_list

    commit_list = get_list_commit_SHA("{}~1...".format(commit_sha))
    if commit_list:
        return commit_list

    raise click.ClickException(
        "Unable to get commit range. Please submit an issue with the following info:\n"
        "\tRepository URL: <Fill if public>\n"
        f"\tTRAVIS_COMMIT_RANGE: {commit_range}"
        f"\tTRAVIS_COMMIT: {commit_sha}"
    )


def bitbucket_pipelines_range(verbose: bool) -> List[str]:  # pragma: no cover
    commit_sha = os.getenv("BITBUCKET_COMMIT", "HEAD")
    if verbose:
        click.echo(f"BITBUCKET_COMMIT: {commit_sha}")

    commit_list = get_list_commit_SHA("{}~1...".format(commit_sha))
    if commit_list:
        return commit_list

    raise click.ClickException(
        "Unable to get commit range. Please submit an issue with the following info:\n"
        "  Repository URL: <Fill if public>\n"
        f"  CI_COMMIT_SHA: {commit_sha}"
    )


def circle_ci_range(verbose: bool) -> List[str]:  # pragma: no cover
    """
    # Extract commit range (or single commit)
    COMMIT_RANGE=$(echo "${CIRCLE_COMPARE_URL}" | cut -d/ -f7)

    # Fix single commit, unfortunately we don't always get a commit range from Circle CI
    if [[ $COMMIT_RANGE != *"..."* ]]; then
    COMMIT_RANGE="${COMMIT_RANGE}...${COMMIT_RANGE}"
    fi
    """
    compare_range = os.getenv("CIRCLE_RANGE")
    commit_sha = os.getenv("CIRCLE_SHA1", "HEAD")

    if verbose:
        click.echo(f"CIRCLE_RANGE: {compare_range}\nCIRCLE_SHA1: {commit_sha}")

    if compare_range and not compare_range.startswith("..."):
        commit_list = get_list_commit_SHA(compare_range)
        if commit_list:
            return commit_list

    commit_list = get_list_commit_SHA("{}~1...".format(commit_sha))
    if commit_list:
        return commit_list

    raise click.ClickException(
        "Unable to get commit range. Please submit an issue with the following info:\n"
        "\tRepository URL: <Fill if public>\n"
        f"\tCIRCLE_RANGE: {compare_range}\n"
        f"\tCIRCLE_SHA1: {commit_sha}"
    )


def gitlab_ci_range(verbose: bool) -> List[str]:  # pragma: no cover
    before_sha = os.getenv("CI_COMMIT_BEFORE_SHA")
    commit_sha = os.getenv("CI_COMMIT_SHA", "HEAD")
    if verbose:
        click.echo(f"CI_COMMIT_BEFORE_SHA: {before_sha}\nCI_COMMIT_SHA: {commit_sha}")
    if before_sha and before_sha != NO_BEFORE:
        commit_list = get_list_commit_SHA("{}~1...".format(before_sha))
        if commit_list:
            return commit_list

    commit_list = get_list_commit_SHA("{}~1...".format(commit_sha))
    if commit_list:
        return commit_list

    raise click.ClickException(
        "Unable to get commit range. Please submit an issue with the following info:\n"
        "  Repository URL: <Fill if public>\n"
        f"  CI_COMMIT_BEFORE_SHA: {before_sha}\n"
        f"  CI_COMMIT_SHA: {commit_sha}"
    )


def github_actions_range(verbose: bool) -> List[str]:  # pragma: no cover
    push_before_sha = os.getenv("GITHUB_PUSH_BEFORE_SHA")
    push_base_sha = os.getenv("GITHUB_PUSH_BASE_SHA")
    pull_req_base_sha = os.getenv("GITHUB_PULL_BASE_SHA")
    default_branch = os.getenv("GITHUB_DEFAULT_BRANCH")
    head_sha = os.getenv("GITHUB_SHA", "HEAD")

    if verbose:
        click.echo(
            f"github_push_before_sha: {push_before_sha}\n"
            f"github_push_base_sha: {push_base_sha}\n"
            f"github_pull_base_sha: {pull_req_base_sha}\n"
            f"github_default_branch: {default_branch}\n"
            f"github_head_sha: {head_sha}"
        )

    if push_before_sha and push_before_sha != NO_BEFORE:
        commit_list = get_list_commit_SHA("{}...".format(push_before_sha))
        if commit_list:
            return commit_list

    if pull_req_base_sha and pull_req_base_sha != NO_BEFORE:
        commit_list = get_list_commit_SHA("{}..".format(pull_req_base_sha))
        if commit_list:
            return commit_list

    if push_base_sha and push_base_sha != "null":
        commit_list = get_list_commit_SHA("{}...".format(push_base_sha))
        if commit_list:
            return commit_list

    if default_branch:
        commit_list = get_list_commit_SHA("{}...".format(default_branch))
        if commit_list:
            return commit_list

    if head_sha:
        commit_list = get_list_commit_SHA("{}~1...".format(head_sha))
        if commit_list:
            return commit_list

    raise click.ClickException(
        "Unable to get commit range. Please submit an issue with the following info:\n"
        "  Repository URL: <Fill if public>\n"
        f"github_push_before_sha: {push_before_sha}\n"
        f"github_push_base_sha: {push_base_sha}\n"
        f"github_pull_base_sha: {pull_req_base_sha}"
        f"github_default_branch: {default_branch}\n"
        f"github_head_sha: {head_sha}"
    )


@click.command()
@click.pass_context
def ci_cmd(ctx: click.Context) -> int:  # pragma: no cover
    """
    scan in a CI environment.
    """
    config = ctx.obj["config"]
    try:
        check_git_dir()
        if not (os.getenv("CI") or os.getenv("JENKINS_HOME")):
            raise click.ClickException("--ci should only be used in a CI environment.")

        if os.getenv("GITLAB_CI"):
            commit_list = gitlab_ci_range(config.verbose)
        elif os.getenv("GITHUB_ACTIONS"):
            commit_list = github_actions_range(config.verbose)
        elif os.getenv("TRAVIS"):
            commit_list = travis_range(config.verbose)
        elif os.getenv("JENKINS_HOME"):
            commit_list = jenkins_range(config.verbose)
        elif os.getenv("CIRCLECI"):
            commit_list = circle_ci_range(config.verbose)
        elif os.getenv("BITBUCKET_COMMIT"):
            commit_list = bitbucket_pipelines_range(config.verbose)

        else:
            raise click.ClickException(
                "Current CI is not detected or supported. Must be one of {}".format(
                    SUPPORTED_CI
                )
            )

        if config.verbose:
            click.echo(f"Commits to scan: {len(commit_list)}")

        return scan_commit_range(
            client=ctx.obj["client"],
            commit_list=commit_list,
            verbose=config.verbose,
            filter_set=ctx.obj["filter_set"],
            matches_ignore=config.matches_ignore,
            all_policies=config.all_policies,
            show_secrets=config.show_secrets,
        )
    except click.exceptions.Abort:
        return 0
    except click.ClickException as exc:
        raise exc
    except Exception as error:
        if config.verbose:
            traceback.print_exc()
        raise click.ClickException(str(error))
