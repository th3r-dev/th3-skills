--!strict
-- Server entry: Rojo makes this folder ServerScriptService.Server (a Script), and its other
-- modules its children. The only server Script: everything else is a module it wires up.

local Players = game:GetService("Players")

local PickupSpawner = require("@self/PickupSpawner")
local Wallet = require("@game/ReplicatedStorage/Shared/Wallet")

local GOAL = 10

local wallets: { [Player]: Wallet.Wallet } = {}

local function onPlayerAdded(player: Player)
	wallets[player] = Wallet.new(GOAL)
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	local coins = Instance.new("IntValue")
	coins.Name = "Coins"
	coins.Parent = leaderstats
	leaderstats.Parent = player
end

local function onPlayerRemoving(player: Player)
	wallets[player] = nil
end

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(onPlayerRemoving)
for _, player in Players:GetPlayers() do
	onPlayerAdded(player)
end

PickupSpawner.new("coin", Vector3.new(0, 4, -10), wallets)
PickupSpawner.new("gem", Vector3.new(8, 4, -16), wallets)
