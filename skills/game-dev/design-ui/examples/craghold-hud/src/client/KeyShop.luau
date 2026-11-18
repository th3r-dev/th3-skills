--!strict
-- The key shop from design/features/key-shop/design.md. KeyOffer.view decides what every state
-- shows; this file only draws it. Buying asks the server and waits: the client never grants the key.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Gold = require("@game/ReplicatedStorage/Shared/Gold")
local KeyOffer = require("@game/ReplicatedStorage/Shared/KeyOffer")
local Net = require("@game/ReplicatedStorage/Shared/Net")
local Ui = require("./Ui")

local TIMEOUT_SECONDS = 10
local GOT_IT = "rbxasset://sounds/electronicpingshort.wav"

local KeyShop = {}
KeyShop.__index = KeyShop

export type KeyShop = typeof(setmetatable(
	{} :: {
		player: Player,
		gui: ScreenGui,
		dim: ScreenGui,
		dialog: Frame,
		icon: TextLabel,
		price: TextLabel,
		have: TextLabel,
		buy: TextButton,
		spinner: Frame,
		note: TextLabel,
		pending: boolean,
		failed: boolean,
	},
	KeyShop
))

function KeyShop.new(player: Player): KeyShop
	local gui = Instance.new("ScreenGui")
	gui.Name = "KeyShop"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 10 -- above the HUD
	gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
	gui.Enabled = false

	-- the dim goes edge to edge on its own ScreenGui (no insets); the dialog stays inside the safe
	-- insets on `gui`. One gui for both left undimmed bands at the top and sides (found in the playtest).
	local dim = Instance.new("ScreenGui")
	dim.Name = "KeyShopDim"
	dim.ResetOnSpawn = false
	dim.DisplayOrder = 9
	dim.ScreenInsets = Enum.ScreenInsets.None
	dim.Enabled = false

	local self: KeyShop
	local backdrop = Instance.new("TextButton")
	backdrop.Name = "Backdrop"
	backdrop.Size = UDim2.fromScale(1, 1)
	backdrop.Text = ""
	backdrop.AutoButtonColor = false
	backdrop.BorderSizePixel = 0
	Ui.tone(backdrop, "Fill", "Backdrop")
	backdrop.BackgroundTransparency = 0.5
	backdrop.Parent = dim

	local dialog = Ui.plate(gui, "Dialog", UDim2.fromScale(0.8, 0.6), 4 / 3)
	dialog.AnchorPoint = Vector2.new(0.5, 0.5)
	dialog.Position = UDim2.fromScale(0.5, 0.5)
	local cap = Instance.new("UISizeConstraint")
	cap.MaxSize = Vector2.new(520, 390)
	cap.Parent = dialog

	local body = Ui.frame(dialog, "Body", UDim2.fromScale(1, 1))
	Ui.pad(body, 0.08, 0.07)
	Ui.list(body, Enum.FillDirection.Vertical, 0.025, Enum.HorizontalAlignment.Center)
	local icon = Ui.text(body, "Icon", UDim2.fromScale(0.3, 0.26), "display", "Accent", 90)
	icon.TextXAlignment = Enum.TextXAlignment.Center
	icon.LayoutOrder = 1
	local title = Ui.text(body, "Title", UDim2.fromScale(1, 0.12), "display", "OnPanel", 34)
	title.Text = "Dungeon key"
	title.TextXAlignment = Enum.TextXAlignment.Center
	title.LayoutOrder = 2
	local priceRow = Ui.frame(body, "PriceRow", UDim2.fromScale(1, 0.13))
	priceRow.LayoutOrder = 3
	Ui.list(priceRow, Enum.FillDirection.Horizontal, 0.02, Enum.HorizontalAlignment.Center)
	Ui.coin(priceRow, UDim2.fromScale(0.1, 0.85))
	local price = Ui.text(priceRow, "Price", UDim2.fromScale(0.4, 1), "display", "Accent", 40)
	price.TextXAlignment = Enum.TextXAlignment.Left
	local have = Ui.text(body, "Have", UDim2.fromScale(1, 0.09), "body", "Muted", 26)
	have.TextXAlignment = Enum.TextXAlignment.Center
	have.LayoutOrder = 4
	local buy = Ui.button(
		body,
		"Buy",
		UDim2.fromScale(1, 0.16),
		"Buy key",
		"Accent",
		"OnAccent",
		function()
			self:purchase()
		end
	)
	buy.LayoutOrder = 5
	local spinner = Ui.spinner(buy, UDim2.fromScale(0.6, 0.6))
	local note = Ui.text(body, "Note", UDim2.fromScale(1, 0.08), "body", "PriceShort", 24, 15)
	note.TextXAlignment = Enum.TextXAlignment.Center
	note.LayoutOrder = 6

	-- the close button sits on the dialog's top-right corner (Roblox's convention: red square, white X)
	local close = Ui.button(
		dialog,
		"Close",
		UDim2.fromScale(0.13, 0.13),
		"X",
		"Danger",
		"OnDanger",
		function()
			self:close()
		end
	)
	close.AnchorPoint = Vector2.new(0.5, 0.5)
	close.Position = UDim2.fromScale(1, 0)
	Ui.aspect(close, 1)

	self = setmetatable({
		player = player,
		gui = gui,
		dim = dim,
		dialog = dialog,
		icon = icon,
		price = price,
		have = have,
		buy = buy,
		spinner = spinner,
		note = note,
		pending = false,
		failed = false,
	}, KeyShop)
	backdrop.Activated:Connect(function()
		self:close()
	end)
	UserInputService.InputBegan:Connect(function(input, processed)
		if processed then
			return
		end
		-- Escape is Roblox's own menu (it arrives already processed), so B toggles the shop instead
		if input.KeyCode == Enum.KeyCode.B then
			if gui.Enabled then
				self:close()
			else
				self:open()
			end
		end
	end)
	for _, name in { Net.GOLD, Net.LEVEL, Net.HAS_KEY } do
		player:GetAttributeChangedSignal(name):Connect(function()
			self:render()
		end)
	end
	local playerGui = player:WaitForChild("PlayerGui")
	dim.Parent = playerGui
	gui.Parent = playerGui
	return self
