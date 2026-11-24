--!strict
-- The one place pickups are made. A new kind is one row in DEFINITIONS; nothing else changes.

local Pickup = require("./Pickup")

local DEFINITIONS: { [string]: Pickup.Definition } = table.freeze({
	coin = table.freeze({ kind = "coin", value = 1, respawnSeconds = 3 }),
	gem = table.freeze({ kind = "gem", value = 5, respawnSeconds = 10 }),
})

local PickupFactory = {}

function PickupFactory.create(kind: string): Pickup.Pickup
	local definition = DEFINITIONS[kind]
	assert(definition, `unknown pickup kind "{kind}"`)
	return Pickup.new(definition)
end

function PickupFactory.kinds(): { string }
	local kinds = {}
	for kind in DEFINITIONS do
		table.insert(kinds, kind)
	end
	table.sort(kinds)
	return kinds
end

return PickupFactory
