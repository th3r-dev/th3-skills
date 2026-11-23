--!strict
-- The UI's design tokens, from design/DESIGN.md. Hex strings, not Color3, so tests/run.luau can
-- check every text/plate pair for contrast under Lune; Theme turns them into a StyleSheet.

local Tokens = {}

Tokens.colors = {
	Panel = "#14213D",
	OnPanel = "#FFF6E2",
	Muted = "#A9B4CC",
	Accent = "#FFB23F",
	OnAccent = "#14213D",
	PriceShort = "#FF6B5E",
	Danger = "#C8302A",
	OnDanger = "#FFFFFF",
	Level = "#5BD15B",
	Disabled = "#3A4560",
	OnDisabled = "#C5CBD8",
	Outline = "#0B1220",
	Backdrop = "#000000",
}

-- every text colour and the plate it sits on; the test holds each pair to 4.5:1
Tokens.textPairs = {
	{ "OnPanel", "Panel" },
	{ "Muted", "Panel" },
	{ "Accent", "Panel" },
	{ "PriceShort", "Panel" },
	{ "Level", "Panel" },
	{ "OnAccent", "Accent" },
	{ "OnDanger", "Danger" },
	{ "OnDisabled", "Disabled" },
}

Tokens.fonts = {
	display = { family = "Montserrat", weight = "Heavy" }, -- Enum.FontWeight names: 900 is Heavy, not Black
	body = { family = "BuilderSans", weight = "Medium" },
}

Tokens.radius = { plate = 12, button = 10 }
Tokens.outline = 3
Tokens.minTap = 44 -- px: the smallest a Scale-sized button may get on any screen

return Tokens
