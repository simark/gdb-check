gdb-check is a simple script to compare the output of make check for two
revisions

Call it and specify the base revision and the revision you want to test.

    $ gdb-check -s /path/to/source/binutils-gdb -b /path/to/build/binutils-gdb master feature_branch --dry-run

You can take a look at the commands the script will use. It's time to make sure
it won't kill your cat.  Looks good?  Repeat without `--dry-run`.

    $ gdb-check -s /path/to/source/binutils-gdb -b /path/to/build/binutils-gdb master feature_branch

If you don't specify the source (-s) or build (-b) directories, the current
working directory will be used instead.

You can pass standard arguments in `RUNTESTFLAGS` using `-r`/`--runtestflags`:

    $ gdb-check -r=--directory=gdb.python master feature_branch

You can pass a list of tests to execute (glob-style) through the `TESTS`
variable using `-t`/`--tests`:

    $ gdb-check -t 'gdb.base/foo-*.exp gdb.base/break.exp'
