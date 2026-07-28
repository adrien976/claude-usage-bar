#!/bin/zsh
echo "🔑 Reconnexion Claude Usage Bar"
TMP="$(mktemp -t cub_reauth).py"
cat > "$TMP" <<'PYEOF'
import base64, hashlib, json, os, secrets, subprocess, time, urllib.request, urllib.parse, sys
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
state = base64.urlsafe_b64encode(secrets.token_bytes(24)).rstrip(b"=").decode()
params = {"code": "true", "client_id": CLIENT_ID, "response_type": "code",
          "redirect_uri": "https://platform.claude.com/oauth/code/callback",
          "scope": "user:inference user:profile",
          "code_challenge": challenge, "code_challenge_method": "S256", "state": state}
url = "https://claude.ai/oauth/authorize?" + urllib.parse.urlencode(params)
subprocess.run(["open", url])
print("")
print("Une page d'autorisation s'est ouverte dans ton navigateur.")
print("Clique sur Autoriser, puis colle ici le code affiche et appuie sur Entree :")
raw = sys.stdin.readline().strip()
code = raw.split("#")[0]
body = {"grant_type": "authorization_code", "code": code,
        "redirect_uri": "https://platform.claude.com/oauth/code/callback",
        "client_id": CLIENT_ID, "code_verifier": verifier, "state": state}
req = urllib.request.Request("https://platform.claude.com/v1/oauth/token",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json",
             "User-Agent": "claude-cli/2.0.14 (external, cli)",
             "anthropic-beta": "oauth-2025-04-20"})
tok = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
creds = {"accessToken": tok["access_token"], "refreshToken": tok.get("refresh_token"),
         "expiresAt": int(time.time() * 1000) + tok.get("expires_in", 28800) * 1000,
         "scopes": tok.get("scope", "").split()}
subprocess.run(["security", "add-generic-password", "-U",
                "-a", os.environ.get("USER", "user"),
                "-s", "ClaudeUsageBar-credentials", "-w", json.dumps(creds)], check=True)
print("✅ Reconnecte ! Le plugin se mettra a jour dans les 2 minutes.")
PYEOF
/usr/bin/python3 "$TMP"
rm -f "$TMP"
