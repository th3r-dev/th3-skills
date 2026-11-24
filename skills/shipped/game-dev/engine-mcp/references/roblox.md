# Roblox: MCP

Checked 2026-11-18 against [create.roblox.com/docs/studio/mcp](https://create.roblox.com/docs/studio/mcp)
(updated 2026-11-17). Roblox renames tools; that page wins over this file and over
[roblox-suite's `roblox-mcp`](https://github.com/nonlooped/roblox-suite/blob/fc1c3dd26fef67ee4d7b6e20b1299b44fc6101ae/roblox-mcp/SKILL.md),
whose June names (`console_output`, `keyboard_input`, `set_active_studio`) are out of date.

## Pick

| Server | Official | License | Versions | Transport | Use when |
|---|---|---|---|---|---|
| Studio MCP (built into Studio) | yes | Roblox terms | current Studio, macOS and Windows | stdio | always: there is no reason to use a third-party server |

## Default: Studio MCP

### Editor side (the person does this)

1. Update Studio. Open the place.
2. **Assistant → `…` → Manage MCP Servers → Enable Studio as MCP server.**
3. Quick connect can wire Antigravity, Codex CLI, Claude Code, Claude Desktop, Cursor, Gemini CLI and
   VS Code by itself. A connected client shows as a green dot with a count.

### Wire the agent

```bash
python scripts/engine_mcp.py config --engine roblox --client claude --root <project>          # shows it
python scripts/engine_mcp.py config --engine roblox --client claude --root <project> --write  # on a yes
```

`roblox/scripts/roblox_setup.py mcp` does the same. The entry:

```json
{ "mcpServers": { "Roblox_Studio": { "command": "/Applications/RobloxStudio.app/Contents/MacOS/StudioMCP" } } }
```

Windows: `"command": "cmd.exe", "args": ["/c", "%LOCALAPPDATA%\\Roblox\\mcp.bat"]`. Linux has no Studio.

### Tools

Every call takes a `studio_id`; get it from `list_roblox_studios` (name, id, place id).

| Group | Tools |
|---|---|
| Scripts | `script_read`, `multi_edit` (needs `datamodel_type`), `script_search`, `script_grep` |
| Data model | `search_game_tree`, `inspect_instance`, `subagent` (`explore`, `playtest`) |
| Code | `execute_luau` (`datamodel_type`: Edit, Client or Server) |
| Play | `get_studio_state`, `start_stop_play`, `get_console_output`, `screen_capture` (optional camera) |
| Input | `character_navigation`, `user_keyboard_input`, `user_mouse_input` |
| Assets | `generate_mesh`, `generate_material`, `generate_procedural_model`, `wait_job_finished`, `generate_animation`, `generate_avatar`, `search_asset`, `insert_asset`, `upload_image`, `store_image` |
| Docs | `http_get` (Roblox docs only), `skill` |
| Place | `save_place` |
| Other | `list_roblox_studios`, `submit_feedback` |

### Run-and-look loop

| Step | Tool |
|---|---|
| Which Studio | `list_roblox_studios` → `studio_id` |
| Enter play | `start_stop_play`, then `get_studio_state` until it reports play |
| Input | `character_navigation`, `user_keyboard_input`, `user_mouse_input` |
| Logs | `get_console_output` |
| Look | `screen_capture` |
| Stop | `start_stop_play` |

Playtests work across teleports inside one experience, with no publish needed.

### Security

- `execute_luau` runs with the signed-in account: it can publish, write DataStores and call HTTP.
  Work on a test place, under git.
- Ask first: `save_place` (a new place version), `insert_asset`, `upload_image`, anything generated or paid.
- Turn the server off when not in use (the same toggle).

## Sources

- https://create.roblox.com/docs/studio/mcp
- https://create.roblox.com/docs/studio/mcp-open-cloud
- https://github.com/nonlooped/roblox-suite/tree/fc1c3dd26fef67ee4d7b6e20b1299b44fc6101ae/roblox-mcp
