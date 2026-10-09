# Py-Managed-OpenVPN

Server **OpenVPN gestito via API REST**. Un servizio Python (Flask + Gunicorn) si occupa di:

- creare e mantenere una **PKI** completa (CA, certificato server, CRL, chiave `tls-crypt`);
- generare la configurazione del server OpenVPN e le **regole `iptables`** coerenti con la modalità scelta;
- gestire il ciclo di vita dei **client** (creazione, rinnovo, revoca, eliminazione), elencare le connessioni e produrre il file `.ovpn` pronto da importare;
- verificare periodicamente CA, certificato server e CRL tramite APScheduler;
- segnalare al container OpenVPN quando deve **riavviarsi** (ad esempio dopo una revoca).

Il tutto gira in due container Docker che condividono un volume: uno per le API, uno per il demone OpenVPN.

---

## Indice

1. [Architettura](#architettura)
2. [Requisiti](#requisiti)
3. [Avvio rapido](#avvio-rapido)
4. [Configurazione](#configurazione)
5. [Modalità di funzionamento](#modalità-di-funzionamento)
6. [API REST](#api-rest)
7. [Flusso tipico](#flusso-tipico)
8. [Struttura del volume dati](#struttura-del-volume-dati)
9. [Struttura del progetto](#struttura-del-progetto)
10. [Sviluppo locale](#sviluppo-locale)
11. [Sicurezza](#sicurezza)
12. [Risoluzione dei problemi](#risoluzione-dei-problemi)
13. [Limiti noti](#limiti-noti)

---

## Architettura

```text
                  ┌────────────────────────────┐        ┌────────────────────────────┐
  HTTP :8080      │  py-managed-openvpn        │        │  openvpn                   │   UDP :1194
 ───────────────► │  (python:3.10-alpine)      │        │  (ubuntu:22.04)            │ ◄───────────────
                  │  Flask + Gunicorn          │        │  openvpn + iptables        │
                  │                            │        │                            │
                  │  - genera PKI              │        │  - avvia openvpn           │
                  │  - genera openvpn.conf     │        │  - applica regole iptables │
                  │  - genera regole iptables  │        │  - osserva need_to_restart │
                  │  - API client              │        │    e riavvia il demone     │
                  └─────────────┬──────────────┘        └─────────────┬──────────────┘
                                │   /opt/py-managed-openvpn/target    │  /etc/openvpn-custom
                                └──────────────►  volume  ◄───────────┘
                                              `openvpn-data`
```

- **`py-managed-openvpn`** genera tutti i file di configurazione e li scrive nel volume. Non esegue il demone VPN.
- **`openvpn`** parte solo quando il servizio Python è *healthy*, legge la configurazione dal volume ed esegue OpenVPN.
- Il riavvio di OpenVPN è comandato dal file `openvpn-conf/need_to_restart`: quando il suo timestamp di modifica cambia (controllo ogni secondo), `entrypoint.bash` invia `SIGKILL` al PID salvato all'avvio, esegue `wait` per attenderne la terminazione e solo dopo avvia il nuovo processo.
- **OpenVPN usa `network_mode: host`**, mentre il servizio Python usa la rete Docker predefinita. La porta UDP 1194 viene aperta direttamente sull'host, senza pubblicazione `ports`. Le regole `iptables` eseguite dall'entrypoint del container OpenVPN modificano quindi il firewall dell'host, non un namespace isolato. La porta TCP 8080 delle API è pubblicata dal compose senza specificare un indirizzo host, quindi è esposta su tutte le interfacce dell'host (salvo regole firewall).

## Requisiti

- Host Linux con Docker e Docker Compose v2 che supporti `build.dockerfile_inline`
- Accesso al dispositivo `/dev/net/tun` sull'host
- Capability `NET_ADMIN` (già configurata nel compose)
- Porta **UDP 1194** raggiungibile dai client e porta **TCP 8080** per le API
- Connessione Internet durante la build: l'immagine OpenVPN basata su Ubuntu 22.04 installa `openvpn` e `iptables` nella definizione inline del compose; l'immagine Python installa dipendenze Python, OpenSSL e OpenVPN
- Forwarding IPv4 attivo sull'host (`sysctl net.ipv4.ip_forward` deve restituire `1`); il progetto non lo abilita automaticamente

> La subnet VPN deve essere distinta dalle reti Docker, dalle reti private da raggiungere e dalle reti locali dei client. In modalità host verifica anche che UDP 1194 e l'interfaccia `tun0` non siano già utilizzati da un altro servizio.

## Avvio rapido

1. Crea (o modifica) il file `.env` nella radice del progetto:

   ```dotenv
   OPENVPN_SERVER_HOSTNAME=vpn.example.com
   OPENVPN_SERVER_NETWORK_ADDRESS=172.16.0.0
   OPENVPN_SERVER_NETWORK_MASK=20
   OPENVPN_SERVER_NETWORK_MODE=resource_only

   OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_0_NETWORK_ADDRESS=192.168.1.0
   OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_0_NETWORK_MASK=24
   ```

2. Avvia lo stack:

   ```bash
   docker compose up -d --build
   ```

3. Controlla che entrambi i container siano `healthy`:

   ```bash
   docker compose ps
   docker compose logs -f
   ```

4. Crea un client e scarica il suo profilo (vedi [Flusso tipico](#flusso-tipico)).

Per fermare tutto:

```bash
docker compose down        # mantiene il volume (PKI e configurazione)
docker compose down -v     # elimina anche il volume: la PKI va rigenerata
```

> ⚠️ `down -v` cancella la CA e la PKI persistente: i profili client precedenti non saranno più utilizzabili con la nuova PKI generata al successivo avvio.

## Configurazione

Tutta la configurazione avviene tramite **variabili d'ambiente** (file `.env`, caricato dal compose e da `python-dotenv`).

### Server OpenVPN

| Variabile                        | Default                   | Descrizione                                                                                                                                                                                                                           |
|----------------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `OPENVPN_SERVER_HOSTNAME`        | *(nessuno)*               | Hostname o IP pubblico scritto nella direttiva `remote` dei profili client. Va impostata per ottenere profili utilizzabili; il codice non ne verifica la presenza all'avvio.                                                          |
| `OPENVPN_SERVER_NETWORK_ADDRESS` | `10.77.0.0`               | Indirizzo della rete VPN assegnata ai client.                                                                                                                                                                                         |
| `OPENVPN_SERVER_NETWORK_MASK`    | `24`                      | Lunghezza del prefisso della rete VPN (notazione CIDR).                                                                                                                                                                               |
| `OPENVPN_SERVER_NETWORK_MODE`    | `full_tunnel` (effettivo) | `full_tunnel` oppure `resource_only` (vedi [Modalità](#modalità-di-funzionamento)). Il valore non distingue maiuscole/minuscole; un valore non riconosciuto ricade silenziosamente su `full_tunnel` (`OpenVPNModeEnums.FULL_TUNNEL`). |

> Il valore di fallback passato attualmente a `os.getenv` nel codice è ancora `PASSTHROUGH`: non essendo più
> riconosciuto dall'enum, viene convertito in `FULL_TUNNEL`. Per una configurazione esplicita usa
> `OPENVPN_SERVER_NETWORK_MODE=full_tunnel`.

### Route per `resource_only`

Per ogni rete privata raggiungibile tramite VPN definisci una coppia di variabili con lo **stesso indice numerico**:

| Variabile | Descrizione |
|---|---|
| `OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_<n>_NETWORK_ADDRESS` | Indirizzo di rete (es. `192.168.1.0`). |
| `OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_<n>_NETWORK_MASK` | Prefisso CIDR (es. `24`). |

- L'indice `<n>` può essere qualsiasi numero: non serve che sia contiguo.
- Una coppia incompleta (manca indirizzo o maschera) viene **ignorata** e segnalata con un warning nei log.
- Le coppie complete non vengono validate come indirizzi/prefissi IP: valori non validi possono rendere errata la configurazione generata o il relativo script `iptables`.

### DNS inviato ai client

| Variabile | Descrizione |
|---|---|
| `OPENVPN_SERVER_DNS_<n>_ADDRESS` | Server DNS inviato ai client con `dhcp-option DNS`. Puoi definirne più di uno cambiando indice. |

Comportamento se non ne definisci nessuno:

- in **`full_tunnel`** vengono usati `8.8.8.8` e `8.8.4.4`;
- in **`resource_only`** **non viene inviato alcun DNS**, così i client continuano a usare il proprio DNS per il traffico non VPN.

Se ti serve risolvere nomi interni in `resource_only`, indica un DNS **raggiungibile tramite le route della VPN**:

```dotenv
OPENVPN_SERVER_DNS_0_ADDRESS=192.168.1.1
```

### Certification Authority e certificato server

| Variabile | Default |
|---|---|
| `CERTIFICATION_AUTHORITY_COUNTRY` | `IT` |
| `CERTIFICATION_AUTHORITY_ORGANIZATION` | `MiaOrganizzazione` |
| `CERTIFICATION_AUTHORITY_ORGANIZATION_UNIT` | `<ORGANIZATION>-VPN` |
| `CERTIFICATION_AUTHORITY_COMMON_NAME` | `<ORGANIZATION>-VPN-CA` |
| `SERVER_COUNTRY` | valore di `CERTIFICATION_AUTHORITY_COUNTRY` |
| `SERVER_ORGANIZATION` | valore di `CERTIFICATION_AUTHORITY_ORGANIZATION` |
| `SERVER_ORGANIZATION_UNIT` | valore di `CERTIFICATION_AUTHORITY_ORGANIZATION_UNIT` |
| `SERVER_COMMON_NAME` | `server` |

> Queste variabili vengono lette a ogni avvio, ma cambiare i valori non forza la rigenerazione dei certificati già presenti. Verranno usate nelle successive emissioni o nei rinnovi previsti dal codice.

### Parametri crittografici (fissi)

| Elemento | Valore |
|---|---|
| Chiave CA | RSA 4096 bit, validità 3650 giorni |
| Chiavi server e client | RSA 3072 bit, certificati validi 825 giorni |
| Digest | SHA-256 |
| TLS | minimo 1.2, canale di controllo protetto con `tls-crypt` |
| Cifrari dati | `AES-256-GCM`, `AES-128-GCM`, `CHACHA20-POLY1305` |
| Scambio chiavi | ECDH (`dh none`) |
| Protocollo / porta | UDP 1194 |

## Modalità di funzionamento

### `full_tunnel` (full tunnel)

Il traffico Internet IPv4 del client passa dalla VPN; non viene configurato un full tunnel IPv6.

- Il server invia `redirect-gateway def1 bypass-dhcp`.
- Se non configuri alcun DNS, vengono inviati `8.8.8.8` e `8.8.4.4`.
- `iptables` abilita il forwarding da `tun0` verso l'interfaccia di uscita e applica **`MASQUERADE`** sull'intera rete VPN.

### `resource_only` (split tunnel)

Solo il traffico verso le **reti elencate** passa dalla VPN (in genere reti private); tutto il resto esce dalla connessione normale del client.

- Il server invia una `push "route <rete> <maschera>"` per ogni route configurata, **senza** `redirect-gateway`.
- `iptables` genera, per ogni rete:
  - una regola `FORWARD` che consente `tun0 → interfaccia di uscita` verso quella rete;
  - una regola `MASQUERADE` (`POSTROUTING`) limitata a quella destinazione, necessaria perché le risposte tornino indietro;
- più una regola `FORWARD` per le risposte (`ESTABLISHED,RELATED`) e una regola finale **`DROP`** per tutto ciò che arriva da `tun0` e non è esplicitamente permesso.

## API REST

URL di base: `http://<host>:8080`. Creazione e rinnovo richiedono un body JSON; download, elenco connessioni, revoca ed
eliminazione non richiedono un body. Gli esiti applicativi descritti sotto sono JSON.

La definizione OpenAPI 3.1 è disponibile in [`API.yaml`](API.yaml), consultabile con un visualizzatore compatibile come
Swagger UI.

Quando il controller completa la richiesta, le risposte applicative degli endpoint client contengono `code` e `message`; download e lista connessioni aggiungono campi specifici:

```json
{ "code": 0, "message": "Success" }
```

### Codici di risposta

| `code` | Significato | HTTP |
|---|---|---|
| `0` | Operazione riuscita | 200 |
| `500` | Errore interno o chiave/certificato del client richiesto non presente | 500 |
| `1001` | Il file della chiave privata del client esiste già | 409 |
| `1002` | File richiesto non trovato (file di stato OpenVPN) | 404 |

### Endpoint client

| Metodo   | Percorso                                          | Corpo                                                                                      | Descrizione                                                                                                                                                                                                                                                                           |
|----------|---------------------------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET`    | `/py-managed-openvpn/client/{client_name}`        | –                                                                                          | Restituisce il profilo `.ovpn` codificato in Base64.                                                                                                                                                                                                                                  |
| `GET`    | `/py-managed-openvpn/client/connected`            | –                                                                                          | Legge la sezione `ROUTING TABLE` del file di stato e restituisce `connected_clients`.                                                                                                                                                                                                 |
| `POST`   | `/py-managed-openvpn/client`                      | `{"client_country":"IT","client_organization_unit":"HR","client_name":"device_name_user"}` | Crea chiave privata, richiesta e certificato firmato dalla CA.                                                                                                                                                                                                                        |
| `PATCH`  | `/py-managed-openvpn/client`                      | `{"client_name":"device_name_user"}`                                                       | Rinnova il certificato del client riutilizzando la chiave privata esistente. Se il certificato precedente non è scaduto, ne richiede la revoca, rigenera la CRL e segnala il riavvio; poi emette un certificato nuovo. Se è già scaduto, salta revoca, CRL e riavvio.                 |
| `DELETE` | `/py-managed-openvpn/client/{client_name}`        | –                                                                                          | Richiama la revoca senza verificarne il risultato e rimuove la chiave privata e il certificato del client. Non elimina la CSR, la cronologia PKI o i certificati archiviati in `newcerts`.                                                                                            |
| `DELETE` | `/py-managed-openvpn/client/{client_name}/revoke` | –                                                                                          | Se chiave e certificato esistono e il certificato non è scaduto, ne richiede la revoca, rigenera la CRL e chiede il riavvio di OpenVPN. Se è scaduto restituisce successo senza aggiornare CRL o marker; se mancano chiave o certificato restituisce `500`. Mantiene i file su disco. |

`{client_name}` è un parametro del percorso: sostituiscilo con il nome del client, ad esempio `device_name_user`.

I codici della tabella sono quelli restituiti esplicitamente dai servizi: per esempio, il download di un client senza chiave o certificato restituisce `500`, non `404`; `1002` è usato quando manca il file di stato. Le richieste non valide non hanno un gestore applicativo JSON comune: JSON malformato o content type non supportato produce l'errore HTTP standard di Flask, mentre campi obbligatori mancanti/non validi nei DTO possono causare un errore HTTP 500 non nel formato `code`/`message`.

La risposta di `GET /py-managed-openvpn/client/{client_name}` aggiunge il campo `file_data`:

```json
{
  "code": 0,
  "message": "Success",
  "file_data": "Y2xpZW50CmRldiB0dW4K..."
}
```

### Client connessi

```bash
curl -fsS http://localhost:8080/py-managed-openvpn/client/connected | jq .
```

Esempio di risposta:

```json
{
  "code": 0,
  "message": "Success",
  "connected_clients": [
    {
      "virtual_address": "172.16.0.2",
      "common_name": "device_name_user",
      "real_address": "203.0.113.10:45000",
      "last_ref": "2026-10-08 12:00:00"
    }
  ]
}
```

Le chiavi derivano dalle intestazioni CSV convertite in minuscolo con `_` al posto degli spazi. I valori restano stringhe. La risposta non include byte trasferiti o data di connessione, che appartengono alla sezione `CLIENT LIST`.

Lo schema OpenAPI `ConnectedClient` descrive i quattro campi obbligatori di ogni elemento di `connected_clients`:

| Campo             | Descrizione                                                                                    |
|-------------------|------------------------------------------------------------------------------------------------|
| `common_name`     | Common name del certificato del client.                                                        |
| `last_ref`        | Ultimo riferimento riportato da OpenVPN, nel formato `YYYY-MM-DD HH:mm:ss`, senza fuso orario. |
| `real_address`    | Indirizzo pubblico e porta del client.                                                         |
| `virtual_address` | Indirizzo virtuale assegnato al client nella VPN.                                              |

Il risultato è uno snapshot, non una lettura in tempo reale: la direttiva `status` non specifica un intervallo e OpenVPN aggiorna normalmente il file ogni 60 secondi. Se il file non esiste, l'endpoint restituisce HTTP 404 con `code: 1002`; un file incompleto o di formato diverso può invece provocare un errore interno.

`connected` è un segmento riservato: un client con questo nome non può scaricare il profilo tramite la route GET, perché prevale l'endpoint statico.

### Endpoint di servizio

| Metodo | Percorso | Risposta |
|---|---|---|
| `GET` | `/actuator/health` | `{"status": "healthy"}` |
| `GET` | `/actuator/readiness` | `{"status": "ready"}` |

Gli actuator restituiscono risposte statiche e non verificano PKI o connettività VPN. Gli healthcheck Docker sono diversi: Python controlla la connessione TCP su 8080 (ogni 5 secondi), OpenVPN controlla `pgrep -x openvpn` (ogni 10 secondi). Lo stato `healthy` di OpenVPN indica soltanto la presenza del processo. `restart: always` non riavvia automaticamente un container solo perché diventa `unhealthy`.

### Tracciamento

Ogni risposta include l'header `Request-ID` con il trace ID OpenTelemetry (`no-trace` se non c'è un trace attivo). Lo stesso identificativo compare nei log, nel formato:

```text
2026-10-07 18:14:30 [<trace_id>,<span_id>] INFO <messaggio>
```

## Flusso tipico

**1. Crea un client**

```bash
curl -X POST http://localhost:8080/py-managed-openvpn/client \
  -H 'Content-Type: application/json' \
  -d '{"client_country":"IT","client_organization_unit":"HR","client_name":"device_name_user"}'
```

**2. Scarica il profilo e salvalo come file `.ovpn`**

```bash
curl -fsS http://localhost:8080/py-managed-openvpn/client/device_name_user \
  | jq -r '.file_data' \
  | base64 -d > device_name_user.ovpn
```

`jq -r` elimina le virgolette; `base64 -d` decodifica il contenuto. Importa `device_name_user.ovpn` in un qualsiasi
client OpenVPN.

**3. Rinnova il client**

```bash
curl -X PATCH http://localhost:8080/py-managed-openvpn/client \
  -H 'Content-Type: application/json' \
  -d '{"client_name":"device_name_user"}'
```

Dopo il rinnovo scarica di nuovo il profilo, che contiene il certificato aggiornato. La chiave privata del client resta invariata; il certificato precedente viene revocato se non era già scaduto.

**4. Revoca il client**

```bash
curl -X DELETE http://localhost:8080/py-managed-openvpn/client/device_name_user/revoke
```

Quando la revoca viene eseguita, aggiorna la CRL e richiede un riavvio che interrompe **tutte** le connessioni OpenVPN, non solo quella del client revocato. Se il certificato è già scaduto, il metodo restituisce successo senza aggiornare la CRL o richiedere il riavvio.

**5. Elimina i file del client**

```bash
curl -X DELETE http://localhost:8080/py-managed-openvpn/client/device_name_user
```

Questa operazione è distinta dalla sola revoca: elimina chiave privata e certificato dopo aver richiamato la revoca. Se entrambi sono già assenti restituisce successo. Le registrazioni della CA restano nel database PKI.

## Struttura del volume dati

Il volume `openvpn-data` è montato come `/opt/py-managed-openvpn/target` nel servizio Python e come `/etc/openvpn-custom` nel container OpenVPN.

```text
openvpn-conf/
├── openvpn.conf             # configurazione del server
└── need_to_restart          # timestamp: la modifica provoca il riavvio di OpenVPN
openvpn-log/
└── status-server.log        # stato dei client connessi
openvpn-rules/
├── iptables.rules.create.bash
└── iptables.rules.delete.bash
openvpn-pki/
├── openssl.cnf              # configurazione OpenSSL generata
├── index.txt  serial  crlnumber
├── private/                 # chiavi private (CA, server, client, ta.key)
├── certs/                   # ca.crt, server.crt, certificati client
├── csr/                     # richieste di firma
├── newcerts/                # certificati emessi, per numero di serie
└── crl/ca.crl               # lista di revoca
```

Gli helper di scrittura impostano `600` sui file e creano con modalità `700` la directory finale mancante (nel rispetto dell'umask); le directory intermedie create ricorsivamente seguono la modalità predefinita e l'umask. Non correggono i permessi delle directory già esistenti. I file emessi direttamente da OpenSSL e il log OpenVPN possono avere permessi diversi. Poiché OpenVPN scende a `nobody:nogroup`, i permessi predefiniti possono impedirgli di attraversare le directory fino alla CRL o di scrivere `status-server.log`: occorre predisporre accesso in lettura/attraversamento per i file necessari e scrittura sulla directory del log, senza esporre le chiavi private. In Docker il volume contiene i dati persistenti: la cartella locale `target/` non è il bind mount usato dal compose.

### Backup

Salva l'intera PKI, inclusi chiavi, certificati, database e contatori. Per un backup coerente ferma prima entrambi i servizi, senza eliminare il volume:

```bash
docker compose stop
docker run --rm -v py-managed-openvpn_openvpn-data:/data:ro -v "$PWD":/backup alpine \
  tar czf /backup/openvpn-data.tar.gz -C /data .
chmod 600 openvpn-data.tar.gz
docker compose up -d
```

(Il nome effettivo del volume può avere un prefisso diverso: verificalo con `docker volume ls`.)

L'archivio contiene chiavi private: custodiscilo cifrato e non inserirlo nel contesto di build Docker. Per ripristinarlo, ferma i servizi ed estrai l'archivio in un volume vuoto dedicato; non mescolare PKI differenti e preserva owner e permessi.

## Struttura del progetto

```text
.
├── app.py                    # applicazione Flask e inizializzazione all'avvio
├── API.yaml                  # definizione OpenAPI delle API REST
├── entrypoint.bash           # script di avvio del container OpenVPN
├── Dockerfile                # immagine del servizio Python
├── docker-compose.yaml       # servizi, volume e healthcheck
├── requirements.txt          # dipendenze Python
├── setup.py
├── configuration/            # variabili d'ambiente e logging
├── controller/               # endpoint REST (client, actuator)
├── dto/                      # modelli Pydantic di richiesta/risposta
├── enumeration/              # modalità OpenVPN e codici di risposta
├── exception/                # eccezioni applicative
├── service/                  # CA, server, client, CRL, iptables, config OpenVPN
├── scheduling/               # APScheduler e refresh periodico della PKI
└── util/                     # inizializzazione PKI, file system, shell, rete, OpenSSL
```

### Cosa succede all'avvio

All'importazione di `app.py` il servizio verifica gli strumenti, richiama `initialization_util.initialize()` e avvia il background scheduler. L'inizializzazione esegue, in ordine:

1. verifica che `openssl` e `openvpn` siano installati;
2. crea le directory necessarie e i file base della PKI (`index.txt`, `serial`, `crlnumber`, `openssl.cnf`);
3. genera la CA e il certificato server se mancano, e li **rinnova se scadono entro 30 giorni**;
4. genera la CRL se manca (e la rinnova quando sta per scadere) e la chiave `tls-crypt`;
5. scrive `openvpn.conf` in base alla modalità scelta;
6. aggiorna `need_to_restart`;
7. genera gli script `iptables` di creazione e rimozione delle regole.

Il container `openvpn` aspetta che il servizio Python sia *healthy*, esegue **prima** `openvpn-rules/iptables.rules.create.bash`, poi avvia OpenVPN e resta in attesa di modifiche a `need_to_restart`. I pacchetti sono già installati nell'immagine durante la build.

### Refresh periodico della PKI

APScheduler registra `refresh_pki` con l'espressione cron `0 0 * * *`, quindi una volta al giorno a mezzanotte. Il job richiama `initialization_util.refresh()` per controllare CA, certificato server e CRL.

Il scheduler è configurato con timezone `UTC`, ma il `CronTrigger` viene costruito senza timezone esplicita e conserva il fuso locale del processo: il job scatta quindi a mezzanotte locale (con le transizioni dell'ora legale del fuso), non necessariamente a mezzanotte UTC.

I certificati CA/server vengono rinnovati se la validità residua calcolata scende sotto 30 giorni. La CRL viene rinnovata se la validità residua calcolata scende sotto **5 giorni** (`5 * 24 * 60 * 60 * 1000` millisecondi). Il calcolo converte date UTC con `time.mktime`, che le interpreta come orari locali: fuori da UTC il residuo può quindi risultare spostato dell'offset locale, e le soglie effettive non sono precise.

`refresh()` azzera il flag Python `need_to_restart` prima dei controlli, ma non cancella il file marker. Il marker viene riscritto solo quando uno dei controlli segnala un rinnovo di CA, certificato server o CRL, quindi il job non provoca un riavvio a ogni esecuzione se la PKI è ancora valida. Il riavvio richiesto da un rinnovo interrompe comunque le sessioni attive.

Il scheduler e l'inizializzazione vengono avviati da ogni processo che importa `app.py`. Il comando Gunicorn del Dockerfile usa il numero di worker predefinito; aumentare i worker senza riorganizzare il lifecycle duplica job e operazioni sulla PKI.

### Riavvio e arresto di OpenVPN

`start_openvpn()` salva il PID del figlio tramite `$!`. `restart_openvpn()` richiama `stop_openvpn()`, che invia `kill -9`, attende il figlio con `wait` e azzera il PID, poi avvia la nuova istanza. Non viene quindi avviato il nuovo demone mentre il precedente è ancora in esecuzione.

Il watcher confronta `stat -c %Y`, con risoluzione in secondi: più aggiornamenti del marker nello stesso secondo possono non essere rilevati distintamente.

Il trap `SIGTERM` richiama `delete_iptables_rules()` nel processo Bash del container OpenVPN. **Non** chiama `stop_openvpn()` e **non** termina esplicitamente il ciclo di polling. Non esiste attualmente un handler di shutdown in `app.py`.

Lo script dichiara anche `trap delete_iptables_rules SIGKILL`, ma **SIGKILL non può essere intercettato**, neppure da Bash: il sistema operativo termina immediatamente il processo senza eseguire handler o cleanup. Questa dichiarazione non rende quindi possibile la rimozione automatica delle regole in caso di arresto forzato.

## Sviluppo locale

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Servono anche `openssl` e `openvpn` installati sul sistema: l'avvio fallisce con `ToolNotInstalledException` se mancano.

Avvio con il server di sviluppo Flask (porta **5000**):

```bash
python app.py
```

Con Gunicorn, come nel container (porta **8080**):

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:8080 app:app
```

I file vengono generati nella cartella `target/` del progetto. Il rilevamento dell'interfaccia di uscita per `iptables` richiede una rotta verso Internet.

## Sicurezza

- **Le API non hanno autenticazione.** Chiunque raggiunga la porta 8080 può creare, rinnovare e revocare client e scaricare profili completi di chiave privata. Non esporre la porta su reti non fidate: mettila dietro un reverse proxy con autenticazione/TLS o limita l'accesso con un firewall.
- Il profilo scaricabile contiene la **chiave privata del client** e la chiave `tls-crypt`: trattalo come un segreto.
- `openvpn-pki/private/ca.key` permette di emettere certificati validi: proteggila e includila nei backup cifrati.
- Il container `openvpn` richiede `NET_ADMIN` e `/dev/net/tun` e usa la rete host: le modifiche `iptables` agiscono sul firewall dell'host. Il demone, dopo l'avvio, scende a `nobody:nogroup`.
- In `resource_only` la regola finale `DROP` riguarda il traffico **inoltrato** dai client attraverso `tun0`; non è una policy `INPUT` per proteggere i servizi locali dell'host e non imposta l'isolamento tra client.
- Il file `.env` può contenere dati di rete interni: non pubblicarlo.

## Risoluzione dei problemi

**`Error opening configuration file: openvpn-conf/openvpn.conf`**
Il servizio Python non ha ancora generato la configurazione o il volume è vuoto. Controlla `docker compose logs py-managed-openvpn` e verifica che sia *healthy*.

**Il client si connette ma non raggiunge le reti private**
- Controlla le route configurate nel `.env` e che il client le riceva (`PUSH_REPLY` nei log del container `openvpn`).
- Verifica le regole: `docker exec openvpn iptables -S` e `docker exec openvpn iptables -t nat -S`. In `resource_only` devono esistere `FORWARD ... -j ACCEPT` e `POSTROUTING ... -j MASQUERADE` per ogni rete.
- Verifica che il forwarding IPv4 sia attivo sull'host: `docker exec openvpn cat /proc/sys/net/ipv4/ip_forward` deve restituire `1` (OpenVPN usa la rete host).
- Verifica che l'interfaccia `-o` negli script generati esista sull'host. Viene rilevata nel container Python, che usa una rete differente: `eth0` del container Python non coincide necessariamente con l'interfaccia fisica di uscita dell'host.
- Assicurati che gli host delle reti private rispondano a pacchetti provenienti dall'host Docker (o che esista una rotta di ritorno).

**I nomi interni non si risolvono in `resource_only`**
Non viene inviato alcun DNS di default. Imposta `OPENVPN_SERVER_DNS_0_ADDRESS` con un DNS raggiungibile tramite la VPN.

**I siti Internet non si aprono con la VPN attiva**
In `resource_only` il traffico generale deve continuare a usare la rete del client. Controlla sovrapposizioni tra
subnet, route predefinita del client e l'eventuale DNS personalizzato: inviare un DNS non configura automaticamente uno
split DNS. Usa `full_tunnel` soltanto se vuoi spostare il traffico Internet IPv4 nella VPN.

**`Cannot uniquely identify the outgoing interface`**
Il rilevamento dell'interfaccia di uscita non ha trovato una sola interfaccia per l'indirizzo sorgente. Controlla la rete del container (rotta verso Internet, nessun indirizzo duplicato).

**Le modifiche al `.env` non hanno effetto**
Le variabili sono lette all'avvio: ricrea i container con `docker compose up -d --build`. Ricorda che i parametri della CA e del certificato server influiscono solo sulla prima generazione.

**Un client revocato è ancora connesso**
La revoca aggiorna `need_to_restart`; se il watcher rileva una modifica, riavvia OpenVPN al successivo controllo. Cerca `Restart requested. Restarting OpenVPN...` nei log. Aggiornamenti multipli nello stesso secondo possono essere accorpati.

**Le connessioni si interrompono durante un rinnovo**
Il refresh periodico richiede un riavvio solo quando viene segnalato un rinnovo. Se le interruzioni si ripetono a ogni esecuzione giornaliera, controlla nei log se il rinnovo continua a essere richiesto e verifica l'effettivo aggiornamento dei certificati e della CRL. Vedi [Refresh periodico della PKI](#refresh-periodico-della-pki).

**HTTP 404 su `/client/connected`**
Il file `openvpn-log/status-server.log` non è ancora disponibile nel volume. Verifica che il demone sia partito e che stia scrivendo lo stato. Un log temporaneamente incompleto può invece causare HTTP 500 nel parser.

**`WARNING: Failed to stat CRL file, not reloading CRL`**
OpenVPN scende a `nobody:nogroup`, ma deve poter attraversare le directory PKI e leggere la CRL anche dopo il cambio utente. Controlla quei permessi senza rendere pubbliche le chiavi private. Le directory create dal servizio hanno modalità `700` se non esistevano già; anche la directory `openvpn-log` può quindi impedire al demone di scrivere il file di stato.

**Comandi utili**

```bash
docker compose logs -f py-managed-openvpn
docker compose logs -f openvpn
docker exec openvpn cat /etc/openvpn-custom/openvpn-log/status-server.log
docker exec openvpn cat /etc/openvpn-custom/openvpn-conf/openvpn.conf
```

## Limiti noti

- Solo IPv4 e solo UDP sulla porta 1194 (non configurabili tramite variabili).
- L'autenticazione dei client avviene esclusivamente tramite certificato.
- Lo script `iptables.rules.delete.bash` è richiamato dal trap `SIGTERM`, ma con `network_mode: host` le regole possono restare sull'host se il trap non viene completato o il container viene terminato forzatamente. Il trap dichiarato per `SIGKILL` non può essere eseguito e non offre protezione in questo caso.
- Le regole vengono aggiunte con `iptables -A` senza controllo di esistenza: avvii ripetuti senza cleanup possono creare duplicati. Le regole non vengono riapplicate durante il solo riavvio del demone.
- L'interfaccia di uscita viene determinata nel servizio Python e usata nella rete host di OpenVPN: i nomi devono coincidere affinché le regole siano efficaci.
- La lista delle connessioni dipende dal formato testuale di stato OpenVPN v1; non gestisce esplicitamente file parziali o formati diversi.
- Le operazioni PKI non sono serializzate tra richieste e scheduler. Più worker Gunicorn avviano più scheduler.
- Diversi metodi ignorano i codici di uscita dei comandi shell: una risposta di successo non dimostra da sola che OpenSSL abbia completato l'operazione. `delete_client` non controlla la risposta della revoca prima di rimuovere i file.
- I parametri di validità dei certificati e le dimensioni delle chiavi sono fissi nel codice.
