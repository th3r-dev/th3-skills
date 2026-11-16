-- Server entry: Rojo makes this folder ServerScriptService.Server (a Script).
-- The server owns the score. A client never reports coins: the server sees the
-- touch, applies Rules and writes leaderstats, which replicate to everyone.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Rules = require(ReplicatedStorage.Shared.Rules)

local states: { [Player]: Rules.State } = {}

Players.PlayerAdded:Connect(function(player)
	states[player] = Rules.newState()
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	local coins = Instance.new("IntValue")
	coins.Name = "Coins"
	coins.Parent = leaderstats
	leaderstats.Parent = player
end)

Players.PlayerRemoving:Connect(function(player)
	states[player] = nil
end)

-- One coin above the spawn. Touched, it pays one coin and hides for three seconds.
local coin = Instance.new("Part")
coin.Name = "Coin"
coin.Shape = Enum.PartType.Cylinder
coin.Size = Vector3.new(0.5, 3, 3)
coin.Color = Color3.fromRGB(255, 200, 40)
coin.Anchored = true
coin.CanCollide = false
coin.Position = Vector3.new(0, 4, -10)
coin.Parent = workspace

local hidden = false
coin.Touched:Connect(function(hit)
	if hidden then
		return
	end
	local player = Players:GetPlayerFromCharacter(hit.Parent)
	local state = player and states[player]
	if not (player and state) then
		return
	end
	hidden = true
	coin.Transparency = 1
	local nextState = Rules.collect(state, 1)
	states[player] = nextState
	player.leaderstats.Coins.Value = nextState.coins
	if Rules.won(nextState) then
		print(`{player.Name} reached {nextState.goal} coins`)
	end
	task.wait(3)
	coin.Transparency = 0
	hidden = false
end)
