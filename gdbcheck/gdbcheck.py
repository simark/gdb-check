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
    line = ' '.join(cmd)

    print(line)

    if not dry_run:
        if check:
            subprocess.check_call(line, shell=True)
        else:
            subprocess.call(line, shell=True)

def checkout(repo_path, commit, dry_run):
    execute(['git', '-C', repo_path, 'checkout', commit], dry_run)


def resolve_to_sha1(repo_path, commit):
    return subprocess.check_output(
        ['git', '-C', repo_path, 'rev-parse', commit],
        universal_newlines=True).strip()


def get_commit_summary(repo_path, commit):
    return subprocess.check_output(
        ['git', '-C', repo_path, 'log', '--format=%aN  %s', '-n', '1', commit],
        universal_newlines=True).strip()


def make(build_path, j, dry_run):
    execute(['make', '-C', build_path, 'MAKEINFO=true', '-j', str(j)],
            dry_run)


def make_check(build_path, runtest_flags, dry_run):
    p = os.path.join(build_path, 'gdb')

    if len(runtest_flags) > 0:
        runtest_flags = shlex.quote(runtest_flags)
    runtest_flags = 'RUNTESTFLAGS={}'.format(runtest_flags)

    execute(['make', '-C', p, 'check', runtest_flags], dry_run, False)


def copy(source, dest, dry_run):
    execute(['cp', source, dest], dry_run)


def test_commit(repo_path, build_path, commit, j, temp_dir, run_name,
                runtest_flags, dry_run):
    cprint('>>> Checking out {}'.format(commit), 'grey', 'on_white')
    checkout(repo_path, commit, dry_run)

    cprint('>>> Making', 'grey', 'on_white')
    make(build_path, j, dry_run)

    cprint('>>> Make checking', 'grey', 'on_white')
    make_check(build_path, runtest_flags, dry_run)

    cprint('>>> Copying results', 'grey', 'on_white')
    sum_file = os.path.join(build_path, 'gdb', 'testsuite', 'gdb.sum')
    copy(sum_file, '{}/gdb.sum.{}'. format(temp_dir, run_name), dry_run)
    log_file = os.path.join(build_path, 'gdb', 'testsuite', 'gdb.log')
    copy(log_file, '{}/gdb.log.{}'. format(temp_dir, run_name), dry_run)


def compare_results(before, after):
    print()
    print('You can run one of these commands to view differences in test '
          'results.')
    print()
    print('  meld {} {}'.format(before, after))
    print('  kdiff3 {} {}'.format(before, after))
    print('  diff -u {} {}'.format(before, after))


def main():
    epilog = '\n'.join((
        'The script won\'t like if you try to pass something like:',
        '',
        '    --runtestflags --directory=gdb.python',
        '',
        'Instead, use an equal sign:',
        '',
        '    --runtestflags=--directory=gdb.python',
    ))

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog)
    argparser.add_argument('before-ref')
    argparser.add_argument('after-ref')
    argparser.add_argument('-j',
                           help='-j value to pass to make when building '
                           '(def: 1)',
                           default=1,
                           type=int,
                           metavar='jobs')
    argparser.add_argument('-d', '--dry-run',
                           help='execute a dry run',
                           action='store_true')
    argparser.add_argument('-r', '--runtestflags',
                           help='value of RUNTESTFLAGS to pass to make check '
                           '(def: empty)',
                           default='')
    argparser.add_argument('--runtestflags-before',
                           help='value of RUNTESTFLAGS to pass to make check '
                           'when testing the \'before\' commit (def: empty)',
                           default='')
    argparser.add_argument('--runtestflags-after',
                           help='value of RUNTESTFLAGS to pass to make check '
                           'when testing the \'after\' commit (def: empty)',
                           default='')
    argparser.add_argument('-s', '--source',
                           help='path to binutils-gdb source repository '
                           '(def: CWD)',
                           default=os.getcwd())
    argparser.add_argument('-b', '--build',
                           help='path to binutils-gdb build directory '
                           '(def: CWD)',
                           default=os.getcwd())
    args = vars(argparser.parse_args())

    before_ref = args['before-ref']
    after_ref = args['after-ref']
    dryrun = args['dry_run']
    runtest_flags_before = ' '.join([args['runtestflags_before'], args['runtestflags']])
    runtest_flags_after = ' '.join([args['runtestflags_after'], args['runtestflags']])
    j = args['j']
    repo_path = args['source']
    build_path = args['build']

    try:
        before_sha1 = resolve_to_sha1(repo_path, before_ref)
        after_sha1 = resolve_to_sha1(repo_path, after_ref)
    except subprocess.CalledProcessError:
        sys.exit(1)

    print('Before: {}  {}  '.format(
        before_sha1[:8], get_commit_summary(repo_path, before_sha1)))
    print('After:  {}  {}  '.format(
        after_sha1[:8], get_commit_summary(repo_path, after_sha1)))

    if not dryrun:
        # Give the user time to check if it makes sense.
        time.sleep(2)
        temp_dir = tempfile.mkdtemp(prefix='gdb-check')
    else:
        temp_dir = '<temp_dir>'

    test_commit(repo_path, build_path, before_sha1, j, temp_dir, 'before',
                runtest_flags_before, dryrun)
    test_commit(repo_path, build_path, after_sha1, j, temp_dir, 'after',
                runtest_flags_after, dryrun)

    compare_results('{}/gdb.sum.before'.format(temp_dir),
                    '{}/gdb.sum.after'.format(temp_dir))

if __name__ == '__main__':
    main()
