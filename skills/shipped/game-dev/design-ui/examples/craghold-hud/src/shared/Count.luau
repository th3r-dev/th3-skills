--!strict
-- The numbers a rising counter shows on its way up (juice.md's tick-up): whole numbers, always
-- increasing, and the last one exactly the new value, so the counter never stops one short.

local Count = {}

function Count.steps(from: number, to: number, count: number): { number }
	local out = {}
	local span = to - from
	if span <= 0 then
		return { to }
	end
	local n = math.min(count, math.floor(span))
	for i = 1, n - 1 do
		local v = from + math.floor(span * i / n)
		if v > (out[#out] or from) then
			table.insert(out, v)
		end
	end
	table.insert(out, to)
	return out
end

return Count
