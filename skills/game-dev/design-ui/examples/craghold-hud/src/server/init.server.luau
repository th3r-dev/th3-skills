--!strict
-- Server entry: owns every player's gold, level and key, and decides every purchase.
-- The stand-in loop (gold and XP every few seconds) replaces farming so the HUD can be seen working.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local KeyOffer = require("@game/ReplicatedStorage/Shared/KeyOffer")
local Net = require("@game/ReplicatedStorage/Shared/Net")
local Progress = require("@game/ReplicatedStorage/Shared/Progress")

local TICK_SECONDS = 2
local TICK_GOLD = 250
local TICK_XP = 60

type State = { progress: Progress.Progress, gold: number, hasKey: boolean }
local states: { [Player]: State } = {}

local function publish(player: Player, s: State)
	player:SetAttribute(Net.GOLD, s.gold)
	player:SetAttribute(Net.LEVEL, s.progress.level)
	player:SetAttribute(Net.XP, s.progress.xp)
	player:SetAttribute(Net.HAS_KEY, s.hasKey)
	player:SetAttribute(Net.HEARTBEAT, workspace:GetServerTimeNow())
end

Players.PlayerAdded:Connect(function(player)
	local s: State = { progress = Progress.new(), gold = 0, hasKey = false }
	states[player] = s
	publish(player, s)
end)

Players.PlayerRemoving:Connect(function(player)
	states[player] = nil
end)

local buyKey = Instance.new("RemoteFunction")
buyKey.Name = Net.BUY_KEY
buyKey.Parent = ReplicatedStorage

-- Studio-only switches for capturing every state in a playtest (workspace attributes), never live:
--   PurchaseDelay (seconds): hold the answer so the shop's Loading state can be seen
--   FailPurchases (bool): refuse every purchase so the Error state can be seen
--   PauseServer (bool): stop the ticks so the HUD's Reconnecting state can be seen
local function studioSwitch(name: string): any
	return if RunService:IsStudio() then workspace:GetAttribute(name) else nil
end

buyKey.OnServerInvoke = function(player: Player): (boolean, string?)
	local s = states[player]
	if not s then
		return false, "not ready"
	end
	local delay = studioSwitch("PurchaseDelay")
	if typeof(delay) == "number" and delay > 0 then
		task.wait(math.min(delay, 15))
	end
	if studioSwitch("FailPurchases") == true then
		return false, "refused"
	end
	local ok, why = KeyOffer.canBuy(s.gold, s.progress.level, s.hasKey)
	if not ok then
		return false, why
	end
	s.gold -= KeyOffer.PRICE
	s.hasKey = true
	publish(player, s)
	return true, nil
end

task.spawn(function()
	while true do
		task.wait(TICK_SECONDS)
		if studioSwitch("PauseServer") == true then
			continue
		end
		for player, s in states do
			s.gold += TICK_GOLD
			if s.progress.level < Progress.FARM_CAP then
				s.progress:add(TICK_XP)
			end
			publish(player, s)
		end
	end
end)
