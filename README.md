# mikrotik-wifi-watchdog

Alerts when a device that is **not on your whitelist** associates with your
MikroTik WiFi — once per arrival, not once per poll.

Runs every 15 minutes under systemd. It has been in continuous production use
on a home network since **August 2026**, and has sent **88 alerts** to date.

*Magyar nyelvű leírás: [README.hu.md](README.hu.md)*

**License:** PolyForm Noncommercial 1.0.0 — free for any noncommercial use; commercial use needs a separate licence (see [License](#license)).

---

## Why it reads the registration table, not the DHCP leases

The obvious way to ask "who is on my WiFi?" is to list the DHCP leases. That is
the wrong list for this job:

- it includes wired and statically-addressed hosts, which were never on WiFi;
- it lags behind a fresh association, so a device that just joined may not
  appear yet;
- a device with a still-valid lease shows up long after it left.

`/interface/wifi/registration-table` answers the question actually being asked:
**which clients are radio-associated right now.** (Note `/interface/wifi`, the
RouterOS 7.x path — not the older `/interface/wireless`.)

## Why it alerts only on *new* MAC addresses

A watchdog that fires on every poll is a watchdog you turn off. This one keeps
a small state file of the unknown devices it is already tracking, and notifies
only on a MAC that was not in the previous run's set. An unidentified device
that stays connected for a week produces exactly one notification.

If it disconnects and comes back, that counts as new again. That is deliberate:
re-appearance is the event worth knowing about.

## What it does not do

- **It does not block anything.** It is read-only on the router and never
  touches the whitelist. Kicking a device off is a decision for a human.
- **It does not identify devices.** A MAC and an OUI vendor is all it has. On
  the network it was built for, 6 of the unknown devices are known-unknowns
  (unlabelled IoT hardware), deliberately left alone.
- **MAC randomization defeats it.** A phone with per-network random MACs looks
  like a new device on every join. This is a property of the problem, not a bug
  to fix here.
- **It is not intrusion detection.** It tells you something unrecognised
  associated. What that means is your call.

> [!WARNING]
> **Read before use**
>
> This tool monitors network traffic and/or changes network and security
> settings. Use it only on networks you own, or have explicit permission from
> the operator to inspect — monitoring third-party networks without
> authorisation is unlawful in most jurisdictions. Treat generated keys,
> configuration files and logs as sensitive: never publish them. This is a
> personal project published without warranty, support or any service
> commitment; you assume all risk arising from its use.

---

## Requirements

- A MikroTik router running RouterOS 7.x with `/interface/wifi`
- Python 3.9+ (standard library only — no dependencies)
- Two small wrapper scripts you provide, see below

## Setup

1. **Router access, read-only.** Create a RouterOS user in a `read` group and
   give it an SSH key. Copy `bin/mikrotik-ssh.sh.example` to
   `bin/mikrotik-ssh.sh` and point it at your router. Its whole contract is:
   take a RouterOS command as `$1`, print the output.

2. **Notification channel.** Copy `bin/ha-api.sh.example` to `bin/ha-api.sh`.
   It calls the Home Assistant REST API; if you notify some other way, replace
   the script — the watchdog only ever runs `<cmd> POST <path> <json-body>`.

3. **Whitelist.** Copy `whitelist.example.json` to `whitelist.json` and fill in
   your own devices. Only the `mac` field is read; the rest is for humans.
   Optionally copy `known_devices.example.json` to `known_devices.json` too — it
   only supplies friendlier labels in the alert text.

   **Get this file right.** If `whitelist.json` is missing or is not valid JSON,
   the script exits with code 1 — which the supplied unit treats as success. A
   broken whitelist therefore fails quietly and you stop being warned. After
   editing it, run the script once by hand and check that it reports a sensible
   number of clients.

4. **Schedule it.** `systemd/` contains a working `.service` + `.timer` pair.
   They assume a `wifi-watchdog` service account and `/opt/wifi-watchdog`, so
   create that account, give it the router SSH key, make it the owner of the
   script directory (it writes its state there), and adjust the paths.

Configuration is environment variables, all optional:

| Variable | Default | Meaning |
|---|---|---|
| `WIFI_WATCHDOG_ROUTER_CMD` | `~/bin/mikrotik-ssh.sh` | read-only router wrapper |
| `WIFI_WATCHDOG_NOTIFY_CMD` | `~/bin/ha-api.sh` | notification wrapper |
| `WIFI_WATCHDOG_NOTIFY_SERVICE` | `/api/services/notify/notify` | HA service path |

## Usage

```
python3 wifi_watchdog.py              # normal run: check, report, notify
python3 wifi_watchdog.py --no-push --no-write   # dry run, changes nothing
                                      # (use BOTH: --no-write alone still
                                      #  notifies and bumps the counter)
python3 wifi_watchdog.py --json       # machine-readable output
```

Exit codes are meant for a scheduler: `0` all clear, `1` new unknown device
found, `2` the router query failed. The systemd unit treats `1` as success —
finding something is not an error. A failed query never produces an alert; a
transient SSH problem should not look like an intrusion.

Output: three files next to the script — a `wifi-watchdog-legutobbi-futas.md`
report, a small JSON state file, and a counter of notifications sent (that
counter is where the "88 alerts" figure comes from). All three are gitignored.

## Example output

Below is the actual stdout of a `--no-push --no-write` run against a mock
router response in the real RouterOS registration-table format (fictional
MACs, not the live home network), so the output format is visible without
touching the real network.

```
wifi-watchdog — 2026-09-27T16:30:53

Aktív WiFi-kliens: 3
Nem whitelistelt: 1 (ebből új: 1)
  ÚJ: 02:11:22:33:44:55 [wifi2]
```

---

## How this was built, and what that means

The code was written by an AI coding agent (Claude). I specified the behaviour,
chose the design (registration table over leases, new-arrivals-only alerting,
read-only router access), tested it against my own network, found the failure
modes, and I run it.

That division matters less than it used to. What a generated script cannot
produce is the second half: a whitelist tuned to 40 real devices over weeks, a
timer that has survived host migrations, an alert policy quiet enough that the
alerts still get read, and the discipline to leave six unidentified IoT devices
alone rather than break something to satisfy a dashboard.

Internal identifiers and inline comments are in Hungarian, which is where this
was built. The behaviour is fully described above.

## License

This project is available under the **PolyForm Noncommercial License 1.0.0**
(see [LICENSE](LICENSE)). You may use, modify and share it free of charge,
without asking, **for any noncommercial purpose** — including personal and family
use, charitable organisations, educational institutions, publicly funded research
bodies, public health and public safety organisations, and government
institutions. Under the licence this holds regardless of how those organisations
are funded.

**Commercial use requires a separate licence from me.** That includes offering
the software, or a service built on it, for money — as a subscription, or bundled
with installation or a support desk. Open an issue at <https://github.com/bozobernat/mikrotik-wifi-watchdog/issues> titled
"commercial licence". I am not against it; I want to know about it.

```
Required Notice: Copyright Bozó Bernát — https://github.com/bozobernat/mikrotik-wifi-watchdog
```

*(Under the licence's "Notices" section, anyone who passes the software on must
keep this line.)* How the human and the machine contributions are separated:
[AUTHORSHIP.md](AUTHORSHIP.md).

### Contributing

Fixes are welcome. Before a pull request can be merged you need to sign
[CLA.md](CLA.md) — a short statement that I may also use your contribution,
including under commercial licences. Without it, your contribution would tie the
project's hands later.

### Trademarks

This project is not affiliated with, endorsed by, or sponsored by Mikrotikls SIA, the Home Assistant project, or any other third party whose products it interoperates with. All trademarks are the property of their respective owners.
