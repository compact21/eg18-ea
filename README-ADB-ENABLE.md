# Abilitazione interfaccia ADB su modulo Quectel EG18-EA

Procedura per abilitare l'interfaccia ADB sul modulo LTE Quectel EG18-EA
su router Zyxel LTE5398-M904 con OpenWrt.

---

## Indice

- [Prerequisiti](#prerequisiti)
- [Verifica stato ADB](#verifica-stato-adb)
- [Generazione chiave di sblocco](#generazione-chiave-di-sblocco)
- [Sblocco ADB](#sblocco-adb)
- [Abilitazione interfaccia ADB](#abilitazione-interfaccia-adb)
- [Riavvio router](#riavvio-router)
- [Verifica finale](#verifica-finale)
- [Note critiche](#note-critiche)

---

## Prerequisiti

- Router con OpenWrt installato e funzionante
- Connessione SSH al router (`ssh root@192.168.1.1`)
  > Per utenti Windows è disponibile [PuTTY](https://www.putty.org/) come client SSH
- `picocom` disponibile sul router (`apk add picocom` oppure tramite GUI `System → Software`)
- `adb` disponibile sul router (`apk add adb`)

> **Nota**: Se presente **ModemManager**, rimuoverlo temporaneamente e riavviare
>           il router senza il pacchetto installato, in quanto può entrare in
>           conflitto con i comandi AT durante la procedura.

---

## Verifica stato ADB

Verificare prima se ADB è già abilitato sul modulo.

Aprire una sessione sulla porta AT del modulo:

```sh
picocom /dev/ttyUSB2
```

Digitare:

```
AT+QCFG="usbcfg"
```

Output atteso:

```
+QCFG: "usbcfg",0x2C7C,0x0512,1,1,1,1,1,1,0
OK
```

Il significato dei parametri è il seguente:

| Parametro | Valore esempio | Descrizione         |
|-----------|----------------|---------------------|
| vid       | 0x2C7C         | Vendor ID           |
| pid       | 0x0512         | Product ID          |
| diag      | 1              | Porta diagnostica   |
| nmea      | 1              | Porta NMEA          |
| at_port   | 1              | Porta AT            |
| modem     | 1              | Porta modem         |
| rmnet     | 1              | Interfaccia rmnet   |
| adb       | 1              | Interfaccia ADB     |
| uac       | 0              | Audio USB (UAC)     |

Il parametro **adb** indica lo stato dell'interfaccia ADB:
- `1` = ADB abilitato — procedura non necessaria
- `0` = ADB disabilitato — procedere con la procedura seguente

Uscire da picocom: `Ctrl-a` poi `Ctrl-x`.

Verificare che ADB sia accessibile da shell:

```sh
adb devices
```

Output atteso se ADB è abilitato:

```
List of devices attached
a12b3c45        device
```

---

## Generazione chiave di sblocco

Aprire una sessione sulla porta AT del modulo:

```sh
picocom /dev/ttyUSB2
```

Richiedere al modulo il numero necessario per generare la chiave di sblocco:

```
AT+QADBKEY?
```

Output atteso:

```
+QADBKEY: 29442446
OK
```

Salvare il numero restituito (es. `29442446`).

Uscire da picocom: `Ctrl-a` poi `Ctrl-x`.

Per generare la chiave di sblocco utilizzare il tool online:

> **[onecompiler.com/python/3znepjcsq](https://onecompiler.com/python/3znepjcsq)**

Inserire il numero restituito da `AT+QADBKEY?` nel campo **STDIN** e premere **Run**.

Esempio con input `12345678`:

```
STDIN:  12345678

Output: AT+QADBKEY="0jXKXQwSwMxYoeg"
```

> **Nota**: per chi preferisce eseguire lo script in locale, il codice sorgente
>           Python è il seguente (richiede il modulo `crypt`, disponibile su
>           sistemi Linux/macOS):
>
> ```python
> import logging
> import os
> import argparse
> import sys
>
> def generateUnlockKey(sn):
>     """
>     @param sn: the serial number to generate an unlock key for
>     """
>     salt = "$1${0}$".format(sn)
>     c = crypt("SH_adb_quectel", salt)
>     return c[12:27]
>
> def main():
>     key = input("Enter the AT+QADBKEY? response: ")
>     c = generateUnlockKey(key)
>     print('AT+QADBKEY="{0}"'.format(c))
>
> if __name__ == "__main__":
>     logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.ERROR)
>     try:
>         from crypt import crypt
>         main()
>     except ImportError as e:
>         logging.error(e)
> ```

---

## Sblocco ADB

Aprire nuovamente picocom:

```sh
picocom /dev/ttyUSB2
```

Inviare la chiave generata dal tool:

```
AT+QADBKEY="0jXKXQwSwMxYoeg"
```

> **Nota**: sostituire `0jXKXQwSwMxYoeg` con la chiave generata dal proprio numero.

Il modulo risponde con `OK`.

---

## Abilitazione interfaccia ADB

Dalla stessa sessione picocom, abilitare l'interfaccia ADB nella configurazione USB del modulo:

```
AT+QCFG="usbcfg",0x2C7C,0x0512,1,1,1,1,1,1,0
```

Il modulo risponde con `OK`.

Uscire da picocom: `Ctrl-a` poi `Ctrl-x`.

> **Nota**: i parametri VID (`0x2C7C`) e PID (`0x0512`) sono **specifici**
>           del modulo EG18-EA — verificare i valori corretti per altri moduli
>           Quectel prima di utilizzare questo comando. Gli altri parametri
>           devono corrispondere alla configurazione attuale rilevata con
>           `AT+QCFG="usbcfg"` — modificare **solo** il parametro `adb`.

---

## Riavvio

Per rendere effettiva la modifica è necessario riavviare il modulo LTE.

**Opzione 1** — riavvio solo del modulo LTE dalla sessione picocom:

```
AT+CFUN=1,1
```

**Opzione 2** — riavvio completo del router da SSH:

```sh
reboot
```

Attendere il riavvio completo prima di procedere con la verifica.

---

## Verifica finale

Dopo il riavvio verificare che ADB sia attivo e il modulo sia raggiungibile:

```sh
adb devices
```

Output atteso:

```
List of devices attached
a12b3c45        device
```

Verificare la configurazione USB aggiornata aprendo picocom:

```sh
picocom /dev/ttyUSB2
```

```
AT+QCFG="usbcfg"
```

Output atteso:

```
+QCFG: "usbcfg",0x2C7C,0x0512,1,1,1,1,1,1,0
OK
```

Accedere alla shell del modulo tramite ADB:

```sh
adb shell
```

---

## Note critiche

- La chiave generata dal tool è **specifica** per il numero restituito da
  `AT+QADBKEY?` — non è riutilizzabile su altri moduli anche se l'hardware è identico
- Il tool online onecompiler potrebbe non essere disponibile in futuro —
  in tal caso utilizzare lo script Python locale indicato nella sezione
  [Generazione chiave di sblocco](#generazione-chiave-di-sblocco)
- **Non modificare i parametri VID/PID del comando** `AT+QCFG="usbcfg"` —
  **valori errati potrebbero rendere il modulo non riconoscibile dall'host**

---

## Riferimenti

- [Tool online generazione chiave ADB](https://onecompiler.com/python/3znepjcsq)
- [README-DFOTA-UPGRADE-ADB.md](https://github.com/compact21/eg18-ea/blob/main/README-DFOTA-UPGRADE-ADB.md) — utilizzo di ADB per aggiornamento DFOTA
- [Quectel forum - How to enable ADB interface for RM520N-GL](https://forums.quectel.com/t/how-to-enable-adb-interface-for-rm520n-gl/34942)
- [Discussione tecnica su fibra.click](https://forum.fibra.click/d/73663-zyxel-lte7490-m904-modulo-modem-eg18-inaccessibile)
- [Zyxel LTE5398-M904 OpenWrt Wiki](https://openwrt.org/toh/zyxel/lte5398-m904)
