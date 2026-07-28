#!/usr/bin/python3
# -*- coding: utf-8 -*-
# <xbar.title>Claude Usage Bar</xbar.title>
# <xbar.version>v1.3</xbar.version>
# <xbar.desc>Consommation Claude : session 5h, Fable, semaine.</xbar.desc>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

import json, os, subprocess, time, urllib.request, urllib.error, base64
from datetime import datetime, timezone

SERVICE = "ClaudeUsageBar-credentials"
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
HDRS = {"anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "claude-cli/2.0.14 (external, cli)"}
APPDIR = os.path.expanduser("~/Library/Application Support/ClaudeUsageBar")
CACHE = os.path.join(APPDIR, "last_usage.json")
REAUTH = os.path.join(APPDIR, "reauth.command")
RENDERJS = os.path.join(APPDIR, "render.js")

RED = "ff5f57"
C_SESSION = "4fa8ff"
C_WEEK = "30d5c8"
C_SCOPED = ["bf5af2", "ff6b9d", "ffd60a", "34c759"]

def sh(args):
    return subprocess.run(args, capture_output=True, text=True)

def get_creds():
    r = sh(["security", "find-generic-password", "-s", SERVICE, "-w"])
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return None

def save_creds(c):
    sh(["security", "add-generic-password", "-U",
        "-a", os.environ.get("USER", "user"), "-s", SERVICE, "-w", json.dumps(c)])

def http_json(url, data=None, headers=None, timeout=30):
    h = dict(HDRS)
    if headers:
        h.update(headers)
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def refresh_token(creds):
    tok = http_json(TOKEN_URL, {"grant_type": "refresh_token",
                                "refresh_token": creds["refreshToken"],
                                "client_id": CLIENT_ID}, timeout=60)
    creds["accessToken"] = tok["access_token"]
    if tok.get("refresh_token"):
        creds["refreshToken"] = tok["refresh_token"]
    creds["expiresAt"] = int(time.time() * 1000) + tok.get("expires_in", 28800) * 1000
    save_creds(creds)
    return creds

def get_usage(creds):
    return http_json(USAGE_URL, headers={"Authorization": "Bearer " + creds["accessToken"]}, timeout=20)

def fmt_reset(iso):
    try:
        dt = datetime.fromisoformat(iso)
        s = (dt - datetime.now(timezone.utc)).total_seconds()
    except Exception:
        return ""
    if s <= 0:
        return "imminente"
    d, rem = divmod(int(s), 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return "dans %d j %d h" % (d, h)
    if h:
        return "dans %d h %02d min" % (h, m)
    return "dans %d min" % m

def esc(t):
    return t.replace("|", "/")

def out_error(msg):
    print(":exclamationmark.triangle.fill: Claude | sfcolor=#ff5f57")
    print("---")
    print(esc(msg) + " | color=#ff5f57")
    print("Se reconnecter… | bash=\"%s\" terminal=true refresh=true" % REAUTH)
    print("Actualiser | refresh=true")

def build_rows(data):
    limits = data.get("limits") or []
    session = next((l for l in limits if l.get("kind") == "session"), None)
    weekly = next((l for l in limits if l.get("kind") == "weekly_all"), None)
    scoped = [l for l in limits if l.get("kind") == "weekly_scoped"]
    if session is None and data.get("five_hour"):
        f = data["five_hour"]
        session = {"percent": round(f.get("utilization") or 0),
                   "resets_at": f.get("resets_at"), "severity": "normal"}
    if weekly is None and data.get("seven_day"):
        f = data["seven_day"]
        weekly = {"percent": round(f.get("utilization") or 0),
                  "resets_at": f.get("resets_at"), "severity": "normal"}
    rows = []
    if session:
        rows.append(("S", "Session (5 h)", session, C_SESSION))
    for i, l in enumerate(scoped):
        name = (((l.get("scope") or {}).get("model") or {}).get("display_name")) or "Modèle"
        rows.append((name, "Semaine — " + name, l, C_SCOPED[i % len(C_SCOPED)]))
    if weekly:
        rows.append(("Sem", "Semaine — tous modèles", weekly, C_WEEK))
    out = []
    for short, full, l, col in rows:
        p = int(l.get("percent") or 0)
        if p >= 90 or l.get("severity") in ("exceeded", "error"):
            col = RED
        out.append((short, full, p, l.get("resets_at") or "", col))
    return out

def render_images(rows):
    payload = {
        "title": [{"text": "%s %d%%" % (s, p), "color": col} for s, _, p, _, col in rows],
        "rows": [{"label": full, "pct": p, "color": col, "reset": fmt_reset(r)}
                 for _, full, p, r, col in rows],
    }
    inp = os.path.join(APPDIR, "render_input.json")
    tp = os.path.join(APPDIR, "title.png")
    pp = os.path.join(APPDIR, "panel.png")
    with open(inp, "w") as f:
        json.dump(payload, f)
    r = sh(["osascript", "-l", "JavaScript", RENDERJS, inp, tp, pp])
    if r.returncode != 0 or not os.path.exists(tp) or not os.path.exists(pp):
        return None
    def b64(p):
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return b64(tp), b64(pp)

def render_text_fallback(rows):
    parts = ["%s %d%%" % (s, p) for s, _, p, _, col in rows]
    print(" · ".join(parts) + " | size=13")
    print("---")
    for _, full, p, resets, col in rows:
        print("%s : %d %% | size=13 font=HelveticaNeue-Medium color=#%s" % (esc(full), p, col))
        r = fmt_reset(resets)
        if r:
            print("réinitialisation %s | size=11 color=gray" % r)

def render(data, stale):
    rows = build_rows(data)
    imgs = render_images(rows)
    if imgs:
        title_b64, panel_b64 = imgs
        print(("⌛ " if stale else "") + "| image=%s" % title_b64)
        print("---")
        print("| image=%s" % panel_b64)
    else:
        render_text_fallback(rows)
    extra = data.get("extra_usage") or {}
    print("Crédits d'utilisation : %s | size=11 color=gray"
          % ("activés" if extra.get("is_enabled") else "désactivés"))
    if stale:
        print("⚠️ Données en cache (API injoignable) | color=#ffa722 size=11")
    print("---")
    print("Actualiser | refresh=true")
    print("Ouvrir la page d'utilisation | href=https://claude.ai/settings/usage")
    print("Se reconnecter… | bash=\"%s\" terminal=true" % REAUTH)

def main():
    os.makedirs(APPDIR, exist_ok=True)
    creds = get_creds()
    if not creds or not creds.get("refreshToken"):
        out_error("Aucun identifiant trouvé — clique sur Se reconnecter")
        return
    data, stale, err = None, False, None
    try:
        if creds.get("expiresAt", 0) - time.time() * 1000 < 10 * 60 * 1000:
            creds = refresh_token(creds)
        try:
            data = get_usage(creds)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                creds = refresh_token(creds)
                data = get_usage(creds)
            else:
                raise
        with open(CACHE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        err = str(e)
        try:
            with open(CACHE) as f:
                data = json.load(f)
            stale = True
        except Exception:
            data = None
    if data is None:
        out_error("API injoignable : " + (err or "?"))
        return
    render(data, stale)

main()
