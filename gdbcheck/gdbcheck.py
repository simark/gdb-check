#!/usr/bin/env python3

import argparse
import os.path
import shlex
import subprocess
import sys
import tempfile
from termcolor import cprint
import time


def execute(cmd, dry_run, check=True):
    line = " ".join(cmd)

    print(line)

    if not dry_run:
        if check:
            subprocess.check_call(line, shell=True)
        else:
            subprocess.call(line, shell=True)


def checkout(repo_path, commit, dry_run):
    execute(["git", "-C", repo_path, "checkout", commit], dry_run)


def resolve_to_sha1(repo_path, commit):
    return subprocess.check_output(
        ["git", "-C", repo_path, "rev-parse", commit], universal_newlines=True
    ).strip()


def get_commit_summary(repo_path, commit):
    return subprocess.check_output(
        ["git", "-C", repo_path, "log", "--format=%aN  %s", "-n", "1", commit],
        universal_newlines=True,
    ).strip()


def make(build_path, j, dry_run):
    execute(["make", "-C", build_path, "MAKEINFO=true", "-j", str(j)], dry_run)


def make_check(build_path, runtest_flags, tests, dry_run):
    p = os.path.join(build_path, "gdb")

    if len(runtest_flags) > 0:
        runtest_flags = shlex.quote(runtest_flags)
    runtest_flags = "RUNTESTFLAGS={}".format(runtest_flags)

    cmd = ["make", "-C", p, "check", runtest_flags]

    if len(tests) > 0:
        cmd.append('TESTS="{}"'.format(tests))

    execute(cmd, dry_run, False)


def copy(source, dest, dry_run):
    execute(["cp", source, dest], dry_run)


def test_spec(spec, dry_run):
    cprint(">>> Checking out {}".format(spec.short_sha1), "grey", "on_white")
    checkout(spec.src_path, spec.sha1, dry_run)

    cprint(">>> Making", "grey", "on_white")
    make(spec.build_path, spec.j, dry_run)

    cprint(">>> Make checking", "grey", "on_white")
    make_check(spec.build_path, spec.runtest_flags, spec.tests, dry_run)

    cprint(">>> Copying results", "grey", "on_white")
    sum_file = os.path.join(spec.build_path, "gdb", "testsuite", "gdb.sum")
    copy(sum_file, "{}/gdb.sum.{}".format(spec.results_path, spec.short_sha1), dry_run)
    log_file = os.path.join(spec.build_path, "gdb", "testsuite", "gdb.log")
    copy(log_file, "{}/gdb.log.{}".format(spec.results_path, spec.short_sha1), dry_run)


def compare_results(before, after):
    print()
    print("You can run one of these commands to view differences in test " "results.")
    print()
    print("  meld {} {}".format(before, after))
    print("  kdiff3 {} {}".format(before, after))
    print("  diff -u {} {}".format(before, after))


class BuildAndTestSpec:
    def __init__(
        self, src_path, build_path, results_path, sha1, j, runtest_flags, tests
    ):
        self._src_path = src_path
        self._build_path = build_path
        self._results_path = results_path
        self._sha1 = sha1
        self._j = j
        self._runtest_flags = runtest_flags
        self._tests = tests

    @property
    def src_path(self):
        return self._src_path

    @property
    def build_path(self):
        return self._build_path

    @property
    def results_path(self):
        return self._results_path

    @property
    def sha1(self):
        return self._sha1

    @property
    def short_sha1(self):
        return self.sha1[:12]

    @property
    def j(self):
        return self._j

    @property
    def runtest_flags(self):
        return self._runtest_flags

    @property
    def tests(self):
        return self._tests


def main():
    epilog = "\n".join(
        (
            "The script won't like if you try to pass something like:",
            "",
            "    --runtestflags --directory=gdb.python",
            "",
            "Instead, use an equal sign:",
            "",
            "    --runtestflags=--directory=gdb.python",
        )
    )

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=epilog
    )
    argparser.add_argument("before-ref")
    argparser.add_argument("after-ref")
    argparser.add_argument(
        "-j",
        help="-j value to pass to make when building " "(def: 1)",
        default=1,
        type=int,
        metavar="jobs",
    )
    argparser.add_argument(
        "-d", "--dry-run", help="execute a dry run", action="store_true"
    )
    argparser.add_argument(
        "-r",
        "--runtestflags",
        help="value of RUNTESTFLAGS to pass to make check " "(def: empty)",
        default="",
    )
    argparser.add_argument(
        "--runtestflags-before",
        help="value of RUNTESTFLAGS to pass to make check "
        "when testing the 'before' commit (def: empty)",
        default="",
    )
    argparser.add_argument(
        "--runtestflags-after",
        help="value of RUNTESTFLAGS to pass to make check "
        "when testing the 'after' commit (def: empty)",
        default="",
    )
    argparser.add_argument(
        "-t",
        "--tests",
        help="value of TESTS to pass to make check " "(def: empty)",
        default="",
    )
    argparser.add_argument(
        "-s",
        "--source",
        help="path to binutils-gdb source repository " "(def: CWD)",
        default=os.getcwd(),
    )
    argparser.add_argument(
        "-b",
        "--build",
        help="path to binutils-gdb build directory " "(def: CWD)",
        default=os.getcwd(),
    )

    args = vars(argparser.parse_args())
    dryrun = args["dry_run"]

    if not dryrun:
        # Give the user time to check if it makes sense.
        results_path = tempfile.mkdtemp(prefix="gdb-check")
    else:
        results_path = "<temp_dir>"

    src_path = args["source"]
    build_path = args["build"]
    before_ref = args["before-ref"]
    after_ref = args["after-ref"]
    j = args["j"]
    runtest_flags_before = " ".join([args["runtestflags_before"], args["runtestflags"]])
    runtest_flags_after = " ".join([args["runtestflags_after"], args["runtestflags"]])
    tests = args["tests"]

    try:
        before_sha1 = resolve_to_sha1(src_path, before_ref)
        after_sha1 = resolve_to_sha1(src_path, after_ref)
    except subprocess.CalledProcessError:
        sys.exit(1)

    before_spec = BuildAndTestSpec(
        src_path, build_path, results_path, before_sha1, j, runtest_flags_before, tests
    )
    after_spec = BuildAndTestSpec(
        src_path, build_path, results_path, after_sha1, j, runtest_flags_after, tests
    )

    print(
        "Before: {}  {}  ".format(
            before_spec.short_sha1, get_commit_summary(src_path, before_spec.sha1)
        )
    )
    print(
        "After:  {}  {}  ".format(
            after_spec.short_sha1, get_commit_summary(src_path, after_spec.sha1)
        )
    )

    if not dryrun:
        # Give the user time to check if it makes sense.
        time.sleep(2)

    specs_to_test = [before_spec, after_spec]
    for spec in specs_to_test:
        test_spec(spec, dryrun)

    compare_results(
        "{}/gdb.sum.{}".format(results_path, before_spec.short_sha1),
        "{}/gdb.sum.{}".format(results_path, after_spec.short_sha1),
    )


if __name__ == "__main__":
    main()
