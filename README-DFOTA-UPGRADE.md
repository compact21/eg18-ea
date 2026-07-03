# Aggiornamento firmware Quectel EG18-EA via DFOTA (AT commands)

Procedura per l'aggiornamento del firmware del modulo LTE Quectel EG18-EA
tramite comandi AT su router Zyxel LTE5398-M904 con OpenWrt.

> **Nota**: questa procedura utilizza il metodo DFOTA (Delta Firmware Over The Air)
>           tramite download HTTPS diretto dal modulo.

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
- [Avvio aggiornamento DFOTA](#avvio-aggiornamento-dfota)
- [Monitoraggio progresso](#monitoraggio-progresso)
- [Verifica post-flash](#verifica-post-flash)
- [Ripristino connessione](#ripristino-connessione)
- [Note critiche](#note-critiche)

---

## Prerequisiti

- Router con OpenWrt installato e funzionante
- Connessione SSH al router
- `picocom` disponibile sul router (`apk add picocom` oppure tramite GUI `System → Software`)
- File DFOTA corretto per la coppia di versioni (partenza → arrivo)
- URL HTTPS raggiungibile dal modulo dove è ospitato il file DFOTA
- UPS collegato per alimentazione stabile durante il flash

---

## Accesso SSH al router

Connettersi al router tramite SSH:

```sh
ssh root@192.168.1.1
```

> **Nota**: `192.168.1.1` è l'indirizzo IP di default — se è stato modificato
>           usare l'indirizzo corretto. Per utenti Windows è disponibile
>           [PuTTY](https://www.putty.org/) come client SSH.

---

## Accesso alla porta AT del modulo

Aprire una sessione sulla porta AT del modulo:

```sh
picocom /dev/ttyUSB2
```

> **Nota**: su OpenWrt sono accessibili per i comandi AT sia `/dev/ttyUSB2`
>           che `/dev/ttyUSB3` — entrambe funzionano.

Output atteso all'avvio:

```
picocom v3.1
port is        : /dev/ttyUSB2
flowcontrol    : none
baudrate is    : 9600
...
Terminal ready
```

Verificare che la porta risponda correttamente:

```
AT
OK
```

Per uscire da picocom: `Ctrl-a` poi `Ctrl-x`.

> **Nota**: tutti i comandi AT nelle sezioni seguenti vanno digitati
>           direttamente nella sessione picocom aperta sul router.

---

## Identificazione del tipo di file firmware

I file di aggiornamento per EG18-EA esistono in due formati distinti e **incompatibili**:

| Formato   | Dimensione tipica | Metodo                                |
|-----------|-------------------|---------------------------------------|
| DFOTA     | ~40 MB            | Questa procedura (AT commands)        |
| qfirehose | >100 MB           | Procedura separata via porta EDL 9008 |

La nomenclatura del file indica la direzione dell'aggiornamento:

```
Update_EG18EAPAR01A08V05M4G-R01A13M4G_01.200.01.200_V02.zip
              ↑ partenza              ↑ arrivo
```

Utilizzare sempre il file corrispondente alla propria revisione di partenza.
La procedura di downgrade è identica a quella di upgrade — basta usare il file
con la direzione inversa **se supportato** dal pacchetto DFOTA.
es. `Update_R01A13M4G_...-EG18EAPAR01A08V05M4G.zip`.

---

## Preparazione

Fermare tutto quello che può interferire con la porta AT o tentare
recovery automatici della connessione durante il flash.

Da una seconda sessione SSH sul router (mantenere picocom aperto):

```sh
# fermare la connessione WAN
ifdown wan

# fermare eventuali watchdog se presenti (da adattare alla situazione del router)
/etc/init.d/watchdog stop
/etc/init.d/watchcat stop
```

> **Nota**: Se presente **ModemManager**, rimuoverlo temporaneamente e riavviare
>           il router senza il pacchetto installato, in quanto può entrare in
>           conflitto con i comandi AT durante la procedura.

---

## Verifica stato pre-flash

Dalla sessione picocom, digitare i seguenti comandi e salvare l'output
per confronto post-flash:

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
Revision: EG18EAPAR01A08M4G
OK

AT+QGMR
EG18EAPAR01A08M4G
OK

AT+CSUB
SubEdition: V05
OK
```

> **Nota**: il comando `ATI` mostra la revisione firmware attualmente installata —
>           verificarla prima di scegliere il file DFOTA corretto.

---

## Avvio aggiornamento DFOTA

Dalla sessione picocom, digitare:

```
AT+QFOTADL="https://url_del_file_dfota.zip"
```

Il modulo risponde con `OK` e avvia autonomamente il download.

Esempio con file pubblico noto (da rev 8 a rev 13):

```
AT+QFOTADL="https://quec-pro-oss.oss-cn-shanghai.aliyuncs.com/fota/9000/Update_EG18EAPAR01A08V05M4G-R01A13M4G_01.200.01.200_V02.zip"
```

---

## Monitoraggio progresso

Dopo aver digitato `AT+QFOTADL` la sessione picocom corrente potrebbe
interrompersi — è normale. Aprire una nuova sessione picocom sulla stessa porta:

```sh
picocom /dev/ttyUSB2
```

Gli indicatori `+QIND` appariranno automaticamente nella nuova sessione.

```
+QIND: "FOTA","HTTPSSTART"       # download avviato
+QIND: "FOTA","HTTPSEND",0       # download completato con successo
+QIND: "FOTA","START"            # flash avviato
+QIND: "FOTA","UPDATING",1       # avanzamento flash (percentuale)
+QIND: "FOTA","UPDATING",2
+QIND: "FOTA","UPDATING",n
+QIND: "FOTA","UPDATING",100     # flash completato
+QIND: "FOTA","END",0            # aggiornamento completato con successo
```

Dopo `END,0` il modulo si riavvia autonomamente. La sequenza di riavvio
attesa è visibile direttamente in picocom:

```
RDY
+CPIN: READY
+QUSIM: 1
+CFUN: 1
+QIND: SMS DONE
+QIND: PB DONE
```

**Non interrompere l'alimentazione durante l'intera procedura.**

Tempi indicativi (da log reale, rev 8 → rev 13):

| Fase       | Durata         |
|------------|----------------|
| Download   | ~1 minuto      |
| Flash      | ~8 minuti      |
| Riavvio    | ~30 secondi    |
| **Totale** | **~10 minuti** |

---

## Verifica post-flash

Dalla sessione picocom, dopo il riavvio del modulo:

```
ATI
AT+QGMR
AT+CSUB
AT+CVERSION
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

Se in alternativa si preferisce ModemManager, installarlo e riavviare il router.
Se era stata rimossa la SIM, reinserirla e attendere la registrazione in rete.

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

---

## Riferimenti

- [OpenWrt forum - DFOTA upgrade](https://forum.openwrt.org/t/openwrt-support-for-zyxel-lte5398-m904/140157/61)
- [Quectel forum - LTE5398-M904 module update](https://forums.quectel.com/t/lte5398-m904-module-update/52887/4)
- [Quectel forum - downgrade warning](https://forums.quectel.com/t/request-for-downgrade-firmware-dfota-package-for-eg18-ea-mikrotik-chateau-due-to-regional-lock/58484/4)
- [Discussione tecnica su fibra.click](https://forum.fibra.click/d/73663-zyxel-lte7490-m904-modulo-modem-eg18-inaccessibile)
- [Zyxel LTE5398-M904 OpenWrt Wiki](https://openwrt.org/toh/zyxel/lte5398-m904)
