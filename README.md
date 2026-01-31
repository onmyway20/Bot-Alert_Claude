# Bot-Alert
by Claude Vibe Coding

# 📢 Upbit & Bithumb Listing Alert Bot v2.0
## Panduan Lengkap Instalasi

Bot untuk monitoring listing baru di **Upbit** dan **Bithumb** dengan notifikasi real-time ke Telegram.

---

## 📋 Daftar Isi

1. [Fitur Bot](#1-fitur-bot)
2. [Daftar VPS Gratis](#2-daftar-vps-gratis)
3. [Setup Telegram Bot](#3-setup-telegram-bot)
4. [Koneksi ke VPS](#4-koneksi-ke-vps)
5. [Instalasi Bot](#5-instalasi-bot)
6. [Konfigurasi Auto-Start](#6-konfigurasi-auto-start-systemd)
7. [Perintah Berguna](#7-perintah-berguna)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Fitur Bot

| Exchange | Metode Deteksi |
|----------|----------------|
| **Upbit** | Notice API + Market API |
| **Bithumb** | Ticker API |

- ✅ Notifikasi real-time ke Telegram
- ✅ Auto-restart jika crash
- ✅ Logging untuk debugging
- ✅ Interval check yang bisa dikustomisasi

---

## 2. Daftar VPS Gratis

### Opsi A: Oracle Cloud (RECOMMENDED - Gratis Selamanya)

**Spesifikasi Always Free:**
- 2 VM AMD (1/8 OCPU, 1GB RAM) atau
- 1 VM ARM (4 OCPU, 24GB RAM)
- 200GB storage
- 10TB bandwidth/bulan

**Langkah Pendaftaran:**

1. Buka https://www.oracle.com/cloud/free/
2. Klik **"Start for free"**
3. Isi formulir:
   - Email aktif
   - Country: Indonesia
   - Name: Sesuai kartu
4. Verifikasi email
5. Buat password
6. **Pilih Home Region: Singapore atau Japan** (penting untuk latency)
7. Masukkan kartu kredit/debit (hanya verifikasi, tidak dicharge)
8. Tunggu ~1 jam untuk aktivasi

**Buat VM Instance:**

1. Login ke https://cloud.oracle.com
2. Klik **"Create a VM instance"**
3. Konfigurasi:
   - Name: `listing-bot`
   - Image: **Ubuntu 22.04** atau **24.04**
   - Shape: **VM.Standard.E2.1.Micro** (Always Free)
4. Di bagian **"Add SSH keys"**: Download SSH key (simpan!)
5. Klik **Create**
6. Tunggu status **RUNNING**
7. Catat **Public IP Address**

**Buka Port di Security List:**

1. Klik VM instance > Virtual Cloud Network
2. Security Lists > Default Security List
3. Add Ingress Rules:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port: `22`

---

### Opsi B: Google Cloud Platform

**Free Tier:**
- 1 e2-micro VM (US regions only)
- $300 credit untuk 90 hari

**Langkah:**

1. Buka https://cloud.google.com/free
2. Login dengan Google Account
3. Isi data & verifikasi kartu
4. Compute Engine > VM Instances > Create
   - Name: `listing-bot`
   - Region: `us-west1` atau `us-central1`
   - Machine type: `e2-micro`
   - Boot disk: Ubuntu 22.04
5. Klik Create & catat External IP

---

## 3. Setup Telegram Bot

### 3.1 Buat Bot di BotFather

1. Buka Telegram, cari **@BotFather**
2. Kirim: `/newbot`
3. Masukkan nama: `Listing Alert Bot`
4. Masukkan username: `mylistingalert_bot` (harus unik)
5. **SIMPAN TOKEN** yang diberikan:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### 3.2 Dapatkan Chat ID

**Untuk Personal Chat:**

1. Cari dan Start bot kamu di Telegram
2. Kirim pesan apa saja (misal: "test")
3. Buka browser:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   Ganti `<TOKEN>` dengan token bot kamu
4. Cari `"chat":{"id":` - angka itu adalah Chat ID

**Untuk Group:**

1. Tambahkan bot ke group
2. Kirim pesan di group
3. Buka URL getUpdates di atas
4. Chat ID group biasanya negatif: `-1001234567890`

### 3.3 Test Bot

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
     -d "chat_id=<CHAT_ID>" \
     -d "text=Test dari Listing Bot!"
```

---

## 4. Koneksi ke VPS

### Dari Linux/Mac:

```bash
# Ganti dengan path SSH key dan IP VPS kamu
ssh -i ~/path/to/ssh-key.key ubuntu@YOUR_VPS_IP
```

### Dari Windows:

1. Download [PuTTY](https://www.putty.org/)
2. Convert SSH key ke .ppk menggunakan PuTTYgen
3. Masukkan IP di PuTTY, load key di Connection > SSH > Auth
4. Klik Open

---

## 5. Instalasi Bot

Jalankan semua command ini di VPS:

### 5.1 Update Sistem & Install Python

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv
```

### 5.2 Buat Folder Project

```bash
mkdir -p ~/listing_alert_bot
cd ~/listing_alert_bot
```

### 5.3 Buat Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

### 5.4 Buat File Script

```bash
nano listing_alert.py
```

**Paste seluruh kode dari file `listing_alert.py` yang disediakan.**

Tekan `Ctrl+X`, `Y`, `Enter` untuk save.

### 5.5 Test Manual

```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python3 listing_alert.py
```

Jika berhasil, akan muncul:
```
Listing Alert Bot v2.0 Started
```

Dan kamu akan menerima pesan di Telegram.

Tekan `Ctrl+C` untuk stop.

---

## 6. Konfigurasi Auto-Start (Systemd)

### 6.1 Buat Service File

```bash
sudo nano /etc/systemd/system/listing_alert.service
```

**Paste konfigurasi ini (GANTI nilai yang ditandai):**

```ini
[Unit]
Description=Listing Alert Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/listing_alert_bot
Environment="TELEGRAM_BOT_TOKEN=GANTI_DENGAN_TOKEN_KAMU"
Environment="TELEGRAM_CHAT_ID=GANTI_DENGAN_CHAT_ID_KAMU"
Environment="CHECK_INTERVAL=30"
ExecStart=/home/ubuntu/listing_alert_bot/venv/bin/python3 /home/ubuntu/listing_alert_bot/listing_alert.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**⚠️ PENTING - Sesuaikan:**
- Ganti `ubuntu` dengan username VPS kamu (cek dengan `whoami`)
- Ganti `TELEGRAM_BOT_TOKEN` dengan token dari BotFather
- Ganti `TELEGRAM_CHAT_ID` dengan chat ID kamu
- Ganti path `/home/ubuntu/` jika username berbeda

Tekan `Ctrl+X`, `Y`, `Enter` untuk save.

### 6.2 Aktifkan Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start saat boot
sudo systemctl enable listing_alert

# Start bot
sudo systemctl start listing_alert

# Cek status
sudo systemctl status listing_alert
```

Jika berhasil, akan muncul:
```
● listing_alert.service - Listing Alert Bot
     Loaded: loaded
     Active: active (running)
```

---

## 7. Perintah Berguna

### Manajemen Bot

```bash
# Cek status
sudo systemctl status listing_alert

# Start bot
sudo systemctl start listing_alert

# Stop bot
sudo systemctl stop listing_alert

# Restart bot
sudo systemctl restart listing_alert

# Disable auto-start
sudo systemctl disable listing_alert
```

### Lihat Log

```bash
# Log dari systemd
sudo journalctl -u listing_alert -f

# Log dari file bot
tail -f ~/listing_alert_bot/listing_alert.log

# Lihat 50 baris terakhir
tail -50 ~/listing_alert_bot/listing_alert.log
```

### Edit Konfigurasi

```bash
# Edit script bot
nano ~/listing_alert_bot/listing_alert.py

# Edit service file
sudo nano /etc/systemd/system/listing_alert.service

# Setelah edit service, reload:
sudo systemctl daemon-reload
sudo systemctl restart listing_alert
```

---

## 8. Troubleshooting

### Error: Unit listing_alert.service not found
Service file belum dibuat. Ikuti langkah 6.1.

### Error: status=217/USER
Username di service file salah. Cek dengan `whoami` dan sesuaikan.

### Error: status=200/CHDIR
Path folder salah. Cek lokasi folder:
```bash
ls -la ~/listing_alert_bot/
```

### Error: status=1/FAILURE
Cek error detail:
```bash
sudo journalctl -u listing_alert -n 30 --no-pager
```

### Error: SyntaxError invalid character
File script rusak saat copy-paste. Buat ulang file dengan `nano`.

### Error: ModuleNotFoundError requests
Pastikan ExecStart menggunakan Python dari venv:
```
ExecStart=/home/ubuntu/listing_alert_bot/venv/bin/python3 ...
```

### Bot jalan tapi tidak kirim Telegram
1. Cek token dan chat_id benar
2. Test manual:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
        -d "chat_id=<CHAT_ID>" \
        -d "text=Test"
   ```

### Bithumb/Upbit API error
Cek koneksi:
```bash
curl -I https://api.bithumb.com/public/ticker/ALL_KRW
curl -I https://api.upbit.com/v1/market/all
```

---

## 📁 File yang Diperlukan

1. **listing_alert.py** - Script utama bot
2. **listing_alert.service** - Systemd service file

---

## ⚠️ Disclaimer

Bot ini untuk tujuan edukasi. Trading cryptocurrency memiliki risiko tinggi. DYOR (Do Your Own Research)!

---

## 📞 Support

Jika ada masalah, cek:
1. Log error dengan `journalctl`
2. Pastikan semua path dan username sudah benar
3. Test manual dulu sebelum setup systemd
