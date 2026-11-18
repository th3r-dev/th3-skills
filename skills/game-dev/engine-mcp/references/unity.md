# Unity: MCP
Checked 2026-11-18. Recheck the server's README before trusting a version or a tool name.

## Pick
| Server | Official | License | Engine versions | Transport | Use when |
|---|---|---|---|---|---|
| Unity AI Assistant "Unity MCP" (`com.unity.ai.assistant`) | yes | Unity package (terms: UNVERIFIED) | Unity 6 (6000.0)+ | stdio to a relay, then pipe/socket to the Editor; no network port | default; the person has the package and an AI-tools trial or subscription |
| MCP for Unity (CoplayDev/unity-mcp) | no | MIT | 2021.3 LTS to 6.x | stdio or HTTP (`127.0.0.1:8080/mcp`) | no Unity AI subscription, or Unity older than 6 |
| AI Game Developer (IvanMurzak/Unity-MCP) | no | Apache-2.0 | 2022.3+ | outbound to a cloud relay, or a local server (stdio) | the person wants runtime (in-game) tools |

Avoid: emeryporter/UnityMCP (GPL-3.0, 11 stars). CoderGamester/mcp-unity (MIT, last push 2026-10-11) was not evaluated: UNVERIFIED. `justinpbarnett/unity-mcp` is the old name of CoplayDev/unity-mcp.

## Default: Unity MCP (official)
Status: open beta (docs show 2.6.0-pre.1). Behavior and availability can change.

### Editor side (the person does this)
1. Unity 6 (6000.0)+, project connected to Unity Cloud, `com.unity.ai.assistant` installed, an active trial or subscription to Unity's AI tools beta. Whether MCP use spends points is UNVERIFIED (the blog says no credits, the 2.6 docs mention a points balance).
2. Edit > Project Settings > AI > Unity MCP: **Unity Bridge** must read Running. Select Start if Stopped. It starts with the Editor.
3. The Editor installs the relay to `~/.unity/relay/` on startup.
4. After the agent first connects: same page, Pending Connections, review, **Accept**. No tool runs before that. Approved clients reconnect on their own.

### Wire the agent
```bash
python scripts/engine_mcp.py config --engine unity --client claude --root <project>
```
Writes server `unity-mcp`. The script picks the relay for the host and expands `~` (the docs warn clients may not):

| Host | command |
|---|---|
| macOS arm64 | `~/.unity/relay/relay_mac_arm64.app/Contents/MacOS/relay_mac_arm64` |
| macOS Intel | `~/.unity/relay/relay_mac_x64.app/Contents/MacOS/relay_mac_x64` |
| Windows | `%USERPROFILE%\.unity\relay\relay_win.exe` |
| Linux | `~/.unity/relay/relay_linux` |

```json
{ "mcpServers": { "unity-mcp": {
  "command": "/Users/<you>/.unity/relay/relay_mac_arm64.app/Contents/MacOS/relay_mac_arm64",
  "args": ["--mcp"],
  "env": { "UNITY_PROJECT_PATH": "/abs/path/to/Project" } } } }
```
- `--mcp` is required, or the relay is not an MCP server.
- Without `UNITY_PROJECT_PATH` (or `--project-path`) the relay takes the first Editor it finds. `--instance-id` / `UNITY_INSTANCE_ID` targets by Editor PID. An argument beats an env var.
- The file now holds an absolute user path. Keep it out of git, or register at user scope: `claude mcp add --scope user ...`.
- The Unity docs also offer auto-configure for listed clients (Integrations section of the Unity MCP page).

### Tools
Seen in the docs: `Unity_ManageScene`, `Unity_ManageGameObject`, `Unity_ReadConsole`. The docs describe scene, asset, script and console tools, GameObject inspection and build settings, and give no full list. Anything else: call tools/list on a live Editor. Custom tools register by attribute, interface or runtime API and are found at Editor start.

### Run-and-look loop
| Step | Tool |
|---|---|
| Check connection | the client is listed under Connected Clients in the settings page; then tools/list |
| Enter play mode | UNVERIFIED: call tools/list, look for a play/editor-state tool |
| Input | UNVERIFIED: no input tool documented |
| Read logs | `Unity_ReadConsole` |
| Screenshot | UNVERIFIED: call tools/list |
| Stop | UNVERIFIED: same tool as enter play |
| Tests | UNVERIFIED: call tools/list |

