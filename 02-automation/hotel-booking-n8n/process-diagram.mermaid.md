# Схема процесса (Mermaid)

Ниже две схемы: обработка заявки (Webhook) и ежедневный отчёт (Cron 18:00).  
Можно вставить в любой markdown-редактор, поддерживающий Mermaid, или использовать как основу для схемы в draw.io/ProcessOn.

---

## A) Обработка заявки (Tally → Webhook → Supabase → Gmail)

```mermaid
flowchart TD
  Client[Client] --> TallyForm[TallyForm]
  TallyForm --> Webhook[Webhook_n8n]

  Webhook --> Validate[ValidateAndNormalize]
  Validate -->|invalid| Invalid[InvalidInput]
  Invalid --> NotifyMgrErr[NotifyManagerOptional]
  Invalid --> EndInvalid[End]

  Validate --> RequestId[BuildRequestId]
  RequestId --> DedupeCheck[DedupeCheck_bookings]
  DedupeCheck -->|duplicate| EndDup[End_NoChanges]

  DedupeCheck --> SearchRooms[SearchRooms_free_matchingDates]
  SearchRooms -->|none| NoRoom[NoRoomFound]
  NoRoom --> EmailClientNo[EmailClient_NoRoom]
  NoRoom --> EndNoRoom[End]

  SearchRooms -->|found| Reserve[ConditionalReserveRoom]
  Reserve -->|reserveFailed| NoRoom2[TreatAsNoRoomOrTryNext]
  NoRoom2 --> EmailClientNo2[EmailClient_NoRoom]
  NoRoom2 --> EndNoRoom2[End]

  Reserve --> CreateBooking[InsertBooking_reserved_pending]
  CreateBooking --> EmailClientYes[EmailClient_Confirmation]
  EmailClientYes --> NotifyMgrNew[NotifyManagerOptional_NewBooking]
  NotifyMgrNew --> EndOk[End]
```

---

## B) Ежедневный отчёт (Cron 18:00 → Supabase → Gmail)

```mermaid
flowchart TD
  Cron[Cron_18_00] --> NewBookings[SelectNewBookings_24h]
  Cron --> PendingBookings[SelectPendingBookings]
  Cron --> ReservedRooms[SelectReservedRooms]
  NewBookings --> Compose[ComposeEmailReport]
  PendingBookings --> Compose
  ReservedRooms --> Compose
  Compose --> EmailMgr[EmailManager_dir_kalugin]
  EmailMgr --> End[End]
```

---

## Как быстро перенести в сервис схем
- **draw.io**: вставьте как референс и соберите блоки вручную (обычно 5–10 минут).
- **ProcessOn**: аналогично; используйте 2 дорожки (заявка и ежедневный отчёт).

