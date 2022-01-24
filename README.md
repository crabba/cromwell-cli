# cromwell-cli.py

A command line script to submit one or more jobs to a Cromwell server. 

## Usage

The script has several commands, global options, and arguments specific to each command.  The command line syntax is:

```
Usage: cromwell-cli.py [OPTIONS] COMMAND [ARGS]...
```

Note that global options come before the command name, and command-specifc arguments come after the command name.

## Help

Help on the overall script, including global options and the command names:

```bash
$ ./cromwell-cli.py --help
Usage: cromwell-cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose       Verbosity (cumulative)
  -p, --profile TEXT  AWS CLI Profile
  --help              Show this message and exit.

Commands:
  query       Query host for all workflows
  run         Run given source WDL file with inputs JSON file
  run-bucket  Call run() on each BAM file in the given bucket
```

## Commands

### run: Run a Cromwell job

```bash
$ ./cromwell-cli.py run --help
Usage: cromwell-cli.py run [OPTIONS]

  Run given source WDL file with inputs JSON file

Options:
  --host TEXT    DNS name or IP of Cromwell host  [required]
  --source TEXT  WDL input file  [required]
  --inputs TEXT  JSON inputs file
  --help         Show this message and exit.


$ ./cromwell-cli.py run --host host.foo.com --source workflows/simple-hello.wdl
Success
{
  "id": "b6af82cf-0c1d-46ff-a49c-41f0054fca15",
  "status": "Submitted"
}
```

### run-bucket: Run a Cromwell job on each object matching a pattern in an S3 bucket

```bash
$ ./cromwell-cli.py run-bucket --help
Usage: cromwell-cli.py run-bucket [OPTIONS]

  Call run() on each BAM file in the given bucket

Options:
  --host TEXT      DNS name or IP of Cromwell host  [required]
  --source TEXT    WDL input file  [required]
  --bucket TEXT    Bucket of BAM files to process  [required]
  --prefix TEXT    Prefix of objects within bucket  [required]
  --template TEXT  Mustache-format template for inputs file  [required]
  --help           Show this message and exit.


$ ./cromwell-cli.py -v run-bucket --host host.foo.com --source workflows/parliament2.wdl --template myinputs.mustache --bucket gatk-test-data --prefix wgs_bam/NA12878_20k_b37/NA12878_20k.b37.
Success
{
  "id": "665c3639-a7a9-42da-889f-93ac3a319f00",
  "status": "Submitted"
}
```
## Quick Start

* Run the `simple-hello` example from the **run** command documented above.  Note the process ID, and monitor the status of the job in the Batch console.

* Run a minimal Parliament2 example with the input file `parliament2.NA12878_14MB.json`. This uses the input file `gatk-test-data/wgs_bam/NA12878_20k_b37/NA12878.bam`, chosen for its small size (15 MB BAM).

```
./cromwell-cli.py --profile myprofile run --host my.host.com --source workflows/parliament2.wdl --inputs workflows/parliament2.NA12878_14MB.json
```

## To Do

* Extend to other workflows.
* Add ability for index (.bai) files to be optional.
* Add tests for result files, so that a partially-processed bucket may be resubmitted without repeating files.