A step that cannot run is NOT ASSESSED, not a pass. If play, screenshot and tests are all absent, say so and offer the CoplayDev server below.

### Security
- Direct clients need approval; connections from Assistant through AI Gateway are approved automatically.
- Several clients can share one Editor at once.
- Pipe/socket only, no TCP port. Telemetry: UNVERIFIED.
- Script-editing tools run with Editor rights. Anything beyond scene and console is arbitrary code to check: UNVERIFIED.

## Alternates

### MCP for Unity (CoplayDev/unity-mcp)
MIT, 16,038 stars, pushed 2026-11-17, release v10.3.0 (2026-10-04). Python 3.10+ via `uv`. The script does NOT write this entry.
- **Install** (Package Manager > Add package from git URL), pinned to a tag, not `#main`:
  `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.3.0`
- **Configure:** Window > MCP for Unity > Configure All Detected Clients. Use it over a hand-written entry; the README gives no JSON.
- Server defaults (from source): HTTP `http://127.0.0.1:8080`, path `/mcp`, env `UNITY_MCP_HTTP_PORT`; the Unity plugin reaches the Python server over WebSocket `/hub/plugin`. The hand entry `{ "type": "http", "url": "http://127.0.0.1:8080/mcp" }` is inferred from these: UNVERIFIED.
- **Telemetry:** the source has an opt-out. Set `DISABLE_TELEMETRY` or `UNITY_MCP_DISABLE_TELEMETRY` to `1` in the server's env. The docs site says "no telemetry by default"; the source disagrees in form. Set it anyway.
- **Loop tools** (50 tools; full list in the catalog):

| Step | Tool |
|---|---|
| Enter play | `manage_editor`, action `play` |
| Pause / stop | `manage_editor`, actions `pause`, `stop` |
| Logs | `read_console` |
| Screenshot | `manage_camera` (screenshot options in source; exact args: call tools/list) |
| Tests | `run_tests` (returns a job id), poll `get_test_job` |
| Compile | `refresh_unity`, `validate_script` |
| Input | UNVERIFIED |

- **Security:** HTTP Local binds loopback only; a LAN bind needs an opt-in. Remote HTTP requires https. `execute_code` runs arbitrary C# in the Editor and `execute_menu_item` runs menu items: ask first. `asset_gen` tools need fal.ai, OpenRouter, Tripo or Meshy keys; leave them off.

### AI Game Developer (IvanMurzak/Unity-MCP)
Apache-2.0, 4,657 stars, pushed 2026-11-18, release 1.12.0. Unity 2022.3+; CI on 2022.3, 6000.0, 6000.3, 6000.6.
- **Install:** download `AI-Game-Dev-Installer.unitypackage` from the releases page and import it, or OpenUPM `com.ivanmurzak.unity.mcp` (scoped registry `https://package.openupm.com`, scopes `com.ivanmurzak`, `extensions.unity`). Pin the version.
- **Configure:** Window > AI Game Dev, set connection **Custom** (local, no account), then Configure for the agent. Default is **Cloud** (sign in to ai-game.dev): pick Custom for private projects.
- **Local entry** (from the README; `<port>` is shown in the window):
```json
{ "mcpServers": { "ai-game-developer": {
  "command": "<project>/Library/mcp-server/osx-arm64/gamedev-mcp-server",
  "args": ["port=<port>", "client-transport=stdio"] } } }
```
- **Loop tools:** `rql-query` (scene, console, Editor state), `rql-mutate`, `script-execute` (C#), `tests-run`, `screenshot-isolated`, `unity-tool-list`. Play mode and input tools: UNVERIFIED; call tools/list.
- **Security:** local auth defaults to `none`: any local process reaching the port can call tools. Set **Authorization Token** to `token`, then Configure again. The token goes in the client config: keep that file out of git. Cloud relay records MCP event metadata for 90 days. `script-execute` is arbitrary C#.

## Sources
- https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.6/manual/integration/unity-mcp-get-started.html
- https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.6/manual/integration/unity-mcp-overview.html
- https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.6/manual/index.html
- https://unity.com/en/blog/unity-ai-mcp-how-to-get-started
- https://github.com/CoplayDev/unity-mcp (README, SECURITY.md, `Server/src/main.py`, `Server/src/core/telemetry.py`, `Server/src/services/tools/manage_editor.py`)
- https://coplaydev.github.io/unity-mcp/ and https://coplaydev.github.io/unity-mcp/reference/tools
- https://github.com/IvanMurzak/Unity-MCP
