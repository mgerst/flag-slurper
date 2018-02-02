Flag Slurper
============
Utility for grabbing CDC flags from machines.

Auto PWN
========
Flag slurper contains a utility for automatically attempting default credentials against team's SSH hosts. This works by
grabbing the team list from IScorE and a list of all the services. The default credentials it uses are:

- `root:cdc`
- `cdc:cdc`

Usage
-----
To generate the team and service list you can simply run:

```bash
flag-slurper autopwn generate
```

This will result in both `teams.yml` and `services.yml` being generated. These files will be used by other `autopwn`
commands so they don't need to keep hitting the IScorE API during the attack phase when the API is getting hammered.

After generating the local files, you can then pwn all the things!

```bash
flag-slurper autopwn pwn
```

This will print out what credentials worked on which machines and any flags found. These results are recorded in
`results.yml` and can be viewed like this:

```bash
flag-slurper autopwn results
```
