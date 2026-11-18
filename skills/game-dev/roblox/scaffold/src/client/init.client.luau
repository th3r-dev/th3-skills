--!strict
-- Client entry: Rojo makes this folder StarterPlayerScripts.Client (a LocalScript).
-- It only shows state; it never changes the score (the server owns it).

local Players = game:GetService("Players")

local player = Players.LocalPlayer
local coins = player:WaitForChild("leaderstats"):WaitForChild("Coins")

-- Layout per design-ui (../../../design-ui/SKILL.md): Scale only, an AnchorPoint at the edge it
-- grows from, inside the core-UI safe insets; a brief comes first once the HUD grows.
local gui = Instance.new("ScreenGui")
gui.Name = "Hud"
gui.ResetOnSpawn = false
gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
local label = Instance.new("TextLabel")
label.AnchorPoint = Vector2.new(0.5, 0)
label.Size = UDim2.fromScale(0.2, 0.07)
label.Position = UDim2.fromScale(0.5, 0.02)
label.BackgroundTransparency = 0.3
label.TextScaled = true
local fit = Instance.new("UITextSizeConstraint")
fit.MinTextSize = 14
fit.MaxTextSize = 32
fit.Parent = label
label.Parent = gui
gui.Parent = player:WaitForChild("PlayerGui")

local function show()
	label.Text = `Coins: {coins.Value}`
end
coins.Changed:Connect(show)
show()