end

function KeyShop.open(self: KeyShop)
	self.failed = false
	self:render()
	self.dim.Enabled = true
	self.gui.Enabled = true
end

function KeyShop.close(self: KeyShop)
	self.gui.Enabled = false
	self.dim.Enabled = false
end

function KeyShop.render(self: KeyShop)
	local gold = self.player:GetAttribute(Net.GOLD)
	local level = self.player:GetAttribute(Net.LEVEL)
	local view = KeyOffer.view({
		gold = if typeof(gold) == "number" then gold else 0,
		level = if typeof(level) == "number" then level else 0,
		owned = self.player:GetAttribute(Net.HAS_KEY) == true,
		pending = self.pending,
		failed = self.failed,
	})
	self.icon.Text = if view.state == "locked"
		then "🔒"
		elseif view.state == "owned" then "✅"
		else "🔑"
	self.price.Text = view.price
	Ui.tone(self.price, "Text", view.priceToken)
	self.have.Text = `You have {Gold.short(if typeof(gold) == "number" then gold else 0)}`
	self.buy.Text = view.button
	Ui.enable(self.buy, view.enabled)
	self.spinner.Visible = view.state == "loading"
	self.note.Text = view.note or ""
	Ui.tone(self.note, "Text", if view.state == "error" then "PriceShort" else "Muted")
end

function KeyShop.purchase(self: KeyShop)
	if self.pending then
		return
	end
	self.pending, self.failed = true, false
	self:render()
	local remote = ReplicatedStorage:WaitForChild(Net.BUY_KEY) :: RemoteFunction
	local done = false
	task.delay(TIMEOUT_SECONDS, function()
		if not done then
			done = true
			self.pending, self.failed = false, true
			self:render()
		end
	end)
	task.spawn(function()
		local ok, result = pcall(function()
			return remote:InvokeServer()
		end)
		if done then
			return
		end
		done = true
		self.pending = false
		self.failed = not (ok and result == true)
		if not self.failed then
			Ui.sound(GOT_IT)
		end
		self:render()
	end)
end

return KeyShop
