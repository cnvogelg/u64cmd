# u64cmd - Remote Control for your Ultimate 64/II+

This Python command line tools allows you to control your [Ultimate 64][1]/Ultimate II+
device via a TCP connection on port 64.

It implements almost the full feature set of the DMA Socket Protocol as
specified in the Ultimate64 [source code][2].

[1]: https://ultimate64.com
[2]: https://github.com/GideonZ/1541ultimate/blob/master/software/network/socket_dma.cc

## Feature Set

* Upload/Run PRG Files
* Upload REU Images
* Upload/Mount Disk Images
* Upload/Activate CRT Images
* Upload/Activate Kernel ROM Images
* Write Data Files to RAM
* POKE, POKEW
* Type Text with Petcat like Control Codes
* Reset/PowerOff Machine
* On Ultimate64: Enable/Disable VIC/Audio/Debug Stream

## Installation

* You need Python 3 >= Version 3.7 and Pip installed
* Install stable version

        pip3 install u64cmd

* Install current Git version

        pip3 install -U git+https://github.com/cnvogelg/u64cmd.git

## Run u64cmd

You run the command with this syntax:

    u64cmd -h 192.168.2.1 reset

The `-h|--host` option is required to give the IP address or hostname of your
Ultimate 64/II+.

The above command triggers only the `reset` command and exits. You can also
specify multiple commands on the command line to execute them in a row:

    u64cmd -h 192.168.2.1 reset load_reu blureu.img load_prg -r blureu.prg

## Command Description

### Main Options

Usage:

    u64cmd [--host|-h <host_addr] [--port|-p <port_num>] <command> ...

* `--host|-h` gives the `host_addr` of the Ultime64/II+ (required). Use
  environment variable `U64CMD_HOST` to set the value permanently.
* With `--port|-p` you can specify the port number. The default is `64`. Use
  environment variable `U64CMD_PORT` to set the value permanently.

### More Main Options

* The option `--version` shows the release version of the tool.
* The option `--help` gives you a command overview.
* Use `... <command> --help` to get detailed help on a command
* The option `--dump-keycodes|-D` shows a list of known petcat control
  commands for typing message (see `type` command)

### `type` - Type Text on C64 Keyboard

Usage:

    type <text>

* Types the given `text`.
* You can pass control codes in the `{code}` notation (similar to `petcat`)
* Use the `--dump-keycodes|-D` command to get a list of all supported codes.

Example:

    type "{clr}{wht}HELLO, WORLD!{lblu}{cr}"

### `prg_load` - Load (and Run) a PRG File  

Usage:

    prg_load [--run] [--jump] <prg_file>

* `prg_file` gives the name of the PRG file you want to DMA load
* add the `--run|-r` switch to automatically `RUN` the PRG after loading
* similar `--jump|-j` jumps to the load address of the PRG file

### `reu_load` - Load Data File into REU

Usage:

    reu_load [--addr <addr>] [--offset <num>] [--size <num>] <reu_file>

* `reu_file` gives the file name to be uploaded into the REU
* `--addr|-a <addr>` defines the loading address. 
* `--offset|-o <num>` sets an optional offset in the file. By default the
  whole file starting at the first byte will be uploaded. With this command
  you can skip bytes for the upload.
* `--size|-s <num>` limits the transfer. This allows you to reduce the
  uploaded block. By default the whole file is transferred.

Note: You can specify any value in the tool either in decimal (e.g. `49152`)
  or in hex (e.g. `0xc000`)

### `disk_load` - Load/Mount Disk Images

Usage:

    disk_load [--run|-r] <disk_file>

* `disk_file` is a D64 disk image to be uploaded and mounted
* The optional `--run|-r` allows to automatically run the first file in the
  image.

### `crt_load` - Load/Enable CRT Images

Usage:

    crt_load <crt_file>

* Uploads the `crt_file` as current cartridge image and activates it.

### `kernal_load` - Load/Enable Kernal Image

Usage:

    kernel_load <kernal_file>

* Upload the `kernal_file` as the new kernal ROM.

### `data_write` - Write data into RAM

Usage:

    data_write [--addr <addr>] [--offset <num>] [--size <num>] <data_file>

* `data_file` gives the file name to be uploaded into C64 RAM
* `--addr|-a <addr>` defines the loading address. You can specify the value
  in decimal (e.g. `49152`) or in hex (e.g. `0xc000`)
* `--offset|-o <num>` sets an optional offset in the file. By default the
  whole file starting at the first byte will be uploaded. With this command
  you can skip bytes for the upload.
* `--size|-s <num>` limits the transfer. This allows you to reduce the
  uploaded block. By default the whole file is transferred.

### `poke` and `pokew` - Write values into C64 Memory

Usage:

    poke <addr> <value>
    pokew <addr> <value>

* poke a byte or a word `value` into memory at address `addr`

### `stream_on` - Enable VIC/Audio/Debug Streaming (U64 only)

Usage:

    stream_on [--duration <num>] [--addr|-a <host_addr>] <stream_name>

* Valid stream names are `vic`, `audio`, or `debug`.
* The optional `--duration|-d <num>` allows to set the transfer duration. By
  default the value is set to 0 meaning infinite duration.
* The optional `--addr|-a <host_addr` gives the host address where the stream
  will be sent to. Typically a multicast address or your own host address.

### `stream_off` - Disable VIC/Audio/Debug Streaming (U64 only)

Usage:

    stream_off <stream_name>

* Valid stream names are `vic`, `audio`, or `debug`.

### `reset` - Reset C64

Usage:

    reset

### `poweroff` - Power Off C64 (U64 only)

Usage:

    poweroff

EOF