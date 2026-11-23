--!strict
-- Tokens (src/shared/Tokens.luau) for the UI code: colours as Color3, fonts as Font. Ui.tone is the
-- only place a colour is applied, so a token change or a theme swap is one table.
-- Universal styling (StyleSheet / StyleRule / StyleLink) is the documented home for tokens, but in a
-- November 2026 Studio playtest no sheet applied (five minimal cases: runtime and edit, parented or
-- not, class and tag selectors); see references/styling.md.

local Tokens = require("@game/ReplicatedStorage/Shared/Tokens")

local Theme = {}

local cache: { [string]: Color3 } = {}

function Theme.color(token: string): Color3
	local hit = cache[token]
	if hit then
		return hit
	end
	local hex = Tokens.colors[token]
	assert(hex, `no colour token {token}`)
	local c = Color3.fromHex(hex)
	cache[token] = c
	return c
end

function Theme.font(kind: "display" | "body"): Font
	local f = Tokens.fonts[kind]
	return Font.fromName(f.family, (Enum.FontWeight :: any)[f.weight])
end

return Theme
