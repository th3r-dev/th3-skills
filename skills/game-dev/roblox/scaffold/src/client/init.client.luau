--!strict
-- Client entry: Rojo makes this folder StarterPlayerScripts.Client (a LocalScript).
-- It only shows state; it never changes the score (the server owns it).

local Players = game:GetService("Players")

local player = Players.LocalPlayer
local coins = player:WaitForChild("leaderstats"):WaitForChild("Coins")

local gui = Instance.new("ScreenGui")
gui.Name = "Hud"
gui.ResetOnSpawn = false
local label = Instance.new("TextLabel")
label.Size = UDim2.fromOffset(220, 48)
label.Position = UDim2.new(0.5, -110, 0, 16)
label.BackgroundTransparency = 0.3
label.TextScaled = true
label.Parent = gui
gui.Parent = player:WaitForChild("PlayerGui")

local function show()
	label.Text = `Coins: {coins.Value}`
end
coins.Changed:Connect(show)
show()
