#!/usr/bin/env python3

import argparse
from termcolor import cprint
import shlex
import subprocess
import sys
import tempfile
import time


def execute(cmd, dry_run, check=True):
    if not dry_run:
        if check:
            subprocess.check_call(cmd)
        else:
            subprocess.call(cmd)
    else:
        print(' '.join(cmd))


def checkout(commit, dry_run):
    execute(['git', 'checkout', commit], dry_run)


def resolve_to_sha1(commit):
    return subprocess.check_output(['git', 'rev-parse', commit],
                                   universal_newlines=True).strip()


def get_commit_summary(commit):
    return subprocess.check_output(
        ['git', 'log', '--format=%aN  %s', '-n', '1', commit],
        universal_newlines=True).strip()


def make(j, dry_run):
    execute(['make', '-C..', '-j', str(j)], dry_run)


def make_check(runtest_flags, dry_run):
    runtest_flags = shlex.quote(runtest_flags)
    runtest_flags = 'RUNTESTFLAGS={}'.format(runtest_flags)
    execute(['make', 'check', runtest_flags], dry_run, False)


def copy(source, dest, dry_run):
    execute(['cp', source, dest], dry_run)


def test_commit(commit, j, temp_dir, run_name, runtest_flags, dry_run):
    cprint('>>> Checking out {}'.format(commit), 'grey', 'on_white')
    checkout(commit, dry_run)

    cprint('>>> Making', 'grey', 'on_white')
    make(j, dry_run)

    cprint('>>> Make checking', 'grey', 'on_white')
    make_check(runtest_flags, dry_run)

    cprint('>>> Copying results', 'grey', 'on_white')
    copy('testsuite/gdb.sum',
         '{}/gdb.sum.{}'. format(temp_dir, run_name), dry_run)
    copy('testsuite/gdb.log',
         '{}/gdb.log.{}'. format(temp_dir, run_name), dry_run)


def compare_results(before, after):
    print()
    print('You can run one of these commands to view differences in test '
          'results.')
    print()
    print('  meld {} {}'.format(before, after))
    print('  kdiff3 {} {}'.format(before, after))
    print('  diff -u {} {}'.format(before, after))


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('baseline-commit')
    argparser.add_argument('commit-to-test')
    argparser.add_argument('-j',
                           help='-j value to pass to make when building.',
                           default=1,
                           type=int)
    argparser.add_argument('-d', '--dry-run',
                           help='Dry run.',
                           action='store_true')
    argparser.add_argument('-r', '--runtest-flags',
                           help='Value of RUNTESTFLAGS to pass to make check.',
                           default='')
    args = vars(argparser.parse_args())

    commit1 = args['baseline-commit']
    commit2 = args['commit-to-test']
    dryrun = args['dry_run']
    runtest_flags = args['runtest_flags']
    j = args['j']

    try:
        commit1 = resolve_to_sha1(commit1)
        commit2 = resolve_to_sha1(commit2)
    except subprocess.CalledProcessError:
        sys.exit(1)

    print('A: {}  {}  '.format(commit1[:8], get_commit_summary(commit1)))
    print('B: {}  {}  '.format(commit2[:8], get_commit_summary(commit2)))

    if not dryrun:
        # Give the user time to check if it makes sense.
        time.sleep(2)
        temp_dir = tempfile.mkdtemp(prefix='gdb-check')
    else:
        temp_dir = '<temp_dir>'

    test_commit(commit1, j, temp_dir, 'before', runtest_flags, dryrun)
    test_commit(commit2, j, temp_dir, 'after', runtest_flags, dryrun)

    compare_results('{}/gdb.sum.before'.format(temp_dir),
                    '{}/gdb.sum.after'.format(temp_dir))

if __name__ == '__main__':
    main()
