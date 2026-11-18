--!strict
-- A player's level and XP. Pure state: the server owns one per player and copies it to attributes;
-- the HUD reads the attributes. The farm levels a player to FARM_CAP, where the dungeon key unlocks.

local Progress = {}
Progress.__index = Progress

Progress.FARM_CAP = 10

export type Progress = typeof(setmetatable(
	{} :: {
		level: number,
		xp: number,
	},
	Progress
))

-- XP needed to go from `level` to the next one.
function Progress.xpToNext(level: number): number
	return 100 * level
end

function Progress.new(): Progress
	return setmetatable({ level = 1, xp = 0 }, Progress)
end

-- Adds XP, levelling up as far as the farm allows. Returns the levels gained.
function Progress.add(self: Progress, xp: number): number
	assert(xp > 0, "xp must be above 0")
	local before = self.level
	if self.level >= Progress.FARM_CAP then
		return 0
	end
	self.xp += xp
	while self.level < Progress.FARM_CAP and self.xp >= Progress.xpToNext(self.level) do
		self.xp -= Progress.xpToNext(self.level)
		self.level += 1
	end
	if self.level >= Progress.FARM_CAP then
		self.xp = 0
	end
	return self.level - before
end

-- 0..1 along the XP bar; full at the farm cap.
function Progress.fraction(self: Progress): number
	if self.level >= Progress.FARM_CAP then
		return 1
	end
	return self.xp / Progress.xpToNext(self.level)
end

return Progress
