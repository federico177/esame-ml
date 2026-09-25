# TechConf — Product Overview

## Dominio

TechConf è una piattaforma a microservizi per la gestione di conferenze tecnologiche (cloud, AI, security).
Permette a una società organizzatrice di gestire utenti, eventi, iscrizioni, feedback e notifiche.

## Scopo dei servizi

| Servizio | Scopo |
|---|---|
| **user-service** | Anagrafica utenti della piattaforma: partecipanti, speaker, organizzatori |
| **event-service** | Conferenze con ciclo di vita (draft → published → cancelled) e capienza |
| **registration-service** | Iscrizioni degli utenti agli eventi pubblicati, con controllo capienza |
| **feedback-service** *(opzionale)* | Valutazioni degli eventi da parte degli iscritti |
| **notification-service** *(opzionale)* | Notifiche singole o massive verso gli iscritti a un evento |

## Utenti principali

- **Organizzatori**: creano e pubblicano eventi
- **Partecipanti**: si iscrivono agli eventi pubblicati
- **Speaker**: tengono sessioni agli eventi

## Flusso principale

1. Un organizzatore viene registrato in user-service con `role = organizer`
2. L'organizzatore crea un evento in event-service (stato iniziale `draft`)
3. L'evento viene pubblicato (`draft → published`)
4. I partecipanti si iscrivono tramite registration-service
5. A evento concluso, i partecipanti lasciano feedback (opzionale)
6. L'organizzatore invia notifiche di ringraziamento via broadcast (opzionale)
