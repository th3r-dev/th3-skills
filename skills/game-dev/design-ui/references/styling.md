# Styling: tokens and themes with universal styling

design-core's rule is "spacing, colour, type and radius come from tokens". On Roblox the token store
is **universal styling** ([docs](https://create.roblox.com/docs/ui/styling)), a CSS-like system:

| Object | Job |
|---|---|
| `StyleSheet` | holds rules; its **attributes** are tokens, read as `"$Name"` |
| `StyleRule` | `Selector` plus properties set with `SetProperties({...})` |
| `StyleLink` | parented to a ScreenGui, applies one sheet to that tree (one sheet per tree) |
| `StyleDerive` | parented to a sheet, inherits another sheet's tokens and rules |
| `StyleQuery` | a named condition (e.g. `MinSize`) that a rule selects with `@Name` |

Selectors the docs show: a class (`TextButton`), a tag with a leading dot (`.Primary`, applied with
`CollectionService:AddTag`), a UI modifier with `::` (`Frame.Panel::UICorner`), a query with `@`
(`@Wide`). Hover and press states exist as GuiState in the Style Editor; until their selector
strings are confirmed in Studio, drive hover and press feedback with a tween in Luau.

## The shape that scales

```
Tokens      raw values: palette, font families, radius, gaps     (one StyleSheet, attributes)
  └─ Theme  semantic names over the tokens: Panel, OnPanel, Accent, Danger, Price, PriceShort
       └─ Design  rules by class and tag, reading only the semantic names
            └─ StyleLink on each ScreenGui
```

A light and a dark theme define the **same** semantic names, so switching is one `StyleDerive`
re-pointed. Rules never name a raw colour; a rule that does is a literal that will drift.

## In Luau

The example builds the sheets from one typed table, so tokens are also checkable under Lune.
Full module: [`examples/craghold-hud/src/client/Theme.luau`](../examples/craghold-hud/src/client/Theme.luau);
the values: [`src/shared/Tokens.luau`](../examples/craghold-hud/src/shared/Tokens.luau).

```lua
local sheet = Instance.new("StyleSheet")
for name, value in Tokens.colors do
	sheet:SetAttribute(name, value)          -- read anywhere as "$Panel", "$Accent"...
end

local rule = Instance.new("StyleRule")
rule.Selector = ".Panel"                     -- every frame tagged Panel
rule:SetProperties({ BackgroundColor3 = "$Panel", BorderSizePixel = 0 })
rule.Parent = sheet

local corner = Instance.new("StyleRule")
corner.Selector = "Frame.Panel::UICorner"    -- the rounded corner comes from the sheet too
corner:SetProperties({ CornerRadius = UDim.new(0, Tokens.radius) })
corner.Parent = sheet

local link = Instance.new("StyleLink")
link.StyleSheet = sheet
link.Parent = screenGui
```

## Rules

- Colours, font families, radius and the gap scale are tokens; sizes and positions stay Scale in the
  layout (tokens don't replace layout objects).
- One semantic token per meaning: `Price` and `PriceShort` (red), not "the red one".
- Text colour on a plate is always checked against that plate, at least 4.5:1 (design-core's
  interface baseline); the example's `Tokens` test enforces it.
- When a game already has a sheet, extend it. Don't fork the palette (design-core's order of authority).
