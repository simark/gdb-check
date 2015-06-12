gdb-check is a simple script to compare the output of make check for two revisions

To use it, you need to be in the **gdb** directory of the `binutils-gdb`repository. Then, call it and specify the base revision and the revision you want to test.

    $ pwd
    /path/to/my/binutils-gdb/gdb
    $ gdb-check -j 4 master feature_branch --dry-run

You can take a look at the commands the script will use. It's time to make sure it won't kill your cat. Looks good? Repeat without `--dry-run`.

    $ gdb-check -j 4 master feature_branch

You can pass standard arguments in `RUNTESTFLAGS` using `-r`/`--runtestflags`:

    $ gdb-check -j 4 -r=--directory=gdb.python master feature_branch
    
