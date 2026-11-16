--!strict
-- One pickup's rules: what it is worth and when it can be taken again. Time is passed in,
-- so the class never waits or reads a clock and stays testable. PickupFactory builds these.

local Pickup = {}
Pickup.__index = Pickup

export type Definition = {
	kind: string,
	value: number,
	respawnSeconds: number,
}

export type Pickup = typeof(setmetatable(
	{} :: {
		definition: Definition,
		_availableAt: number,
	},
	Pickup
))

function Pickup.new(definition: Definition): Pickup
	local self = {
		definition = definition,
		_availableAt = 0,
	}
	return setmetatable(self, Pickup)
end

function Pickup.isAvailable(self: Pickup, now: number): boolean
	return now >= self._availableAt
end

-- Takes the pickup at `now`. Returns its value, or 0 while it is still respawning.
function Pickup.take(self: Pickup, now: number): number
	if not self:isAvailable(now) then
		return 0
	end
	self._availableAt = now + self.definition.respawnSeconds
	return self.definition.value
end

return Pickup
