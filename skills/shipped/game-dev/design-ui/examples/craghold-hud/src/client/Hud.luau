--!strict
-- The HUD from design/features/hud/design.md: level and XP, gold, the objective, the Shop button.
-- It only shows what the server published as player attributes; it never changes a value.

local TweenService = game:GetService("TweenService")

local Gold = require("@game/ReplicatedStorage/Shared/Gold")
local KeyOffer = require("@game/ReplicatedStorage/Shared/KeyOffer")
local Net = require("@game/ReplicatedStorage/Shared/Net")
local Progress = require("@game/ReplicatedStorage/Shared/Progress")
local Juice = require("./Juice")
local Ui = require("./Ui")

local STALE_SECONDS = 10
local DELTA_SECONDS = 1.5
local COIN = "rbxasset://sounds/electronicpingshort.wav"

local Hud = {}
Hud.__index = Hud

export type Hud = typeof(setmetatable(
	{} :: {
		player: Player,
		gui: ScreenGui,
		level: TextLabel,
		xpFill: Frame,
		gold: TextLabel,
		delta: TextLabel,
		objective: TextLabel,
		shop: TextButton,
		stale: Frame,
		shown: number?,
		shownLevel: number?,
	},
	Hud
))

function Hud.new(player: Player, openShop: () -> ()): Hud
	local gui = Instance.new("ScreenGui")
	gui.Name = "Hud"
	gui.ResetOnSpawn = false
	gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
	-- left-middle stack, anchored at its own left-middle so it grows away from the edge; clear of
	-- Roblox's chat window (top-left) and the thumbstick (bottom-left)
	local stack = Ui.frame(gui, "Stack", UDim2.fromScale(0.26, 0.32))
	stack.AnchorPoint = Vector2.new(0, 0.5)
	stack.Position = UDim2.fromScale(0.015, 0.5) -- centred: the chat's input bar reaches about a third down
	local cap = Instance.new("UISizeConstraint")
	cap.MaxSize = Vector2.new(360, math.huge)
	cap.Parent = stack
	Ui.list(stack, Enum.FillDirection.Vertical, 0.05)

	local levelPlate = Ui.plate(stack, "Level", UDim2.fromScale(1, 0.4), 4.4)
	levelPlate.LayoutOrder = 1
	Ui.pad(levelPlate, 0.04, 0.16)
	Ui.list(levelPlate, Enum.FillDirection.Horizontal, 0.04)
	local level = Ui.text(levelPlate, "Badge", UDim2.fromScale(0.34, 1), "display", "Level", 40)
	local track = Ui.frame(levelPlate, "Track", UDim2.fromScale(0.6, 0.5), "Disabled")
	Ui.corner(track, 8)
	local xpFill = Ui.frame(track, "Fill", UDim2.fromScale(0, 1), "Level")
	Ui.corner(xpFill, 8)

	local goldPlate = Ui.plate(stack, "Gold", UDim2.fromScale(1, 0.4), 4.4)
	goldPlate.LayoutOrder = 2
	Ui.pad(goldPlate, 0.04, 0.16)
	Ui.list(goldPlate, Enum.FillDirection.Horizontal, 0.03)
	Ui.coin(goldPlate, UDim2.fromScale(0.14, 0.8))
	local gold = Ui.text(goldPlate, "Amount", UDim2.fromScale(0.5, 1), "display", "OnPanel", 40)
	local delta =
		Ui.text(goldPlate, "Delta", UDim2.fromScale(0.28, 0.8), "display", "Accent", 30, 16)
	delta.TextTransparency = 1

	local stale = Ui.plate(stack, "Reconnecting", UDim2.fromScale(0.7, 0.18), 5.5)
	stale.LayoutOrder = 3
	stale.Visible = false
	Ui.pad(stale, 0.06, 0.15)
	local staleText = Ui.text(stale, "Text", UDim2.fromScale(1, 1), "body", "Muted", 22)
	staleText.Text = "Reconnecting…"

	-- the objective, top centre
	-- wide enough for the longest objective at the 14 px text floor on a phone; capped on big screens
	local pill = Ui.plate(gui, "Objective", UDim2.fromScale(0.5, 0.075), 9.5)
	local pillCap = Instance.new("UISizeConstraint")
	pillCap.MaxSize = Vector2.new(480, 52)
	pillCap.Parent = pill
	pill.AnchorPoint = Vector2.new(0.5, 0)
	pill.Position = UDim2.fromScale(0.5, 0.02)
	Ui.pad(pill, 0.04, 0.18)
	local objective = Ui.text(pill, "Text", UDim2.fromScale(1, 1), "display", "Accent", 30)
	objective.TextXAlignment = Enum.TextXAlignment.Center

	-- the Shop button: right edge, above the jump button, in the right thumb's reach
	local shop =
		Ui.button(gui, "Shop", UDim2.fromScale(0.09, 0.09), "🔑", "Accent", "OnAccent", openShop)
	shop.AnchorPoint = Vector2.new(1, 0.5)
	Ui.aspect(shop, 1)
	local function placeShop()
		local view = (workspace.CurrentCamera :: Camera).ViewportSize
		-- tablets (closer to 4:3) need the button lower for the thumb; phones and desktops at 45%
		shop.Position = UDim2.fromScale(0.985, if view.X / view.Y < 1.5 then 0.55 else 0.45)
	end
	(workspace.CurrentCamera :: Camera):GetPropertyChangedSignal("ViewportSize"):Connect(placeShop)
	placeShop()

	local self = setmetatable({
		player = player,
		gui = gui,
		level = level,
		xpFill = xpFill,
		gold = gold,
		delta = delta,
		objective = objective,
		shop = shop,
		stale = stale,
		shown = nil,
		shownLevel = nil,
	}, Hud)
	for _, name in { Net.GOLD, Net.LEVEL, Net.XP, Net.HAS_KEY } do
		player:GetAttributeChangedSignal(name):Connect(function()
			self:render()
		end)
	end
	self:render()
	task.spawn(function()
		while true do -- the HUD lives all session (ResetOnSpawn = false)
			task.wait(1)
			local beat = player:GetAttribute(Net.HEARTBEAT)
			stale.Visible = typeof(beat) == "number"
				and workspace:GetServerTimeNow() - beat > STALE_SECONDS
		end
	end)
	gui.Parent = player:WaitForChild("PlayerGui")
	return self
