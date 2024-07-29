# Portal 2 Verifier

This is a tool that automates as much of the verification process as possible

### Setup

1. Run verifier.py
    - This will make all necessary files for using it
2. Install mdp under mdp/, so you have mdp/mdp.exe
3. Open config.json and look at the options you want to customize

### Usage

1. Put all demos that are part of the run under run/
    - They don't have to be exactly in run/, any subfolder will suffice
2. Alternatively to 1. put a single .zip file into run
    - Make sure there are no other files or folders in run/
    - Make sure that unzipper is set to true in config.json
3. Run verifier.py
    - Make sure both Steam and Portal 2 are installed
    - SAR isn't required
4. Look at output.json and run commands if you want

### Features and options

- config.json options
    - verbose: puts more logging in the terminal
    - commandline: allows you to send commands to Portal 2
    - unzipper: incase of a single zip files in run/ unzips it
    - addindex: adds map and demo indexes to output.json
- Setting aliases
    - Add it into config.json before running verifier.py
    - If you are confused look at how the sla alias is set up
    - Note: you can only alias a command that isn't an alias
    - Note: incase you alias an existing command name the original will have priority
- Commands
    - help: displays the help command
    - exit: stops both the tool and portal 2
    - playdemo [demos]: plays all demos
        - they can be a filename, a demoname or an index
    - playmap [maps]: plays all demos of all maps
        - they can be a mapname or an index
    - sla: a default alias that plays all maps that i think needs to be verified for accidental sla
- output.json
    - rta: rta time begin, end and elapsed time
    - servernumber: first and last servernumber, amount of demos and servernumber difference is in total
    - sarchecksums: list of all failed SAR checksums
    - cvars: a list of all cvars that were flagged by mdp throughout the run
    - files: all file checksum failes (except SAR)
    - demos: a list of all the commands in all the demos, sorted by mapname
        - demos on the same map are sorted in chronological order
        - `sar_always_transmit_heavy_ents x`, `sv_player_funnel_into_portals 1` and `ui_transition_effect x` are filtered

Incase you have any questions dm me on discord (@archerthereal)