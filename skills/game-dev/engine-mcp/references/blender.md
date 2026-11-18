# Blender: MCP
Checked 2026-11-18. Recheck the server's README before trusting a version or a tool name.

Building models from a headless Python script is the modeling sub-skill: `../../modeling/SKILL.md`. MCP is for looking at and poking a live Blender, not for the build.

## Pick
| Server | Official | License | Versions | Transport | Use when |
|---|---|---|---|---|---|
| Blender Lab MCP (`lab/blender_mcp`) | yes (Blender Lab, Blender Foundation) | GPL-3.0-or-later | Blender 5.1+ (add-on manifest); Python 3.10+ | stdio, then TCP socket to an add-on (port set in add-on prefs, default UNVERIFIED) | Blender is 5.1+ and official matters |
| ahujasid/mcp-for-blender (formerly blender-mcp) | no | MIT | Blender 3.0+; Python 3.10+; uv | stdio via `uvx`, JSON over TCP `localhost:9876` | **default**: older Blender, `look` multi-angle views |

Avoid: VxASI/blender-mcp-vxai (last push 2025-03), pranav-deshmukh/blender-mcp (last push 2025-08), and any "blender-ai-copilot" style clone with ~500 stars and no history (unvetted).

## Default: ahujasid/mcp-for-blender
Repo https://github.com/ahujasid/mcp-for-blender. MIT, 34,816 stars, PyPI 2.3.0 (2026-11-15). Third-party; it says it is not made by Blender.

### Editor side (the person does this)
1. Install uv with the official installer, not `pip install uv`. Read any install script before running it; the agent does not pipe one into a shell.
2. Install the add-on: `uvx mcp-for-blender@2.3.0 install-addon` (the README shows the unpinned form).
3. Blender: Edit > Preferences > Add-ons: enable **Interface: MCP for Blender**.
4. 3D viewport, `N`, **MCP for Blender** tab: **Start MCP Server** if it is not running.
5. After bumping the pin, reinstall the add-on. Whether server and add-on must match versions is UNVERIFIED.
6. Run one server only (one client at a time).

### Wire the agent
```bash
python scripts/engine_mcp.py config --engine blender --client claude --root <project>
```
Entry it writes:
```json
{"mcpServers": {"blender": {"command": "uvx", "args": ["mcp-for-blender@2.3.0"], "env": {"DISABLE_TELEMETRY": "true"}}}}
```
GUI clients may not see `uvx` on PATH (`spawn uvx ENOENT`): use the absolute path from `which uvx` as `command`. Optional env: `BLENDER_HOST` (default `localhost`), `BLENDER_PORT` (default `9876`).

### Tools
9 tools, named in its README.

| Tool | Does |
|---|---|
| `execute_blender_code` | run Python in the live Blender |
| `look` | view from `viewport`, `camera`, `angles` (auto-framed multi-view sheet) or `frames` (animation strip); shaded solid, material, rendered, wireframe or xray; or show an image file |
| `get_scene_info` | compact scene summary, one line per object; drill in with `root` or `query` |
| `generate_3d` | generate and import a model (Tripo, Hunyuan3D, Hyper3D Rodin, Meshy) |
| `generate_gaussian_world` | World Labs Gaussian-splat world (Blender 5.3+) |
| `search_assets`, `import_asset` | Poly Haven, Sketchfab, Poly Pizza |
| `get_addon_status` | Blender and add-on version, enabled libraries |
| `disable_telemetry`, `record_trajectory_feedback` | data-collection controls |

### Run-and-look loop
| Step | Tool |
|---|---|
| Run | `execute_blender_code` (build or change the scene) |
| Input | n/a, Blender is not a running game |
| Read logs | `execute_blender_code` result; whether `print` output and Python tracebacks come back is UNVERIFIED, test it once |
| Screenshot | `look` (`camera` for the shot, `angles` for a turnaround) |
| Stop | n/a |

Order: execute, `look`, fix, execute, `look`. Judge the picture, not the absence of an error.

### Security
- `execute_blender_code` runs arbitrary Python with the person's file access. Save and commit the `.blend` first; the README says to save before using it.
- Telemetry: a minimal anonymous usage record (install ID, tool name, success, timing, versions, OS) is sent by default; prompts, code, screenshots and scene data only on opt-in. The written entry sets `DISABLE_TELEMETRY=true`, which turns all of it off.
- The add-on listens on localhost. "Allow Remote Connections" has no authentication or encryption: leave it off; use an SSH tunnel if a remote machine is needed.
- `generate_3d`, `generate_gaussian_world` and the asset tools call external services. Do not call them without an ask.

## Alternates

### Blender Lab MCP (official)
https://projects.blender.org/lab/blender_mcp. GPL-3.0-or-later, 39 stars, v1.0.3 (2026-09-11), last commit 2026-09-29. Docs page https://www.blender.org/lab/mcp-server/ was blocked (HTTP 403) and not read.
- Install: follow its own README. Server: `pip install git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp` (unpinned, so pin a tag or commit yourself) or the `.mcpb` bundle for Claude Desktop. Add-on: add the extensions repository `https://lab.blender.org/`, install and enable the MCP add-on.
- Client config: UNVERIFIED. The bundle manifest runs `uv run blender-mcp`; the pip entry point is `blender-mcp`. The script does not write this entry. Do not guess a JSON: follow the repo's install and read what it produces.
- Loop tools: `execute_blender_code`, `get_screenshot_of_window_as_image`, `get_screenshot_of_area_as_image`, `render_viewport_to_path`, `render_thumbnail_to_path`.
- Other tools (26 in all): `get_objects_summary`, `get_object_detail_summary`, `get_blendfile_summary_*` (each with a `_for_cli` variant that opens a file in headless Blender), `get_screenshot_of_window_as_json`, `jump_to_tab_by_name`, `jump_to_tab_by_space_type`, `jump_to_view3d_object_by_name`, `jump_to_view3d_object_data_by_name`, `execute_blender_code_for_cli`, `get_python_api_docs`, `search_api_docs`, `search_manual_docs` (API and manual bundled).
- Security: `execute_blender_code` runs LLM Python; the repo's `weak_sandbox.py` calls itself "more guidance" than a sandbox. The add-on runs a local TCP socket (host and port in prefs). No telemetry found in the README; privacy policy at blender.org/privacy-policy.

## Sources
- https://projects.blender.org/lab/blender_mcp (README, `readme_tools.rst`, add-on manifest, `weak_sandbox.py`, releases, via the Gitea API)
- https://github.com/ahujasid/mcp-for-blender (README via API)
- https://pypi.org/pypi/mcp-for-blender/json (version, date)
