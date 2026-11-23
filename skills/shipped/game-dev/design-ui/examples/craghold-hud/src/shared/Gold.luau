--!strict
-- Gold as players read it. Below 100,000: the exact number with separators ("12,500"). From
-- 100,000 up: one decimal and a suffix ("100K", "9.9M", "1B"), rounded down so it never overstates.
-- The delta beside the count is compact from 1,000 ("+8.3K"), since its box is narrow on a phone.

local Gold = {}

Gold.SHORT_FROM = 100000

-- largest first; simulator games run past trillions, so Qa (1e15) and Qi (1e18) too
local UNITS =
	{ { 1e18, "Qi" }, { 1e15, "Qa" }, { 1e12, "T" }, { 1e9, "B" }, { 1e6, "M" }, { 1e3, "K" } }

function Gold.format(amount: number): string
	local whole = tostring(math.floor(math.abs(amount)))
	local grouped = whole:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	if grouped:sub(1, 1) == "," then
		grouped = grouped:sub(2)
	end
	return if amount < 0 then "-" .. grouped else grouped
end

-- The exact number below `from` (default SHORT_FROM), a suffixed one from there up.
function Gold.short(amount: number, from: number?): string
	local size = math.abs(amount)
	local sign = if amount < 0 then "-" else ""
	if size < (from or Gold.SHORT_FROM) then
		return sign .. Gold.format(size)
	end
	for _, u in UNITS do
		if size >= u[1] then
			local v = math.floor(size / u[1] * 10) / 10
			local text = if v == math.floor(v)
				then tostring(math.floor(v))
				else string.format("%.1f", v)
			return sign .. text .. u[2]
		end
	end
	return sign .. Gold.format(size)
end

function Gold.delta(amount: number): string
	return (if amount >= 0 then "+" else "-") .. Gold.short(math.abs(amount), 1000)
end

return Gold
