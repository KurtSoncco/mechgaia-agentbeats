# MechGaia AgentBeats - Startup Guide

## Quick Start (TL;DR)

**Open 4 terminals:**

```bash
# Terminal 1: White Agent
uv run python main.py white

# Terminal 2: Controller  
uv run python main.py controller

# Terminal 3: Green Agent (optional)
uv run python main.py green

# Terminal 4: Cloudflare Tunnel
uv run python main.py run-ctrl
# NOTE: Use "python main.py run-ctrl" NOT "agentbeats run_ctrl"
# "agentbeats run_ctrl" is AgentBeats v2's controller (different thing!)

# Terminal 5: Health Check
uv run python check_agent_health.py
```

### Important: Command Differences

- ✅ `python main.py run-ctrl` → Starts Cloudflare tunnel (what you want)
- ❌ `agentbeats run_ctrl` → AgentBeats v2 controller (manages agents, different purpose)

---

## Architecture Overview

- **Port 9001**: Green Agent (assessment controller)
- **Port 9002**: Controller (proxies to white agent, serves at white.mechgaia.org)
- **Port 9003**: White Agent (mechanical engineering solver)
- **Cloudflare**: Routes white.mechgaia.org → localhost:9002 (controller)

## Step-by-Step Startup

### Step 1: Start White Agent (Port 9003)

**Terminal 1:**
```bash
cd /home/kurt-asus/mechgaia-agentbeats
uv run python main.py white
```

Expected output:
```
Starting white agent...
INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:9003
```

**OR use the run script:**
```bash
./run.sh
```

---

### Step 2: Start Controller (Port 9002)

**Terminal 2:**
```bash
cd /home/kurt-asus/mechgaia-agentbeats
uv run python main.py controller
```

Expected output:
```
Starting MechGaia Controller on 0.0.0.0:9002
Controller will proxy to white agent at http://localhost:9003
🚀 MechGaia Controller Starting
INFO:     Uvicorn running on http://0.0.0.0:9002
```

---

### Step 3: Start Green Agent (Port 9001) - Optional

**Terminal 3:**
```bash
cd /home/kurt-asus/mechgaia-agentbeats
uv run python main.py green
```

Expected output:
```
Starting MechGaia Green Agent...
INFO:     Uvicorn running on http://0.0.0.0:9001
```

---

### Step 4: Start Cloudflare Tunnel

**Terminal 4:**
```bash
cd /home/kurt-asus/mechgaia-agentbeats
uv run python main.py run-ctrl
```

Expected output:
```
Starting cloudflared tunnel...
Tunnel will forward:
  - https://green.mechgaia.org → http://localhost:9001
  - https://white.mechgaia.org → http://localhost:9002
```

---

## Health Checks

### Check All Agents Locally

**Terminal 5:**
```bash
cd /home/kurt-asus/mechgaia-agentbeats
uv run python check_agent_health.py
```

This will check:
- ✅ Green Agent (Local) - http://localhost:9001
- ✅ Green Agent (Public) - https://green.mechgaia.org
- ✅ White Agent (Local) - http://localhost:9003
- ✅ Controller (Local) - http://localhost:9002
- ✅ Controller (Public) - https://white.mechgaia.org
- ✅ Cloudflare Communication Test

---

### Manual Health Checks

#### Check White Agent (Port 9003)
```bash
curl http://localhost:9003/health
```
Expected: `{"status":"healthy","ready":true}`

#### Check Controller (Port 9002)
```bash
curl http://localhost:9002/health
```
Expected: `{"status":"healthy","ready":true}`

#### Check Controller Info
```bash
curl http://localhost:9002/info | python3 -m json.tool
```
Expected:
```json
{
    "agent_id": "af71be80-9702-43c2-b9f8-d95dda16e63a",
    "name": "MechGaia White Agent",
    "type": "assessee",
    "status": "healthy",
    "url": "https://white.mechgaia.org",
    "version": "0.1.0"
}
```

