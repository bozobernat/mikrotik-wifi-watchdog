# mikrotik-wifi-watchdog

Riaszt, ha **nem whitelistelt eszköz** csatlakozik a MikroTik WiFi-re — érkezésenként
egyszer, nem lekérdezésenként.

15 percenként fut, systemd timerrel. Egy otthoni hálózaton **2026 augusztusa óta**
folyamatosan üzemel, és eddig **88 riasztást** küldött.

*(English version: [README.md](README.md))*

**Licenc:** PolyForm Noncommercial 1.0.0 — nem kereskedelmi célra szabadon használható; kereskedelmi felhasználáshoz külön engedély kell (l. [Licenc](#licenc)).

---

## Miért a regisztrációs táblát olvassa, és nem a DHCP-lease-eket

A kézenfekvő út a „ki van a WiFi-men?" kérdésre a lease-lista lenne. Erre a
feladatra viszont az rossz lista:

- benne vannak a vezetékes és a statikus IP-s gépek, amik sosem voltak WiFi-n;
- lemarad a friss csatlakozásokról, tehát egy épp most belépett eszköz még nem
  látszik;
- egy érvényes lease-ű eszköz jóval azután is szerepel, hogy elment.

A `/interface/wifi/registration-table` arra a kérdésre válaszol, amit tényleg
felteszünk: **melyik kliens van most rádiósan kapcsolódva.** (Figyelem:
`/interface/wifi`, a RouterOS 7.x-es út — nem a régi `/interface/wireless`.)

## Miért csak ÚJ MAC-re riaszt

Az a watchdog, ami minden futáskor riaszt, az a watchdog, amit kikapcsolsz. Ez
egy kis állapotfájlban tartja a már nyomon követett ismeretlen eszközöket, és
csak olyan MAC-re szól, ami az előző futás halmazában nem volt benne. Egy
azonosítatlan eszköz, ami egy hétig csatlakozva marad, pontosan **egy**
értesítést okoz.

Ha lecsatlakozik és visszajön, az megint újnak számít. Ez szándékos: az
újramegjelenés az az esemény, amiről tudni akarsz.

## Amit NEM csinál

- **Nem tilt ki semmit.** A routeren csak olvas, a whitelisthez nem nyúl. Egy
  eszköz lekapcsolása emberi döntés.
- **Nem azonosít eszközt.** Egy MAC és egy gyártói OUI minden, amije van. Azon
  a hálózaton, amire készült, 6 ismeretlen eszköz tudatosan „ismert
  ismeretlen": címkézetlen IoT-hardver, szándékosan érintetlenül hagyva.
- **A MAC-randomizáció kifogja.** Egy telefon, ami hálózatonként véletlen
  MAC-et használ, minden csatlakozáskor új eszköznek látszik. Ez a feladat
  természete, nem itt javítandó hiba.
- **Ez nem behatolásészlelés.** Annyit mond, hogy valami ismeretlen
  csatlakozott. Hogy az mit jelent, a te döntésed.

> [!WARNING]
> **Figyelmeztetés — olvasd el használat előtt**
>
> Ez az eszköz hálózati forgalmat figyel, illetve hálózati és biztonsági
> beállításokat módosít. Kizárólag olyan hálózaton használd, amely a tiéd,
> vagy amelynek vizsgálatára a hálózat üzemeltetőjétől kifejezett engedélyed
> van — idegen hálózat engedély nélküli megfigyelése a legtöbb joghatóságban
> jogszabályba ütközik. A generált kulcsokat, konfigurációkat és naplófájlokat
> érzékeny adatként kezeld: ne töltsd fel őket nyilvános tárhelyre. Ezt
> személyes projektként, ellenszolgáltatás nélkül teszem közzé, garancia és
> támogatási kötelezettség nélkül; a használatból eredő bármilyen kárért,
> adatvesztésért vagy jogsértésért a felelősség a felhasználóé.

---

## Mi kell hozzá

- MikroTik router RouterOS 7.x-szel, `/interface/wifi`-vel
- Python 3.9+ (csak a standard könyvtár — nincs függősége)
- Két kis wrapper szkript, amit te adsz — lásd lent

## Beállítás

1. **Router-hozzáférés, csak olvasásra.** Hozz létre egy RouterOS-fiókot `read`
   csoportban, kulcsos belépéssel. Másold a `bin/mikrotik-ssh.sh.example`-t
   `bin/mikrotik-ssh.sh`-ra, és állítsd a routeredre. A teljes szerződése ennyi:
   kap egy RouterOS-parancsot `$1`-ben, kiírja a kimenetet.

2. **Értesítési csatorna.** Másold a `bin/ha-api.sh.example`-t `bin/ha-api.sh`-ra.
   Ez a Home Assistant REST API-t hívja; ha máshogy értesítenél, cseréld le a
   szkriptet — a watchdog csak annyit tesz, hogy lefuttatja:
   `<parancs> POST <útvonal> <json-törzs>`.

3. **Whitelist.** Másold a `whitelist.example.json`-t `whitelist.json`-ra, és
   töltsd fel a saját eszközeiddel. Csak a `mac` mezőt olvassa, a többi az
   ember kedvéért van. Ha akarod, a `known_devices.example.json`-t is másold át
   `known_devices.json`-ra — az csak barátságosabb címkéket ad a riasztáshoz.

   **Ezt a fájlt jól kell megcsinálni.** Ha a `whitelist.json` hiányzik vagy nem
   érvényes JSON, a szkript 1-es kóddal áll le — amit a mellékelt unit sikernek
   könyvel el. Egy elrontott whitelist tehát némán elhasal, és onnantól nem kapsz
   riasztást. Szerkesztés után futtasd le egyszer kézzel, és nézd meg, hogy
   értelmes kliensszámot ír-e ki.

4. **Ütemezd.** A `systemd/` mappában van működő `.service` + `.timer` pár.
   Ezek egy `wifi-watchdog` szolgáltatásfiókot és az `/opt/wifi-watchdog`
   könyvtárat feltételezik: hozd létre a fiókot, add oda neki a router
   SSH-kulcsát, tedd a szkript könyvtárának tulajdonosává (oda írja az
   állapotát), és igazítsd az útvonalakat.

A konfiguráció környezeti változókban van, mind opcionális:

| Változó | Alapérték | Mire való |
|---|---|---|
| `WIFI_WATCHDOG_ROUTER_CMD` | `~/bin/mikrotik-ssh.sh` | csak olvasó router-wrapper |
| `WIFI_WATCHDOG_NOTIFY_CMD` | `~/bin/ha-api.sh` | értesítő wrapper |
| `WIFI_WATCHDOG_NOTIFY_SERVICE` | `/api/services/notify/notify` | a HA-szolgáltatás útvonala |

## Használat

```
python3 wifi_watchdog.py              # rendes futás: ellenőriz, jelent, értesít
python3 wifi_watchdog.py --no-push --no-write   # szárazon, semmit nem változtat
                                      # (MINDKETTŐ kell: a --no-write önmagában
                                      #  még értesít és lépteti a számlálót)
python3 wifi_watchdog.py --json       # gépi kimenet
```

A kilépési kódok az ütemezőnek szólnak: `0` minden rendben, `1` új ismeretlen
eszköz, `2` a router-lekérdezés hibás. A systemd unit az `1`-et sikernek veszi
— találni valamit nem hiba. **Hibás lekérdezésből soha nem lesz riasztás:** egy
átmeneti SSH-probléma ne látsszon behatolásnak.

Kimenet: három fájl a szkript mellett — egy `wifi-watchdog-legutobbi-futas.md`
jelentés, egy kis JSON állapotfájl, és az elküldött értesítések számlálója
(ebből jön a „88 riasztás" szám). Mindhárom gitignore-olva.

## Példa kimenet

Az alábbi egy `--no-push --no-write` futás tényleges stdout-ja, kitalált
(mock) router-válaszon, ami a valódi RouterOS regisztrációs-tábla formátumát
követi (kitalált MAC-ekkel, nem az élő otthoni hálózaton) — így a formátum
látszik anélkül, hogy az éles hálózatot érintené.

```
wifi-watchdog — 2026-09-27T16:30:53

Aktív WiFi-kliens: 3
Nem whitelistelt: 1 (ebből új: 1)
  ÚJ: 02:11:22:33:44:55 [wifi2]
```

---

## Hogyan készült, és ez mit jelent

A kódot AI-ügynök (Claude) írta. Én határoztam meg a viselkedést, én döntöttem
el a tervezési kérdéseket (regisztrációs tábla a lease-lista helyett, csak-új-
eszközre riasztás, csak olvasó router-hozzáférés), én próbáltam ki a saját
hálózatomon, én találtam meg a hibamódokat, és én üzemeltetem.

Ez a felosztás ma már kevésbé számít. Amit egy generált szkript **nem** tud
előállítani, az a második fele: egy 40 valódi eszközre hetek alatt hangolt
whitelist, egy timer, ami túlélt gazdagép-költözést, egy riasztási politika,
ami elég csendes ahhoz, hogy a riasztásokat még elolvassák — és az a fegyelem,
hogy hat azonosítatlan IoT-eszközt inkább békén hagyunk, mint hogy elrontsunk
valamit egy szép műszerfalért.

## Licenc

Ez a projekt a **PolyForm Noncommercial License 1.0.0** alatt érhető el (lásd:
[LICENSE](LICENSE)). Ingyenesen, engedélykérés nélkül használhatod, módosíthatod
és továbbadhatod **bármilyen nem kereskedelmi célra**, ideértve kifejezetten:

- magánszemélyként, a saját vagy a hozzátartozód otthonában;
- jótékonysági szervezetként (pl. egyházi vagy karitatív szolgálat);
- oktatási intézményként és közfinanszírozott kutatóhelyként;
- közegészségügyi vagy közbiztonsági szervezetként;
- állami vagy önkormányzati intézményként.

A licenc szerint ez akkor is így van, ha a szervezet állami vagy pályázati
finanszírozásból működik.

**Kereskedelmi felhasználáshoz külön engedély kell tőlem.** Ide tartozik, ha a
szoftvert vagy a rá épülő szolgáltatást pénzért kínálod — akár előfizetésként,
akár telepítéssel vagy ügyfélszolgálattal együtt. Ilyen esetben **nyiss egy
issue-t** a projektben (<https://github.com/bozobernat/mikrotik-wifi-watchdog/issues>), „commercial licence" címmel.
Nem zárkózom el tőle, csak tudni akarok róla.

```
Required Notice: Copyright Bozó Bernát — https://github.com/bozobernat/mikrotik-wifi-watchdog
```

*(Ezt a sort a licenc „Notices" szakasza alapján mindenkinek tovább kell vinnie,
aki a szoftvert továbbadja.)* A szerzőség emberi és gépi részének elhatárolása:
[AUTHORSHIP.md](AUTHORSHIP.md).

### Hozzájárulás

Örülök a javításoknak. Mielőtt pull requestet fogadok el, alá kell írnod a
[CLA.md](CLA.md)-t — egy rövid nyilatkozatot arról, hogy a beküldött kódot én is
felhasználhatom, beleértve a kereskedelmi engedélyeket. Enélkül a hozzájárulásod
később megkötné a projektet.

### Védjegyek

Ez a projekt nem áll kapcsolatban a Mikrotikls SIA-val, a Home Assistant projekttel, sem más olyan harmadik féllel, amelynek termékével együttműködik, és egyikük sem támogatja. A védjegyek a jogosultjaik tulajdonát képezik.
