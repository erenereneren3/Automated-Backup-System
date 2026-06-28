# Automated Backup System

A Python-based automated backup tool with scheduling, compression, logging, and Telegram notifications. Designed for reliability and ease of configuration — no code changes needed, just edit `config.json`.

---

## Features

- **ZIP compression** — each backup is a timestamped `.zip` archive (e.g. `backup_2025-06-25_14-30.zip`)
- **Multiple source folders** — back up any number of directories in one run
- **Auto-cleanup** — keeps only the last N backups; older ones are deleted automatically
- **Configurable schedule** — runs every X hours via a persistent scheduler process
- **Detailed logging** — colourised console output + persistent log file at `logs/backup.log`
- **Telegram notifications** — success and failure messages sent to your phone
- **Dry-run mode** — simulate a backup without writing any files (`--dry-run`)
- **Summary report** — files backed up, total size, and time taken printed after every run
- **Cross-platform** — works on Windows and Linux

---

## Project Structure

```
auto-backup/
├── backup.py           # Core backup logic (also runnable standalone)
├── scheduler.py        # Persistent scheduler — runs backup every N hours
├── notifier.py         # Telegram notification handler
├── config.json         # All user settings (edit this, not the code)
├── requirements.txt    # Python dependencies
├── logs/
│   ├── .gitkeep        # Keeps the folder in git
│   └── backup.log      # Generated at runtime
└── README.md
```

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/auto-backup.git
cd auto-backup
pip install -r requirements.txt
```

### 2. Configure `config.json`

Open `config.json` and fill in your paths:

```json
{
  "source_folders": [
    "C:/Users/YourName/Documents",
    "C:/Users/YourName/Projects"
  ],
  "destination_folder": "C:/Backups",
  "keep_last_n_backups": 5,
  "backup_interval_hours": 6,
  "telegram": {
    "bot_token": "",
    "chat_id": ""
  }
}
```

| Key | Description |
|-----|-------------|
| `source_folders` | List of folders to back up (absolute paths) |
| `destination_folder` | Where ZIP archives are saved |
| `keep_last_n_backups` | Number of recent backups to keep; older ones are deleted |
| `backup_interval_hours` | How often the scheduler runs a backup |
| `telegram.bot_token` | Your Telegram bot token (leave empty to disable) |
| `telegram.chat_id` | Your Telegram chat/user ID (leave empty to disable) |

---

## How to Run

### Start the scheduler (runs forever, backs up every N hours)

```bash
python scheduler.py
```

### Start the scheduler and run a backup immediately

```bash
python scheduler.py --run-now
```

### Run a single backup right now

```bash
python backup.py
```

### Dry-run — simulate without writing any files

```bash
python backup.py --dry-run
```

Stop the scheduler at any time with **Ctrl+C**.

---

## Setting Up Telegram Notifications (Step by Step)

Telegram notifications are **optional**. If `bot_token` is empty, the tool runs silently without them.

### Step 1 — Create a bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts (choose a name and username)
3. BotFather will give you a token like `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`
4. Copy that token into `config.json` → `telegram.bot_token`

### Step 2 — Get your chat ID

1. Start a conversation with your new bot (click **Start**)
2. Open this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Find `"chat":{"id": 123456789}` in the JSON response
4. Copy that number into `config.json` → `telegram.chat_id`

### Step 3 — Test

Run a single backup and check your Telegram:

```bash
python backup.py
```

You should receive a message like:

```
✅ Backup Successful

📦 File: backup_2025-06-25_14-30.zip
📁 Files backed up: 342
💾 Size: 28.50 MB
⏱ Duration: 4.2s
```

---

## Log File

All activity is logged to `logs/backup.log` in plain text, and to the console in colour:

```
2025-06-25 14:30:01 [INFO]  Automated Backup System — starting backup
2025-06-25 14:30:01 [INFO]  Sources   : ['C:/Users/user/Documents']
2025-06-25 14:30:01 [INFO]  Compressing: C:/Users/user/Documents
2025-06-25 14:30:05 [INFO]  BACKUP SUMMARY
2025-06-25 14:30:05 [INFO]    Archive  : backup_2025-06-25_14-30.zip
2025-06-25 14:30:05 [INFO]    Files    : 342
2025-06-25 14:30:05 [INFO]    Size     : 28.50 MB
2025-06-25 14:30:05 [INFO]    Duration : 4.2s
```

---

## Screenshots

> _Add screenshots of the terminal output and Telegram notifications here._

---

## Requirements

- Python 3.10+
- See `requirements.txt` for all dependencies

---

## License

MIT — free to use and modify.
