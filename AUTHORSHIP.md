# Szerzőség / Authorship

**Projekt / Project:** `mikrotik-wifi-watchdog`
**Szerző / Author:** Bozó Bernát
**Első kiadás / First release:** 2026-09-26

## Magyar

Ez a projekt **ember által tervezett és irányított munka, amelynek kódját
részben MI-eszköz (Claude, Anthropic) segítségével írtuk.** A gépi
közreműködést nyíltan vállalom; az alábbiakat viszont ember végezte, és ezek
együtt adják a mű szerzői jogilag releváns részét:

- **A feladat és a követelmények meghatározása.** Mit csináljon a rendszer, mit
  ne, milyen esetekre kell működnie, mi számít hibának.
- **Az architektúra és a tervezési döntések:** a regisztrációs tábla olvasása a DHCP-lease-ek helyett; riasztás csak újonnan érkező MAC-re, nem minden lekérdezésre; csak olvasó router-hozzáférés; a hibás lekérdezés soha ne legyen riasztás.
- **A válogatás és az elrendezés.** Mi került be a projektbe és mi maradt ki,
  milyen sorrendben és szerkezetben — beleértve azt is, mely megoldásokat
  vetettem el.
- **A tényleges tesztelés valós eszközökön:** saját otthoni hálózaton, folyamatos üzemben 2026 augusztusa óta, 15 perces időzítővel; a whitelist hetek alatt, valós eszközökre hangolva.
- **A hibák felismerése és a javítások iránya:** a riasztási zaj csökkentése (csak új érkezésre), és a kiadás előtti átvizsgálásban talált csendes hibamód (hibás whitelist esetén a systemd sikernek könyveli a kilépést) — ez a README-ben figyelmeztetésként szerepel.
- **Az üzemeltetési tapasztalat visszavezetése a kódba.** Amit éles használat
  közben tanultam, és ami emiatt megváltozott a megoldásban.

A projekt **egésze** — a felépítése, az összeválogatása és az elrendezése —
szintén az én szerzői döntéseim eredménye, függetlenül attól, hogy az egyes
kódrészletek hogyan készültek.

## English

This project is **human-conceived and human-directed work whose code was written
in part with the help of an AI tool (Claude, by Anthropic).** I disclose the
machine contribution openly. The following, however, was done by a human, and
together these constitute the copyright-relevant part of the work:

- **Definition of the problem and the requirements** — what the system must do,
  what it must not, which cases it must handle, what counts as a failure.
- **Architecture and design decisions:** reading the radio registration table instead of DHCP leases; alerting only on newly arrived MACs, not on every poll; read-only router access; a failed query must never become an alert.
- **Selection and arrangement** — what went into the project and what stayed
  out, in what structure, including which approaches were rejected.
- **Actual testing on real devices:** on my own home network, in continuous operation since August 2026 on a 15-minute timer; the whitelist tuned to real devices over weeks.
- **Identifying defects and directing the fixes:** reducing alert noise (new arrivals only), and the quiet failure mode found in the pre-release review (with a broken whitelist the systemd unit books the exit as success) — documented in the README as a warning.
- **Feeding operational experience back into the code.**

The project **as a whole** — its structure, selection and arrangement — is the
result of my authorial choices, regardless of how individual code fragments were
produced.

## Required Notice

A licenc „Notices" szakasza szerint mindenkinek, aki a szoftvert továbbadja,
tovább kell vinnie a `Required Notice:` kezdetű sorokat. / Under the licence's
"Notices" section, anyone who passes the software on must keep the lines starting
with `Required Notice:`.

```
Required Notice: Copyright Bozó Bernát — https://github.com/bozobernat/mikrotik-wifi-watchdog
```

## Ami nem ebben a fájlban dől el / What this file does not settle

Ez a feljegyzés a védhetőséget **javítja**, de nem tesz bizonyossá: a gépi
közreműködéssel készült művek jogi megítélése 2026-ban sem letisztázott, és
országonként eltér. Két dolog ettől függetlenül is áll: (1) a PolyForm
„Acceptance" szakasza szerint a feltételeket kötelezettségként ÉS feltételként
is el kell fogadni ahhoz, hogy bárki bármilyen engedélyt kapjon — aki elfogadta,
majd megszegi, az megállapodást szegett; (2) a projekt és a szerző neve nem a
szerzői jogon múlik.

This record **strengthens** the claim but does not make it certain: the legal
treatment of works made with machine assistance is unsettled in 2026 and varies
by country. Two things hold regardless: (1) under the PolyForm "Acceptance"
section the terms must be accepted as both obligations and conditions before any
licence is granted — whoever accepts and then breaches them breaches an
agreement; (2) the project's and the author's name do not depend on copyright.
