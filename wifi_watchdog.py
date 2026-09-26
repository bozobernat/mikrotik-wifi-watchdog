#!/usr/bin/env python3
# Copyright 2026 Bozó Bernát
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Required Notice: Copyright Bozó Bernát — https://github.com/bozobernat/mikrotik-wifi-watchdog
"""wifi_watchdog.py — riaszt, ha nem whitelistelt eszköz csatlakozik a WiFi-re.

Minden futáskor lekéri a MikroTik router aktuális WiFi-regisztrációs tábláját
(`/interface/wifi/registration-table`) — tehát a ténylegesen, most rádiósan
kapcsolódott klienseket, nem a DHCP-lease-listát (ami statikus IP-s vagy
vezetékes eszközöket is tartalmazhat, és lemaradhat a friss csatlakozásokról).

Csak azokra a MAC-ekre riaszt, amik ÚJONNAN jelentek meg (nem szerepeltek az
előző futás nyomon követett idegen-listáján) — így egy folyamatosan kapcsolódva
maradó ismeretlen eszköz nem küld push-t minden egyes futáskor, csak első
alkalommal, amíg csatlakozva marad. Ha lecsatlakozik, majd újra megjelenik, az
megint "új" — ez szándékos.

A routeren CSAK OLVAS. Egyetlen írás: a saját állapotfájlja és a jelentés a
szkript könyvtárában.

Konfiguráció (környezeti változók, mind opcionális):

    WIFI_WATCHDOG_ROUTER_CMD    a routert olvasó wrapper (l. README)
                                alap: ~/bin/mikrotik-ssh.sh
    WIFI_WATCHDOG_NOTIFY_CMD    a Home Assistant API-t hívó wrapper
                                alap: ~/bin/ha-api.sh
    WIFI_WATCHDOG_NOTIFY_SERVICE  a HA notify-szolgáltatás útvonala
                                alap: /api/services/notify/notify

Használat:
    python3 wifi_watchdog.py
    python3 wifi_watchdog.py --no-push --no-write
    python3 wifi_watchdog.py --json
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

PROJEKT_DIR = os.path.dirname(os.path.abspath(__file__))
WHITELIST_FAJL = os.path.join(PROJEKT_DIR, "whitelist.json")
KNOWN_DEVICES_FAJL = os.path.join(PROJEKT_DIR, "known_devices.json")
STATE_FAJL = os.path.join(PROJEKT_DIR, "wifi-watchdog-jelenlet-allapot.json")
JELENTES = os.path.join(PROJEKT_DIR, "wifi-watchdog-legutobbi-futas.md")
SZAMLALO_FAJL = os.path.join(PROJEKT_DIR, "wifi_watchdog_ertesites_szamlalo.txt")

MT = os.environ.get(
    "WIFI_WATCHDOG_ROUTER_CMD", os.path.expanduser("~/bin/mikrotik-ssh.sh"))
HQ = os.environ.get(
    "WIFI_WATCHDOG_NOTIFY_CMD", os.path.expanduser("~/bin/ha-api.sh"))
NOTIFY_SERVICE = os.environ.get(
    "WIFI_WATCHDOG_NOTIFY_SERVICE", "/api/services/notify/notify")

# RouterOS 7.x /interface/wifi (nem a régi /interface/wireless) — wifi1=5G, wifi2=2.4G.
REG_TABLE_PARANCS = (
    ':foreach r in=[/interface/wifi/registration-table/find] do={:put '
    '([/interface/wifi/registration-table/get $r mac-address] . "|" . '
    '[/interface/wifi/registration-table/get $r interface])}'
)


def _fut(parancs: list, timeout: int) -> tuple:
    """(stdout, hiba) — a stdout üres/hibás, ha hiba nem None."""
    try:
        p = subprocess.run(parancs, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"időtúllépés ({timeout}s)"
    except FileNotFoundError:
        return None, f"a parancs nem található: {parancs[0]}"
    if p.returncode != 0:
        hiba = (p.stderr or p.stdout or "").strip().splitlines()
        return None, (hiba[-1][:300] if hiba else f"exit kód {p.returncode}")
    return p.stdout, None


def whitelist_betolt() -> set:
    with open(WHITELIST_FAJL, encoding="utf-8") as f:
        d = json.load(f)
    return {dev["mac"].upper() for dev in d["devices"]}


def label_terkep_betolt() -> dict:
    """MAC -> label a known_devices.json-ból, jobb push-üzenethez."""
    if not os.path.exists(KNOWN_DEVICES_FAJL):
        return {}
    with open(KNOWN_DEVICES_FAJL, encoding="utf-8") as f:
        d = json.load(f)
    return {dev["mac"].upper(): dev.get("label") or dev.get("comment") or ""
            for dev in d}


def registracios_tabla_lekerdez():
    """(aktiv_kliensek, hiba) — [{mac, interface}], a router friss WiFi-regisztrációja."""
    out, hiba = _fut([MT, REG_TABLE_PARANCS], timeout=30)
    if hiba:
        return None, hiba
    kliensek = []
    for sor in (out or "").strip().splitlines():
        sor = sor.strip()
        if not sor or "|" not in sor:
            continue
        mac, _, iface = sor.partition("|")
        mac = mac.strip().upper()
        if len(mac) == 17:  # AA:BB:CC:DD:EE:FF alak — durva józansági ellenőrzés
            kliensek.append({"mac": mac, "interface": iface.strip()})
    return kliensek, None


def state_betolt() -> dict:
    if not os.path.exists(STATE_FAJL):
        return {}
    try:
        with open(STATE_FAJL, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def state_ment(state: dict):
    with open(STATE_FAJL, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def kovetkezo_ertesites_szam() -> int:
    """Folyamatos sorszám az elküldött push-értesítéseknek."""
    szam = 0
    try:
        with open(SZAMLALO_FAJL, "r", encoding="utf-8") as f:
            szam = int(f.read().strip() or "0")
    except (FileNotFoundError, ValueError):
        szam = 0
    szam += 1
    with open(SZAMLALO_FAJL, "w", encoding="utf-8") as f:
        f.write(str(szam))
    return szam


def push_kuld(cim: str, uzenet: str) -> tuple:
    body = json.dumps({"title": cim, "message": uzenet}, ensure_ascii=False)
    return _fut([HQ, "POST", NOTIFY_SERVICE, body], timeout=30)


def vizsgal() -> dict:
    most = datetime.datetime.now().isoformat(timespec="seconds")
    kliensek, hiba = registracios_tabla_lekerdez()

    eredmeny = {
        "futtatva": most,
        "hiba": hiba,
        "aktiv_osszes": 0,
        "idegenek": [],
        "uj_idegenek": [],
        "eltavozott_idegenek": [],
    }
    if hiba:
        return eredmeny

    whitelist = whitelist_betolt()
    labelek = label_terkep_betolt()
    elozo_state = state_betolt()

    eredmeny["aktiv_osszes"] = len(kliensek)

    idegenek = {}
    for k in kliensek:
        if k["mac"] in whitelist:
            continue
        rekord = idegenek.setdefault(k["mac"], {
            "mac": k["mac"], "label": labelek.get(k["mac"], ""),
            "interfaces": [],
        })
        if k["interface"] not in rekord["interfaces"]:
            rekord["interfaces"].append(k["interface"])

    uj_state = {}
    for mac, rekord in idegenek.items():
        elozo = elozo_state.get(mac)
        first_lattam = elozo["first_lattam"] if elozo else most
        uj_state[mac] = {"first_lattam": first_lattam, "last_lattam": most}
        rekord["first_lattam"] = first_lattam
        rekord["uj"] = elozo is None

    eredmeny["idegenek"] = sorted(idegenek.values(), key=lambda r: r["mac"])
    eredmeny["uj_idegenek"] = [r for r in eredmeny["idegenek"] if r["uj"]]
    eredmeny["eltavozott_idegenek"] = sorted(set(elozo_state) - set(uj_state))
    eredmeny["_uj_state"] = uj_state
    return eredmeny


def push_uzenet(uj_idegenek: list) -> str:
    reszek = []
    for r in uj_idegenek:
        cimke = f" ({r['label']})" if r["label"] else ""
        ifacek = "/".join(r["interfaces"])
        reszek.append(f"{r['mac']}{cimke} [{ifacek}]")
    return ("Új, nem whitelistelt eszköz csatlakozott a WiFi-hez: "
            + "; ".join(reszek))


def markdown(e: dict) -> str:
    s = ["---", "topic: wifi-watchdog",
         f"updated: {e['futtatva']}", "---", "",
         "# wifi-watchdog — legutóbbi futás", "",
         f"Futtatva: **{e['futtatva']}**.", ""]

    if e["hiba"]:
        s += ["## Lekérdezés hibás", "", f"`{e['hiba']}`", "",
              "A router WiFi-regisztrációs táblája nem volt olvasható — "
              "ez lehet átmeneti SSH-/hálózati hiba, nem feltétlenül "
              "behatolás. Nincs push (elkerülve a téves riasztást).", ""]
        return "\n".join(s)

    s += [f"Aktív WiFi-kliens összesen: **{e['aktiv_osszes']}**.", ""]

    if e["idegenek"]:
        s += [f"## Nem whitelistelt eszköz a WiFi-n ({len(e['idegenek'])})", "",
              "| MAC | címke (ha ismert) | interfész | első észlelés (ebben a "
              "kapcsolódásban) | új ebben a futásban |",
              "|---|---|---|---|:--:|"]
        s += [f"| `{r['mac']}` | {r['label'] or '—'} | {'/'.join(r['interfaces'])} "
              f"| {r['first_lattam']} | {'IGEN' if r['uj'] else 'nem'} |"
              for r in e["idegenek"]]
        s += [""]
        if e.get("ertesites_szam"):
            s += [f"**Elküldött push-értesítés: #{e['ertesites_szam']} "
                  f"({e['ertesites_datum']}).**", ""]
    else:
        s += ["## Nem whitelistelt eszköz a WiFi-n", "",
              "Nincs — minden aktív WiFi-kliens a whitelisten van.", ""]

    if e["eltavozott_idegenek"]:
        s += [f"## Lecsatlakozott, korábban nyomon követett idegen "
              f"({len(e['eltavozott_idegenek'])})", "",
              "Ezek most nincsenek a hálón; ha újra megjelennek, megint "
              "'új'-ként fognak jelentkezni.", ""]
        s += [f"- `{mac}`" for mac in e["eltavozott_idegenek"]]
        s += [""]

    s += ["---", "",
          "Ezt a jelentést a `wifi_watchdog.py` írta. Csak olvas (WiFi-"
          "regisztrációs tábla) — a routeren és a whitelisten semmit nem "
          "módosít. Push csak ÚJ (korábban nem látott) idegen eszközre — "
          "folyamatosan kapcsolódva maradó ismeretlen eszköz nem küld "
          "értesítést minden futáskor.", ""]
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser(description="WiFi watchdog (MikroTik regisztrációs tábla)")
    ap.add_argument("--json", action="store_true", help="gépi kimenet")
    ap.add_argument("--no-write", action="store_true", help="ne írja a jelentés- és state-fájlt")
    ap.add_argument("--no-push", action="store_true", help="ne küldjön HA-push-t")
    args = ap.parse_args()

    e = vizsgal()

    if not e["hiba"] and e["uj_idegenek"] and not args.no_push:
        szam = kovetkezo_ertesites_szam()
        datum = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cim = f"WiFi watchdog — ismeretlen eszköz #{szam}"
        uzenet = f"#{szam} · {datum} — " + push_uzenet(e["uj_idegenek"])
        _out, push_hiba = push_kuld(cim, uzenet)
        e["push_elkuldve"] = push_hiba is None
        e["push_hiba"] = push_hiba
        e["ertesites_szam"] = szam
        e["ertesites_datum"] = datum
    else:
        e["push_elkuldve"] = False
        e["push_hiba"] = None
        e["ertesites_szam"] = None
        e["ertesites_datum"] = None

    if not args.no_write and not e["hiba"]:
        state_ment(e.pop("_uj_state"))
    else:
        e.pop("_uj_state", None)

    if not args.no_write:
        with open(JELENTES, "w", encoding="utf-8") as f:
            f.write(markdown(e))

    if args.json:
        print(json.dumps(e, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"wifi-watchdog — {e['futtatva']}")
        print()
        if e["hiba"]:
            print(f"LEKÉRDEZÉS HIBÁS: {e['hiba']}")
        else:
            print(f"Aktív WiFi-kliens: {e['aktiv_osszes']}")
            print(f"Nem whitelistelt: {len(e['idegenek'])} "
                  f"(ebből új: {len(e['uj_idegenek'])})")
            if e["uj_idegenek"]:
                for r in e["uj_idegenek"]:
                    cimke = f" ({r['label']})" if r["label"] else ""
                    print(f"  ÚJ: {r['mac']}{cimke} [{'/'.join(r['interfaces'])}]")
            if e["push_elkuldve"]:
                print(f"Push elküldve: {NOTIFY_SERVICE}")
            elif e["push_hiba"]:
                print(f"Push HIBÁS: {e['push_hiba']}")
        if not args.no_write:
            print(f"Jelentés: {os.path.basename(JELENTES)}")

    if e["hiba"]:
        sys.exit(2)
    sys.exit(1 if e["uj_idegenek"] else 0)


if __name__ == "__main__":
    main()
