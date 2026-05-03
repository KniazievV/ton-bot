# Deploy to Oracle Cloud Free (24/7)

This guide runs your Telegram bot on an Oracle Cloud Always Free VM and keeps token private.

## Why this option
- Always Free VM can run continuously (good for bots with polling).
- You store token on server in `.env`, not in git.

## 1) Create VM (Ubuntu)
- Oracle Cloud -> Compute -> Instances -> Create instance.
- Image: Ubuntu 22.04 (or newer).
- Shape: `VM.Standard.E2.1.Micro` (Always Free).
- Add your SSH key.
- Create instance and copy public IP.

## 2) Connect by SSH
```bash
ssh ubuntu@YOUR_PUBLIC_IP
```

## 3) Install Docker + Compose plugin
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

## 4) Clone project and create server `.env`
```bash
git clone YOUR_REPO_URL botton
cd botton
cp .env.example .env
```

Edit `.env`:
```bash
nano .env
```

Set values:
- `TELEGRAM_BOT_TOKEN=...` (real token from BotFather)
- `TONCENTER_API_KEY=...` (optional)
- `POLL_INTERVAL_SEC=45` (optional)

Save file and exit.

## 5) Start bot
```bash
docker compose -f docker-compose.oracle.yml up -d --build
```

Check logs:
```bash
docker compose -f docker-compose.oracle.yml logs -f
```

## 6) Update bot later
```bash
cd botton
git pull
docker compose -f docker-compose.oracle.yml up -d --build
```

## Security checklist (important)
- Keep repository private if possible.
- Never commit `.env` (already ignored).
- If token was shown publicly before, revoke and issue new token in BotFather.
- In Oracle VCN security list, keep only needed inbound ports (SSH 22 for admin). Bot polling does not need inbound HTTP port.

## If container is not running
```bash
docker compose -f docker-compose.oracle.yml ps
docker compose -f docker-compose.oracle.yml logs --tail=200
```
