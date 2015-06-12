#!/usr/bin/env python3

import argparse
from termcolor import colored, cprint
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
	return subprocess.check_output(['git', 'rev-parse', commit], universal_newlines=True).strip()

def get_commit_summary(commit):
	return subprocess.check_output(['git', 'log', '--format=%aN  %s', '-n', '1', commit], universal_newlines=True).strip()

def make(j, dry_run):
	execute(['make', '-C..', '-j', str(j)], dry_run)

def make_check(dry_run):
	execute(['make', 'check', 'RUNTESTFLAGS=--directory=gdb.python'], dry_run, False)

def copy(source, dest, dry_run):
	execute(['cp', source, dest], dry_run)

def test_commit(commit, j, temp_dir, run_name, dry_run):
	cprint('>>> Checking out {}'.format(commit), 'grey', 'on_white')
	checkout(commit, dry_run)

	cprint('>>> Making', 'grey', 'on_white')
	make(j, dry_run)

	cprint('>>> Make checking', 'grey', 'on_white')
	make_check(dry_run)

	cprint('>>> Copying results', 'grey', 'on_white')
	copy('testsuite/gdb.sum', '{}/gdb.sum.{}'. format(temp_dir, run_name), dry_run)
	copy('testsuite/gdb.log', '{}/gdb.log.{}'. format(temp_dir, run_name), dry_run)

def compare_results(before, after):
	print()
	print('You can run one of these commands to view differences in test results.')
	print()
	print('  meld {} {}'.format(before, after))
	print('  kdiff3 {} {}'.format(before, after))
	print('  diff -u {} {}'.format(before, after))

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('baseline-commit')
	argparser.add_argument('commit-to-test')
	argparser.add_argument('-j', help='-j value to pass to make when building.', default=1, type=int)
	argparser.add_argument('-d', help='Dry run.', action='store_true')
	args = vars(argparser.parse_args())

	commit1 = args['baseline-commit']
	commit2 = args['commit-to-test']

	try:
		commit1 = resolve_to_sha1(commit1)
		commit2 = resolve_to_sha1(commit2)
	except subprocess.CalledProcessError:
		sys.exit(1)

	print('A: {}  {}  '.format(commit1[:8], get_commit_summary(commit1)))
	print('B: {}  {}  '.format(commit2[:8], get_commit_summary(commit2)))

	# Give the user time to check if it makes sense.
	if not args['d']:
		time.sleep(2)
		temp_dir = tempfile.mkdtemp(prefix='gdb-check')
	else:
		temp_dir = '<temp_dir>'

	test_commit(commit1, args['j'], temp_dir, 'before', args['d'])
	test_commit(commit2, args['j'], temp_dir, 'after', args['d'])

	compare_results('{}/gdb.sum.before'.format(temp_dir), '{}/gdb.sum.after'.format(temp_dir))

if __name__ == '__main__':
	main()
