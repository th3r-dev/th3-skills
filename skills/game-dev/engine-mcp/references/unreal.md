# Unreal Engine: MCP
Checked 2026-11-18. Recheck the server's README before trusting a version or a tool name.

## Pick
| Server | Official | License | Engine versions | Transport | Use when |
|---|---|---|---|---|---|
| Unreal MCP (`ModelContextProtocol` plugin) | yes, experimental | engine (Epic EULA) | UE 5.8+ | Streamable HTTP and SSE, `127.0.0.1:8000/mcp` | default, on 5.8 or later |
| EngineWire (ChiR24/Unreal_mcp) | no | MIT | UE 5.0 to 5.8 | Streamable HTTP `127.0.0.1:3000/mcp`, or an npx stdio proxy | UE 5.7 or older, or the official plugin is too thin |
| UE-MCP (db-lyon/ue-mcp) | no | MIT | UE 5.4 to 5.9 (Windows); 5.6+ macOS and Linux | via its own bridge plugin | the person wants flows, write guards and many actions |

Avoid (stale or unlicensed): chongdashu/unreal-mcp (last commit 2025-04-22), runreal/unreal-mcp (2025-06-06), flopperam/unreal-engine-mcp (handed to Aura; no license shown). No official MCP before 5.8: Epic's 5.7 AI Assistant is a separate feature.

## Default: Unreal MCP (official, UE 5.8+)
Status: Experimental. 5.8.1 carries an MCP bug fix.

