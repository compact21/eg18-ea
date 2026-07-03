# Aggiornamento firmware Quectel EG18-EA via DFOTA con trasferimento ADB

Procedura per l'aggiornamento del firmware del modulo LTE Quectel EG18-EA
tramite trasferimento del file via ADB e comandi AT su router Zyxel LTE5398-M904
con OpenWrt.

> **Nota**: questa procedura utilizza il metodo DFOTA (Delta Firmware Over The Air)
>           con trasferimento locale del file via ADB — non richiede server HTTPS
>           esterni né pubblicazione del file online.
>
> **Prerequisito**: ADB deve essere abilitato e accessibile sul modulo EG18-EA.
>           Vedi [README-ADB-ENABLE.md](https://github.com/compact21/eg18-ea/blob/main/README-ADB-ENABLE.md) per la procedura
>           di abilitazione.

## ⚠ Avvertenza

**Procedura ad alto rischio. Un errore può rendere il modem inutilizzabile**

**Questa procedura è destinata esclusivamente ai proprietari del dispositivo per l'accesso al proprio hardware.
L'autore non fornisce alcuna garanzia e l'utilizzo è a proprio rischio**

---

## Indice

- [Prerequisiti](#prerequisiti)
- [Identificazione del tipo di file firmware](#identificazione-del-tipo-di-file-firmware)
- [Preparazione](#preparazione)
- [Verifica stato pre-flash](#verifica-stato-pre-flash)
- [Trasferimento file su /tmp del router](#trasferimento-file-su-tmp-del-router)
- [Trasferimento file via ADB](#trasferimento-file-via-adb)
- [Avvio aggiornamento DFOTA](#avvio-aggiornamento-dfota)
- [Monitoraggio progresso](#monitoraggio-progresso)
- [Verifica post-flash](#verifica-post-flash)
- [Ripristino connessione](#ripristino-connessione)
- [Note critiche](#note-critiche)

---

## Prerequisiti

- Router con OpenWrt installato e funzionante
- Connessione SSH al router (`ssh root@192.168.1.1`)
  > Per utenti Windows è disponibile [PuTTY](https://www.putty.org/) come client SSH
  > e [WinSCP](https://winscp.net/) per la copia dei file verso il router
- `picocom` disponibile sul router (`apk add picocom` oppure tramite GUI `System → Software`)
- `adb` disponibile sul router (`apk add adb`  oppure tramite GUI `System → Software`)
- ADB abilitato sul modulo EG18-EA (vedi [README-ADB-ENABLE.md](https://github.com/compact21/eg18-ea/blob/main/README-ADB-ENABLE.md))
- File DFOTA corretto per la coppia di versioni (partenza → arrivo) disponibile sul router
- UPS collegato per alimentazione stabile durante il flash

---

## Identificazione del tipo di file firmware

I file di aggiornamento per EG18-EA esistono in due formati distinti e **incompatibili**:

| Formato   | Dimensione tipica | Metodo                                |
|-----------|-------------------|---------------------------------------|
| DFOTA     | ~40 MB            | Questa procedura (AT commands)        |
| qfirehose | >100 MB           | Procedura separata via porta EDL 9008 |

La nomenclatura del file indica la direzione dell'aggiornamento:

```
Upgrade_EG18EAPAR01A12M4G_01.001.01.001-R01A13M4G_01.001.01.001.zip
                ↑ partenza                       ↑ arrivo
```

Utilizzare sempre il file corrispondente alla propria revisione di partenza.
La procedura di downgrade è identica a quella di upgrade — basta usare il file
con la direzione inversa **se supportato** dal pacchetto DFOTA.

---

## Preparazione

Fermare tutto quello che può interferire con la porta AT o tentare
recovery automatici della connessione durante il flash.

Da una sessione SSH sul router:

```sh
# fermare eventuali watchdog se presenti (da adattare alla situazione del router)
/etc/init.d/watchdog stop
/etc/init.d/watchcat stop

# fermare la connessione WAN
ifdown wan
```

> **Nota**: Se presente **ModemManager**, rimuoverlo temporaneamente e riavviare
>           il router senza il pacchetto installato, in quanto può entrare in
>           conflitto con i comandi AT durante la procedura.

---

## Verifica stato pre-flash

Aprire una sessione sulla porta AT del modulo:

```sh
picocom /dev/ttyUSB2
```

> **Nota**: su OpenWrt sono accessibili per i comandi AT sia `/dev/ttyUSB2`
>           che `/dev/ttyUSB3` — entrambe funzionano.

Digitare i seguenti comandi e salvare l'output per confronto post-flash:

```
ATI
AT+QGMR
AT+CSUB
AT+CVERSION
```

Esempio output atteso:

```
ATI
Quectel
EG18
Revision: EG18EAPAR01A12M4G
OK

AT+QGMR
EG18EAPAR01A12M4G_01.001.01.001
OK

AT+CSUB
SubEdition: V01
OK

AT+CVERSION
VERSION: EG18EAPAR01A12M4G
Sep 27 2021 09:53:17
Authors: QCT
OK
```

> **Nota**: il comando `ATI` mostra la revisione firmware attualmente installata —
>           verificarla prima di scegliere il file DFOTA corretto.

Uscire da picocom: `Ctrl-a` poi `Ctrl-x`.

---

## Trasferimento file su /tmp del router

Dal PC, copiare il file DFOTA nella directory `/tmp` del router:

```sh
scp Upgrade_EG18EAPAR01A12M4G_01.001.01.001-R01A13M4G_01.001.01.001.zip \
    root@192.168.1.1:/tmp/Upgrade_EG18EAPAR01A12M4G_01.001.01.001-R01A13M4G_01.001.01.001.zip
```

> **Nota**: per utenti Windows utilizzare WinSCP per trasferire il file.

---

## Trasferimento file via ADB

Copiare il file DFOTA dalla directory `/tmp` del router nella memoria UFS del modulo tramite ADB:

```sh
# Da adattare al file di origine
LOCAL_FILE="/tmp/Upgrade_EG18EAPAR01A12M4G_01.001.01.001-R01A13M4G_01.001.01.001.zip"

REMOTE_PATH="/cache/ufs/DFOATUpgrade.zip"

adb push "$LOCAL_FILE" "$REMOTE_PATH"
```

Verificare che il checksum del file corrisponda a quello del file di origine —
i due hash devono essere **identici**:

```sh
sha256sum $LOCAL_FILE
adb shell sha256sum $REMOTE_PATH
```

Esempio output atteso (rev 12 → rev 13):

```
522f880e42b90bf3c4c60d5e3cf4c72cbe0a8b1bf4056bc9df4612e01392af46  /tmp/Upgrade_EG18EAPAR01A12M4G_01.001.01.001-R01A13M4G_01.001.01.001.zip
522f880e42b90bf3c4c60d5e3cf4c72cbe0a8b1bf4056bc9df4612e01392af46  /cache/ufs/DFOATUpgrade.zip
```

**Se i due hash sono diversi interrompere immediatamente la procedura** —
il file trasferito **è corrotto e non deve essere utilizzato** per il flash.

Verificare che il file sia visibile lato AT aprendo nuovamente picocom:

```sh
picocom /dev/ttyUSB2
```

e digitando:

```
AT+QFLST="*"
```

Output atteso (la dimensione deve corrispondere al file trasferito):

```
+QFLST: "UFS:DFOATUpgrade.zip",41440551
OK
```

---

## Avvio aggiornamento DFOTA

Dalla sessione picocom, digitare:

```
AT+QFOTADL="/cache/ufs/DFOATUpgrade.zip"
```

Il modulo risponde con `OK` e avvia autonomamente il flash.

Dopo l'`OK` la sessione picocom si interromperà con il messaggio:

```
FATAL: read zero bytes from port
term_exitfunc: reset failed for dev UNKNOWN: Not a tty
```

È normale — il modulo ha resettato la porta AT per avviare il processo di aggiornamento.

---

## Monitoraggio progresso

Aprire una nuova sessione picocom sulla stessa porta:

```sh
picocom /dev/ttyUSB2
```

Gli indicatori `+QIND` appariranno automaticamente:

```
+QIND: "FOTA","START"            # flash avviato
+QIND: "FOTA","UPDATING",0       # avanzamento flash (percentuale)
+QIND: "FOTA","UPDATING",1
+QIND: "FOTA","UPDATING",2
+QIND: "FOTA","UPDATING",n
+QIND: "FOTA","UPDATING",99
+QIND: "FOTA","UPDATING",100     # flash completato
+QIND: "FOTA","END",0            # aggiornamento completato con successo
```

> **Nota**: con file locale non è presente la fase di download HTTP/HTTPS —
>           la sequenza parte direttamente da `START`.

Dopo `END,0` la sessione picocom si interromperà nuovamente con lo stesso
messaggio `FATAL` — il modulo si sta riavviando autonomamente.

**Non interrompere l'alimentazione durante l'intera procedura.**

Tempi indicativi (rev 12 → rev 13):

| Fase              | Durata           |
|-------------------|------------------|
| Trasferimento ADB | ~variabile       |
| Flash             | ~10/20 minuti    |
| Riavvio           | ~30/60 secondi   |

---

## Verifica post-flash

Aprire una nuova sessione picocom dopo il riavvio del modulo:

```sh
picocom /dev/ttyUSB2
```

Digitare:

```
ATI
AT+QGMR
AT+CSUB
AT+CVERSION
```

Esempio output atteso (rev 12 → rev 13):

```
ATI
Quectel
EG18
Revision: EG18EAPAR01A13M4G
OK

AT+QGMR
EG18EAPAR01A13M4G_01.001.01.001
OK

AT+CSUB
SubEdition: V01
OK

AT+CVERSION
VERSION: EG18EAPAR01A13M4G
Aug 15 2023 14:07:36
Authors: QCT
OK
```

Confrontare con i valori salvati nella fase di pre-flash.
La revisione riportata da `AT+QGMR` deve corrispondere alla versione di arrivo attesa.

---

## Ripristino connessione

Da una sessione SSH sul router:

```sh
# attivare la connessione WAN
ifup wan

# far ripartire eventuali watchdog se presenti (da adattare alla situazione del router)
/etc/init.d/watchdog start
/etc/init.d/watchcat start
```

---

## Note critiche

- **Non usare mai** `AT+QFOTADL` con file in formato qfirehose —
  sono procedure diverse e incompatibili tra loro
- Il file DFOTA deve corrispondere **esattamente** alla revisione di partenza:
  un file con revisione di partenza errata viene rifiutato dal modulo
- L'aggiornamento DFOTA **potrebbe non essere reversibile** in alcune coppie
  di versioni — verificare le release notes prima di procedere e valutare
  se i cambiamenti giustificano il rischio
- Il modulo EG18-EA è **saldato sulla scheda madre** — in caso di hard brick
  il recupero non è semplice e richiede accesso JTAG o sostituzione hardware
- Non usare mai l'opzione `-e` di qfirehose (procedura separata) in quanto
  cancella i dati di calibrazione del modulo in modo irreversibile
- Se il file trasferito via ADB rimane nella UFS del modulo — rimuoverlo
  dopo l'aggiornamento con:

```
AT+QFDEL="UFS:DFOATUpgrade.zip"
```

---

## Riferimenti

- [README-DFOTA-UPGRADE.md](https://github.com/compact21/eg18-ea/blob/main/README-DFOTA-UPGRADE.md) — procedura alternativa via URL HTTPS
- [README-ADB-ENABLE.md](https://github.com/compact21/eg18-ea/blob/main/README-ADB-ENABLE.md) — abilitazione ADB sul modulo EG18-EA
- [OpenWrt forum - DFOTA upgrade](https://forum.openwrt.org/t/openwrt-support-for-zyxel-lte5398-m904/140157/61)
- [Quectel forum - LTE5398-M904 module update](https://forums.quectel.com/t/lte5398-m904-module-update/52887/4)
- [Discussione tecnica su fibra.click](https://forum.fibra.click/d/73663-zyxel-lte7490-m904-modulo-modem-eg18-inaccessibile)
- [Zyxel LTE5398-M904 OpenWrt Wiki](https://openwrt.org/toh/zyxel/lte5398-m904)