end

function Hud.render(self: Hud)
	local gold = self.player:GetAttribute(Net.GOLD)
	local level = self.player:GetAttribute(Net.LEVEL)
	local xp = self.player:GetAttribute(Net.XP)
	local owned = self.player:GetAttribute(Net.HAS_KEY) == true
	if typeof(gold) ~= "number" or typeof(level) ~= "number" or typeof(xp) ~= "number" then
		-- Loading: the plates are up, the numbers wait for the server
		self.level.Text, self.gold.Text, self.objective.Text = "LVL …", "…", "…"
		self.xpFill.Size = UDim2.fromScale(0, 1)
		return
	end
	self.level.Text = `LVL {level}`
	if self.shownLevel and level > self.shownLevel then
		Juice.flash(self.level, "Accent", "Level", 1.5) -- the brief: the badge flashes for 1.5 s
	end
	self.shownLevel = level
	local fraction = if level >= Progress.FARM_CAP then 1 else xp / Progress.xpToNext(level)
	TweenService:Create(self.xpFill, TweenInfo.new(0.25), { Size = UDim2.fromScale(fraction, 1) })
		:Play()

	if self.shown and gold > self.shown then
		self.delta.Text = Gold.delta(gold - self.shown)
		self.delta.TextTransparency = 0
		TweenService:Create(
			self.delta,
			TweenInfo.new(DELTA_SECONDS, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
			{ TextTransparency = 1 }
		):Play()
		Ui.sound(COIN)
	end
	-- the brief: gold counts up when it rises
	Juice.tick(self.gold, self.shown or gold, gold, Gold.short)
	self.shown = gold

	local locked = level < KeyOffer.UNLOCK_LEVEL
	if owned then
		self.objective.Text = "Enter the dungeon"
		Ui.tone(self.objective, "Text", "Accent")
	elseif locked then
		self.objective.Text = `🔒 Reach LVL {KeyOffer.UNLOCK_LEVEL}`
		Ui.tone(self.objective, "Text", "Muted")
	else
		self.objective.Text = `Buy the dungeon key · {Gold.format(KeyOffer.PRICE)}`
		Ui.tone(self.objective, "Text", "Accent")
	end
	self.shop.Text = if locked then "🔒" else "🔑"
	Ui.enable(
		self.shop,
		true,
		if locked then "Disabled" else "Accent",
		if locked then "OnDisabled" else "OnAccent"
	)
end

return Hud
