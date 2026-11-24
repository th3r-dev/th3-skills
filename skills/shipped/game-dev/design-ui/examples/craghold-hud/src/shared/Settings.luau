--!strict
-- The player's settings and the one rule both sides use to clean them (references/settings.md).
-- The client cleans before it sends, the server cleans again before it keeps them; neither trusts
-- the other's table. Pure: no `game`, so Lune tests it.

local Settings = {}

export type Level = "Full" | "Reduced" | "Off"
export type Effects = Level | "Auto" -- Auto follows the player's Roblox Reduce Motion setting
export type Settings = {
	music: number, -- 0-100
	sound: number, -- 0-100
	effects: Effects,
	hints: boolean,
}

Settings.DEFAULTS = table.freeze({
	music = 60,
	sound = 80,
	effects = "Auto" :: Effects,
	hints = true,
})

local EFFECTS = { Auto = true, Full = true, Reduced = true, Off = true }
local RANK = { Off = 0, Reduced = 1, Full = 2 }

local function volume(v: any, default: number): number
	if typeof(v) ~= "number" or v ~= v then -- v ~= v catches NaN
		return default
	end
	return math.clamp(math.floor(v + 0.5), 0, 100)
end

-- Anything in, a valid Settings out: numbers clamped and rounded, unknown keys dropped, a wrong
-- type replaced by its default.
function Settings.validate(raw: any): Settings
	local t = if typeof(raw) == "table" then raw else {}
	local d = Settings.DEFAULTS
	return {
		music = volume(t.music, d.music),
		sound = volume(t.sound, d.sound),
		effects = if typeof(t.effects) == "string" and EFFECTS[t.effects]
			then t.effects
			else d.effects,
		hints = if typeof(t.hints) == "boolean" then t.hints else d.hints,
	}
end

-- The level every effect reads. A choice the player made in the game wins over the device.
function Settings.level(s: Settings, reducedMotion: boolean): Level
	if s.effects == "Auto" then
		return if reducedMotion then "Reduced" else "Full"
	end
	return s.effects :: Level
end

-- Does an effect that needs `need` play at `level`?
function Settings.allows(level: Level, need: Level): boolean
	return RANK[level] >= RANK[need]
end

return Settings