### Editor side (the person does this)
1. Edit > Plugins: "Unreal MCP" on (default), then "All Toolsets" or the individual toolset plugins. Restart when asked. A forum user reports nothing works until the toolset registries are enabled.
2. Edit > Editor Preferences > Agentic Workflows > Model Context Protocol: **Auto Start Server** on. Port (8000) and path (`/mcp`) are set there.
3. If the server is not up: console command `ModelContextProtocol.StartServer` (from a third-party README: UNVERIFIED against Epic's docs).

### Wire the agent
```bash
python scripts/engine_mcp.py config --engine unreal --client claude --root <project>
```
Writes server `unreal-mcp`:
```json
{ "mcpServers": { "unreal-mcp": { "type": "http", "url": "http://127.0.0.1:8000/mcp" } } }
```
- HTTP and SSE only: no stdio, no WebSocket.
- The editor can write this itself: console `ModelContextProtocol.GenerateClientConfig <Client>`. Epic's docs name Claude Code, Codex, Cursor, Gemini CLI and VS Code with Copilot. Codex: `codex mcp add unreal-mcp --url http://127.0.0.1:8000/mcp`.
- The file has no secret, so it can be committed. The server must be running first, or the client reports a failed connection.

### Tools
Tool search is on by default and exposes four meta-tools:

| Tool | Does |
|---|---|
| `list_toolsets` | list registered toolsets |
| `describe_toolsets` | describe toolsets |
| `describe_tools` | describe tools in a toolset |
| `call_tool` | run one tool by name |

Toolset areas in the docs: actors, Blueprints, Widget Blueprints, materials, MetaSounds, PCG, Niagara, Sequencer, Slate inspection, profiling, automation tests; runtime-callable NavMesh, Scene Capture, Console, Widget Finder, Perf, Input. Individual tool names are not in the docs: call `list_toolsets`, then `describe_tools`. Cooked builds expose only tools marked `AIRuntimeCallable`.

### Run-and-look loop
| Step | Tool |
|---|---|
| Discover | `list_toolsets`, `describe_toolsets`, `describe_tools` |
| Enter play (PIE) | UNVERIFIED: no named tool; look in the Console and automation toolsets |
| Input | UNVERIFIED: the docs name an Input toolset; call `describe_tools` on it |
| Read logs | UNVERIFIED: the docs name a Console toolset; call `describe_tools` on it |
| Screenshot | UNVERIFIED: the docs name a Scene Capture toolset; call `describe_tools` on it |
| Stop | UNVERIFIED |
| Tests | UNVERIFIED: the docs name automation tests; call `describe_tools` on it |

A step that cannot run is NOT ASSESSED, not a pass. A third-party blog (not Epic) calls closed-loop read-back "limited this release": UNVERIFIED.

### Security
- Loopback only, **no authentication**. Not designed for remote use: do not bind it to a LAN.
- Rejects an `Origin` header not on the allow-list (localhost, 127.0.0.1, [::1]). Each origin added widens exposure.
- Tool calls run one at a time on the game thread. The editor freezes while a slow call runs.
- Python toolsets run code through `init_unreal.py`; treat any Python-running tool as arbitrary code.
- Epic says defenses will harden over time. No account, API key or telemetry mentioned in the docs.

## Alternates

### EngineWire (ChiR24/Unreal_mcp)
MIT, 1,045 stars, pushed 2026-11-16, release v0.6.0 (2026-10-27). UE 5.0 to 5.8. Installing from a source clone needs a C++ project; Fab needs no compiler. The script does NOT write this entry.
- **Install:** get EngineWire from Fab (Library > Install to Engine), or `EngineWire-plugin-<version>.zip` from the releases page into `<Project>/Plugins/EngineWire/`. Enable in Edit > Plugins and restart. The status bar then reads `MCP :3000 (0)`. If it reads `MCP off` (the Fab 0.6.0 build ships with the server off), enable Native MCP Server in Project Settings > Plugins > EngineWire and restart.
- **Token:** `<Project>/Saved/MCP/capability-token`. Treat it like a password. Never write it into a committed file; keep it in an env var.
- **Config A, HTTP** (header value comes from the environment):
```json
{ "mcpServers": { "unreal-engine": { "type": "http", "url": "http://127.0.0.1:3000/mcp",
  "headers": { "X-MCP-Capability-Token": "${UNREAL_MCP_TOKEN}" } } } }
```
  Cursor takes the same `url` and `headers` without `type`.
- **Config B, stdio proxy** (Node 20.19+; survives editor restarts; pin the version):
```json
{ "mcpServers": { "unreal-engine": { "command": "npx", "args": ["-y", "unreal-engine-mcp-server@0.6.0"],
  "env": { "UE_PROJECT_PATH": "/abs/path/to/YourProject" } } } }
```
  The proxy reads the token from the project. Use the 0.6 plugin with it; a 0.5.x plugin serves 23 separate tools instead. The plugin version and the npm version must match.
- **Tools:** one gateway tool, `unreal`, with 450+ actions found by plain-word search. Action names: see the generated Action Reference in the repo, or call tools/list.
- **Loop** (README claims, action names UNVERIFIED): run PIE with synthetic input, screenshots the model can see, read logs, run Python, package builds. Ask the `unreal` tool for each; confirm by what it returns.
- **Security:** everything on 127.0.0.1 and gated by the capability token. Python execution is arbitrary code in the editor.

### UE-MCP (db-lyon/ue-mcp)
MIT, 508 stars, pushed 2026-11-17, release v1.4.14. Needs Node 20+.
- **Install:** the README's path is `npx ue-mcp init` with no version, which is unpinned. Pin a version before running it: UNVERIFIED which versions are safe, so read its releases page first. `init` also writes the client config, so read what it writes. The bridge plugin compiles in the project (C++ toolchain) or comes as prebuilt binaries.
- **Config:** written by `init`; JSON not read: UNVERIFIED.
- **Loop tools:** the README says it covers builds and PIE, and a first call `project(action="get_status")` confirms the connection. Other tool names: call tools/list.
- **Security:** write guards can block or confirm changes. Mechanism and auth: UNVERIFIED. Its optional Studio client signs in with a Claude or ChatGPT account or an API key: skip it.

## Sources
- https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- https://forums.unrealengine.com/t/unreal-engine-5-8-released/2729274
- https://github.com/WildCake/unreal-engine-mcp-codex (third party; `StartServer`, `GenerateClientConfig`)
- https://www.strayspark.studio/blog/epic-official-mcp-plugin-ue5-8-vs-third-party (third party; read-back claim)
- https://github.com/ChiR24/Unreal_mcp
- https://github.com/db-lyon/ue-mcp
- https://github.com/IvanMurzak/Unreal-MCP (not recommended; cloud default)
