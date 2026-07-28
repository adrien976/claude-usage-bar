# -*- coding: utf-8 -*-
"""Claude Usage Bar - version Windows (zone de notification).
Affiche les limites d'utilisation Claude dans le system tray.
BETA : portage du plugin macOS, memes endpoints OAuth + usage.
"""
import base64, hashlib, json, os, secrets, sys, threading, time
import urllib.request, urllib.error, urllib.parse
import webbrowser

try:
    import keyring
    from PIL import Image, ImageDraw, ImageFont
    import pystray
except ImportError:
    sys.stderr.write("Dependances manquantes : pip install pystray Pillow keyring\n")
    raise

SERVICE = "ClaudeUsageBar"
ACCOUNT = "credentials"
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
AUTH_URL = "https://claude.ai/oauth/authorize"
REDIRECT = "https://platform.claude.com/oauth/code/callback"
HDRS = {"anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "claude-cli/2.0.14 (external, cli)"}

GREEN, ORANGE, RED = (52, 199, 89), (255, 167, 34), (255, 95, 87)
C_SESSION, C_WEEK = (79, 168, 255), (48, 213, 200)
C_SCOPED = [(191, 90, 242), (255, 107, 157), (255, 214, 10)]


# ---------- Stockage du jeton (Gestionnaire d'identifiants Windows) ----------
def get_creds():
    raw = keyring.get_password(SERVICE, ACCOUNT)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def save_creds(c):
    keyring.set_password(SERVICE, ACCOUNT, json.dumps(c))

# ---------- Appels HTTP ----------
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
    return http_json(USAGE_URL,
                     headers={"Authorization": "Bearer " + creds["accessToken"]},
                     timeout=20)


# ---------- Autorisation OAuth (PKCE) via fenetre de saisie ----------
def do_reauth():
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = base64.urlsafe_b64encode(secrets.token_bytes(24)).rstrip(b"=").decode()
    params = {"code": "true", "client_id": CLIENT_ID, "response_type": "code",
              "redirect_uri": REDIRECT, "scope": "user:inference user:profile",
              "code_challenge": challenge, "code_challenge_method": "S256",
              "state": state}
    webbrowser.open(AUTH_URL + "?" + urllib.parse.urlencode(params))
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    raw = simpledialog.askstring(
        "Claude Usage Bar",
        "Une page s'est ouverte dans ton navigateur.\n"
        "Clique sur Autoriser, puis colle ici le code affiche :",
        parent=root)
    if not raw:
        root.destroy()
        return False
    code = raw.strip().split("#")[0]
    body = {"grant_type": "authorization_code", "code": code,
            "redirect_uri": REDIRECT, "client_id": CLIENT_ID,
            "code_verifier": verifier, "state": state}
    try:
        tok = http_json(TOKEN_URL, body, timeout=120)
    except Exception as e:
        messagebox.showerror("Claude Usage Bar", "Echec : " + str(e))
        root.destroy()
        return False
    creds = {"accessToken": tok["access_token"],
             "refreshToken": tok.get("refresh_token"),
             "expiresAt": int(time.time() * 1000) + tok.get("expires_in", 28800) * 1000,
             "scopes": tok.get("scope", "").split()}
    save_creds(creds)
    messagebox.showinfo("Claude Usage Bar",
                        "Reconnecte ! L'icone va se mettre a jour.")
    root.destroy()
    return True


# ---------- Donnees ----------
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
        rows.append(("Session (5 h)", session, C_SESSION))
    for i, l in enumerate(scoped):
        name = (((l.get("scope") or {}).get("model") or {}).get("display_name")) or "Modele"
        rows.append(("Semaine - " + name, l, C_SCOPED[i % len(C_SCOPED)]))
    if weekly:
        rows.append(("Semaine - tous modeles", weekly, C_WEEK))
    out = []
    for label, l, col in rows:
        p = int(l.get("percent") or 0)
        if p >= 90 or l.get("severity") in ("exceeded", "error"):
            col = RED
        out.append({"label": label, "pct": p, "reset": l.get("resets_at") or "", "col": col})
    return out

def fmt_reset(iso):
    from datetime import datetime, timezone
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

def worst_color(rows):
    if not rows:
        return GREEN, 0
    w = max(rows, key=lambda r: r["pct"])
    return w["col"], w["pct"]


# ---------- Icone de la zone de notification ----------
def make_icon_image(pct, color):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, size - 2, size - 2], fill=(30, 30, 36, 255), outline=color, width=4)
    txt = str(pct)
    try:
        font = ImageFont.truetype("segoeui.ttf", 30 if pct < 100 else 24)
    except Exception:
        font = ImageFont.load_default()
    try:
        bbox = d.textbbox((0, 0), txt, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ox, oy = bbox[0], bbox[1]
    except Exception:
        tw, th, ox, oy = d.textsize(txt, font=font)[0], 20, 0, 0
    d.text(((size - tw) / 2 - ox, (size - th) / 2 - oy), txt, font=font, fill=color)
    return img

# ---------- Etat partage ----------
class State:
    def __init__(self):
        self.rows = []
        self.tooltip = "Claude Usage Bar"
        self.stale = False
        self.error = None

STATE = State()
ICON = None


# ---------- Rafraichissement ----------
def refresh(_=None):
    creds = get_creds()
    if not creds or not creds.get("refreshToken"):
        STATE.error = "Non connecte"
        STATE.rows = []
        _apply()
        return
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
        STATE.rows = build_rows(data)
        STATE.stale = False
        STATE.error = None
    except Exception as e:
        STATE.error = str(e)
        STATE.stale = True
    _apply()

def _apply():
    if ICON is None:
        return
    color, pct = worst_color(STATE.rows)
    if STATE.error and not STATE.rows:
        color, pct = RED, 0
    ICON.icon = make_icon_image(pct, color)
    parts = []
    short = {"Session (5 h)": "S", "Semaine - tous modeles": "Sem"}
    for r in STATE.rows:
        lbl = short.get(r["label"], r["label"].replace("Semaine - ", ""))
        parts.append("%s %d%%" % (lbl, r["pct"]))
    tip = " - ".join(parts) if parts else (STATE.error or "Claude Usage Bar")
    if STATE.stale:
        tip += " (cache)"
    ICON.title = "Claude Usage Bar\n" + tip
    ICON.menu = build_menu()
    ICON.update_menu()


# ---------- Menu ----------
def build_menu():
    items = [pystray.MenuItem("Limites d'utilisation Claude", None, enabled=False)]
    for r in STATE.rows:
        line = "%s : %d %%" % (r["label"], r["pct"])
        rr = fmt_reset(r["reset"])
        if rr:
            line += "  (reinit. " + rr + ")"
        items.append(pystray.MenuItem(line, None, enabled=False))
    if STATE.error:
        items.append(pystray.MenuItem("! " + STATE.error, None, enabled=False))
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Actualiser", lambda: threading.Thread(
        target=refresh, daemon=True).start()))
    items.append(pystray.MenuItem("Ouvrir la page d'utilisation",
        lambda: webbrowser.open("https://claude.ai/settings/usage")))
    items.append(pystray.MenuItem("Se reconnecter...", on_reauth))
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Quitter", on_quit))
    return pystray.Menu(*items)

def on_reauth(_=None):
    # relance ce script en mode --reauth pour eviter les conflits de threads
    import subprocess
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        exe = exe[:-10] + "pythonw.exe"
    subprocess.Popen([exe, os.path.abspath(__file__), "--reauth"])

def on_quit(_=None):
    if ICON is not None:
        ICON.stop()

def loop():
    while True:
        refresh()
        time.sleep(120)

def main():
    global ICON
    if "--reauth" in sys.argv:
        do_reauth()
        return
    if not get_creds():
        if not do_reauth():
            return
    ICON = pystray.Icon("ClaudeUsageBar", make_icon_image(0, C_WEEK),
                        "Claude Usage Bar", menu=build_menu())
    threading.Thread(target=loop, daemon=True).start()
    ICON.run()

if __name__ == "__main__":
    main()
