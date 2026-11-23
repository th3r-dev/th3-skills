--!strict
-- Puts one Pickup in the world as a Part and pays whoever touches it. Owns its Part and its
-- connections, and destroy() removes both: anything this creates, it can clean up.

local Players = game:GetService("Players")

local PickupFactory = require("@game/ReplicatedStorage/Shared/PickupFactory")
local Wallet = require("@game/ReplicatedStorage/Shared/Wallet")

local COLORS: { [string]: Color3 } = {
	coin = Color3.fromRGB(255, 200, 40),
	gem = Color3.fromRGB(80, 200, 255),
}

local PickupSpawner = {}
PickupSpawner.__index = PickupSpawner

export type PickupSpawner = typeof(setmetatable(
	{} :: {
		part: Part,
		_connections: { RBXScriptConnection },
	},
	PickupSpawner
))

type Wallets = { [Player]: Wallet.Wallet }

function PickupSpawner.new(kind: string, position: Vector3, wallets: Wallets): PickupSpawner
	local pickup = PickupFactory.create(kind)

	local part = Instance.new("Part")
	part.Name = `Pickup_{kind}`
	part.Shape = Enum.PartType.Cylinder
	part.Size = Vector3.new(0.5, 3, 3)
	part.Color = COLORS[kind] or Color3.new(1, 1, 1)
	part.Anchored = true
	part.CanCollide = false
	part.Position = position
	part.Parent = workspace

	local self = {
		part = part,
		_connections = {},
	}

	-- The server decides: it sees the touch, checks the pickup, and writes the wallet.
	table.insert(self._connections, part.Touched:Connect(function(hit: BasePart)
		local character = hit:FindFirstAncestorOfClass("Model")
		local player = character and Players:GetPlayerFromCharacter(character)
		local wallet = player and wallets[player]
		if not (player and wallet) then
			return
		end
		local value = pickup:take(os.clock())
		if value == 0 then
			return
		end
		part.Transparency = 1
		local coins = wallet:add(value)
		local leaderstats = player:FindFirstChild("leaderstats")
		local counter = leaderstats and leaderstats:FindFirstChild("Coins")
		if counter and counter:IsA("IntValue") then
			counter.Value = coins
		end
		task.delay(pickup.definition.respawnSeconds, function()
			part.Transparency = 0
		end)
	end))

	return setmetatable(self, PickupSpawner)
end

function PickupSpawner.destroy(self: PickupSpawner)
	for _, connection in self._connections do
		connection:Disconnect()
	end
	table.clear(self._connections)
	self.part:Destroy()
end

return PickupSpawner