#### Check Agent Card (Controller)
```bash
curl http://localhost:9002/.well-known/agent-card.json | python3 -m json.tool
```
Expected: Full agent card JSON without `managedAgents` field

#### Check Agent Card via Cloudflare
```bash
curl https://white.mechgaia.org/.well-known/agent-card.json | python3 -m json.tool
```

---

### Test Message Sending

#### Test Controller → White Agent (Local)
```bash
curl -X POST http://localhost:9002/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test","method":"messages/send","params":{"message":{"role":"user","parts":[{"kind":"text","text":"Calculate beam deflection for 2m span, 100kN load"}]}}}' \
  | python3 -m json.tool
```

#### Test via Cloudflare
```bash
curl -X POST https://white.mechgaia.org/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test","method":"messages/send","params":{"message":{"role":"user","parts":[{"kind":"text","text":"Test message"}]}}}' \
  | python3 -m json.tool
```

---

## Quick Verification Checklist

- [ ] White agent running on port 9003
- [ ] Controller running on port 9002
- [ ] Green agent running on port 9001 (optional)
- [ ] Cloudflare tunnel running
- [ ] All health checks pass
- [ ] Agent card accessible locally
- [ ] Agent card accessible via Cloudflare
- [ ] Controller `/info` shows `"type": "assessee"`
- [ ] Messages can be sent through controller

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :9002
lsof -i :9003

# Kill process if needed
kill <PID>
```

### Controller Can't Connect to White Agent
- Verify white agent is running: `curl http://localhost:9003/health`
- Check controller logs for connection errors

### Agent Card Not Available
- Restart controller after code changes
- Verify white agent is running (controller proxies to it)
- Check controller logs for errors

### Cloudflare Not Working
- Verify tunnel is running: `ps aux | grep cloudflared`
- Check tunnel logs for errors
- Verify DNS is pointing to Cloudflare

---

## Stop All Services

Press `Ctrl+C` in each terminal, or:

```bash
# Kill all Python processes (be careful!)
pkill -f "python.*main.py"
pkill -f "uvicorn"

# Kill cloudflared
pkill -f cloudflared
```

---

## AgentBeats v2 Registration

When registering in AgentBeats v2:
- **Controller URL**: `https://white.mechgaia.org`
- The controller will proxy all requests to the white agent
- AgentBeats should NOT try to start agents - it should connect to the controller directly

### AgentBeats Controller Configuration

**Important**: `agentbeats run_ctrl` runs locally on port 8010, but it needs to connect to your controller via the public domain.

**Cloudflare is already configured correctly** - no need to register anything in Cloudflare. The tunnel routes:
- `https://white.mechgaia.org` → `http://localhost:9002` (your controller)

**How AgentBeats Controller Works:**
1. `agentbeats run_ctrl` runs locally on port 8010 (AgentBeats' own controller)
2. This controller needs to be configured to connect to `https://white.mechgaia.org` (your controller)
3. Configuration happens when you **register/add a controller in AgentBeats UI**, not in Cloudflare

**To configure AgentBeats controller:**
1. Start your controller: `uv run python main.py controller` (runs on port 9002)
2. Start Cloudflare tunnel: `uv run python main.py run-ctrl`
3. In AgentBeats UI/registration, set Controller URL to: `https://white.mechgaia.org`
4. AgentBeats controller will then check: `https://white.mechgaia.org/info`
5. Verify it works: `curl https://white.mechgaia.org/info` should return controller info

**Note**: You don't need to register anything in Cloudflare - Cloudflare is just a tunnel/proxy. The configuration happens in AgentBeats when you register the controller URL.

### Port Conflict Issue

If you see `ERROR: [Errno 98] address already in use`:
- This means AgentBeats is trying to start the white agent, but it's already running
- **Solution**: Don't let AgentBeats manage agent lifecycle - start agents manually:
  ```bash
  # Start white agent manually (Terminal 1)
  uv run python main.py white
  
  # Start controller manually (Terminal 2)  
  uv run python main.py controller
  
  # Then AgentBeats controller can connect to https://white.mechgaia.org
  ```

