--!strict
-- Client entry: builds the HUD and the key shop. Both only show what the server publishes; the
-- shop asks the server to buy and waits for its answer.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local RunService = game:GetService("RunService")

local Hud = require("@self/Hud")
local KeyShop = require("@self/KeyShop")
local LayoutLint = require("@self/LayoutLint")

local player = Players.LocalPlayer
local shop = KeyShop.new(player)
Hud.new(player, function()
	shop:open()
end)

ProximityPromptService.PromptTriggered:Connect(function(prompt)
	if prompt.Name == "OpenShop" then
		shop:open()
	end
end)

if RunService:IsStudio() then
	task.delay(5, LayoutLint.run) -- once the server's first values have drawn the HUD
end
