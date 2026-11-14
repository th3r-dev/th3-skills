# Reference first

Words lose spacing, proportion and type. Pictures don't. Before designing anything with open
style choices, collect references and let them carry the look; the prompt only says what to
build. Adapted from [Leonxlnx/cook](https://github.com/Leonxlnx/cook) (MIT) and the reference
tools below.

The product's own screens are always the first reference. Outside ones fill only what the
product's system leaves open (see the order of authority in [SKILL.md](../SKILL.md)).

## How many, and what

- **9 to 12 references** for a new page or a redesign; 3 to 5 for one component or state.
- Mix whole pages (layout, rhythm) with crops of single parts (a nav, a pricing table, a form).
- Match the kind of work ([taste.md](taste.md#1-classify-the-work-first)): an admin tool takes
  references from good tools, not from award-winning landing pages.
- For motion, take screen recordings, not descriptions.

Number them in the work folder: `refs/R01.png`, `R02` … for stills, `refs/V01.webm` … for video.

## Sources

| Source | Use for | Setup |
|---|---|---|
| The product itself | Sibling screens, its components and tokens | Figma file, the live app, `design-flow` captures |
| [Inspo MCP](https://github.com/Nutlope/inspo) | ~830 production sites, desktop + mobile, with palette, type ramp and a DESIGN.md per site | `claude mcp add --transport http inspo https://inspomcp.dev/api/mcp` |
| [Awwwards MCP](https://github.com/INSANE0777/Awwwards-mcp) | Award-winning sites, design DNA, motion and section analysis of any URL | `claude mcp add awwwards -- npx -y awwwards-mcp` |
| Browser | Screenshots and recordings of any URL the user names | Claude in Chrome, or Playwright (`~/.venvs/diagram-design`) |
| Dribbble, Mobbin, the user's own picks | Single patterns | Screenshots dropped into `refs/` |

Useful calls:

- **Inspo:** `recommend(brief)` first, which composes most of the others. Then `search_screens`,
  `find_reference_components`, `get_design_system` for the palette, type and spacing of a pick.
- **Awwwards:** `search_sites` → `get_site_details` (design DNA) → `create_design_brief` for 2–5
  picks. For a site's motion: `record_site_motion`, `analyze_scroll_map`, `analyze_hover_census`.
  `analyze_page_structure` maps sections. The browser tools need Playwright installed beside it;
  plain `npx` gives only the catalogue tools.

## Shot list

Write `SHOTS.md` beside the references, one line each: what to take from it and what to leave.

```text
R01  hero: the type scale and the left-aligned headline; not its dark ground
R02  pricing: three tiers in one row, the middle one marked by border only
V01  nav: 200 ms fade + 8 px slide on open; not the cursor trail
```

Take from many references, never one element 1:1. A reference's code, copy, photographs or
signature effect is never copied.

## The prompt

Short. The references do the describing.

```text
Build <what> for <who>. Main action: <action>.
References: refs/R01–R12, notes in SHOTS.md. Match their spacing, type and composition,
in this product's own identity. Product tokens and components first.
```

## Privacy

References are third-party work: keep them in the work folder, credit the source if one is
shown publicly, and don't commit them to a public repo. Never send the user's private screens
to an outside reference service.
