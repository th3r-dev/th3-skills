# Godot 4: MCP
Checked 2026-11-18. Recheck the server's README before trusting a version or a tool name.

There is no official Godot Foundation MCP server (no MCP repo in the `godotengine` org, no announcement found). Every option below is community.

## Pick
| Server | Official | License | Versions | Transport | Use when |
|---|---|---|---|---|---|
| tomyud1/godot-mcp ("Godlink") | no | MIT | Godot 4.4+ | stdio to Node, WebSocket `:6505` to an editor plugin | **default**: needs run, input, screenshots, logs |
| Coding-Solo/godot-mcp | no | MIT | Godot 4.4+ for UID tools; Node 18+ | stdio, shells out to the Godot CLI, no addon, no port | no addon allowed, or run + logs is enough |
| tugcantopaloglu/godot-mcp | no | MIT | 4.4+ (tested 4.7), GDScript and C# | stdio (install UNVERIFIED) | need C#, headless export, 157 tools |
| yurineko73/Godot-MCP-Native | no | MIT | UNVERIFIED | HTTP `:9080` or stdio, served by the editor plugin itself | no Node wanted |

Avoid: ee0pdt/Godot-MCP (last push 2025-03), bradypp/godot-mcp (last push 2025-05), youichi-uda/godot-mcp-pro (server is paid; public repo is the addon only).

## Default: tomyud1/godot-mcp
Repo https://github.com/tomyud1/godot-mcp. MIT, v0.6.0 (2026-08-24), npm `godot-mcp-server` 0.6.1.

### Editor side (the person does this)
1. Install the plugin:
   - Godot 4.7+: Asset Store tab, search "Godlink", install "Godlink MCP".
   - Godot 4.6 and older: AssetLib tab, search "mcp", install "Godot AI Assistant tools MCP".
   - Manual: copy `addons/godot_mcp/` from the repo into the project's `addons/`.
2. Project > Project Settings > Plugins: enable **Godot MCP**.
3. Keep the editor open on the project. The server talks to the plugin over `ws://:6505`; no editor, no tools.

### Wire the agent
```bash
python scripts/engine_mcp.py config --engine godot --client claude --root <project>
```
Entry it writes (Windows: `"command": "cmd"`, `"args": ["/c", "npx", "-y", "godot-mcp-server@0.6.1"]`):
```json
{"mcpServers": {"godot": {"command": "npx", "args": ["-y", "godot-mcp-server@0.6.1"]}}}
```
Restart the agent, then call `tools/list` and record the names.

### Tools
69 tools. The README gives groups and counts, not names: tool names are UNVERIFIED, call `tools/list`.

| Group | Count | Does |
|---|---|---|
| Project & Runtime | 28 | run/stop the game, send input, take screenshots, inspect live nodes, read errors and logs, project settings, input map, autoloads |
| Script & File Operations | 8 | edit and validate scripts, write files, rename/move with reference updates, folders |
| File Browsing | 4 | browse, read, search, create scripts |
| Undo & Batching | 4 | undo/redo any AI change, run many changes as one all-or-nothing batch |
| Scene and node tools | UNVERIFIED | scene tree, add/edit nodes |

### Run-and-look loop
| Step | Tool |
|---|---|
| Run | runtime "run project" tool in Project & Runtime (name UNVERIFIED, `tools/list`) |
| Input | runtime "send input" tool (name UNVERIFIED) |
| Read logs | runtime "errors and logs" tool (name UNVERIFIED) |
| Screenshot | runtime "screenshot" tool (name UNVERIFIED; whether it needs the game running is UNVERIFIED) |
| Stop | runtime "stop" tool (name UNVERIFIED) |

Order: run, wait a beat, read logs, screenshot, edit, stop, repeat. A step that errored is NOT ASSESSED, never a pass.

### Security
- Writes files and edits scripts: it is arbitrary code in the project. Commit first.
- Edits go to disk, not the editor tree, so **Ctrl+Z does not undo them**. Use the undo tool.
- Opens a WebSocket on `:6505`. Loopback-only binding is UNVERIFIED: do not forward the port.
- Telemetry: UNVERIFIED.

## Alternates

### Coding-Solo/godot-mcp (no addon)
https://github.com/Coding-Solo/godot-mcp. MIT, 6,688 stars, last commit 2026-04-16, npm `@coding-solo/godot-mcp` 0.1.1. Not written by the script; add by hand.
```json
{"mcpServers": {"godot": {"command": "npx", "args": ["-y", "@coding-solo/godot-mcp@0.1.1"], "env": {"GODOT_PATH": "/path/to/godot"}}}}
```
`GODOT_PATH` overrides executable detection. `DEBUG=true` turns on server logging.
- Loop tools: `run_project`, `get_debug_output`, `stop_project`. No screenshot, no input, no scene-tree read, no test or project export (only `export_mesh_library`).
- Other tools: `launch_editor`, `get_godot_version`, `list_projects`, `get_project_info`, `create_scene`, `add_node`, `load_sprite`, `save_scene`, `get_uid`, `update_project_uids`.
- Security: complex ops run one bundled `godot_operations.gd`. The newest commit fixes arbitrary GDScript instantiation via `add_node` / `create_scene`: treat those two as an injection surface and keep the pin current. No open port.

### tugcantopaloglu/godot-mcp
https://github.com/tugcantopaloglu/godot-mcp. MIT, 520 stars, v3.1.0 (2026-07-13). Install and config: UNVERIFIED, follow its README.
- Loop tools named in its README: `run_project`, `game_screenshot` (base64 PNG), `export_project` (headless), `manage_export_presets`.

### yurineko73/Godot-MCP-Native
https://github.com/yurineko73/Godot-MCP-Native. MIT, 879 stars, v1.0.8 (2026-07-26). The plugin is the MCP server (no Node). Enable it under Plugins; default `http_port` 9080, or `--mcp-transport=stdio`. Client config: UNVERIFIED.
- Named in its README: `get-editor-screenshot` (editor viewport, not the running game), `list-export-presets`, `validate-export-preset`, `run-export`.

## Sources
- https://github.com/tomyud1/godot-mcp (README, release via API)
- https://github.com/Coding-Solo/godot-mcp (README, last commit via API)
- https://github.com/tugcantopaloglu/godot-mcp (README via API)
- https://github.com/yurineko73/Godot-MCP-Native (README via API)
- https://github.com/youichi-uda/godot-mcp-pro (README via API)
- https://registry.npmjs.org/godot-mcp-server and https://registry.npmjs.org/@coding-solo/godot-mcp (versions)
- https://api.github.com/orgs/godotengine/repos (no MCP repo)
