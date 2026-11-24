--!strict
-- Settings from design/features/settings/design.md: effects level, music and sound volume. Every
-- change applies at once (Juice and the SoundGroups), then saves: the client sends the whole table
-- at most once a second, the server cleans it with Settings.validate and answers. The values the
-- panel starts from are the server's copy, published as a JSON attribute.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local UserInputService = game:GetService("UserInputService")

local Net = require("@game/ReplicatedStorage/Shared/Net")
local Settings = require("@game/ReplicatedStorage/Shared/Settings")
local Juice = require("./Juice")
local Ui = require("./Ui")

local SAVE_GAP = 1 -- seconds between saves; changes inside it go in the next one
local SAMPLE = "rbxasset://sounds/electronicpingshort.wav"
local LEVELS: { Settings.Level } = { "Full", "Reduced", "Off" }

local SettingsPanel = {}
SettingsPanel.__index = SettingsPanel

export type SettingsPanel = typeof(setmetatable(
	{} :: {
		player: Player,
		gui: ScreenGui,
		dim: ScreenGui,
		dialog: Frame,
		values: Settings.Settings,
		ready: boolean,
		segments: { [Settings.Level]: TextButton },
		device: TextLabel,
		sliders: { [string]: (number) -> () },
		note: TextLabel,
		dirty: boolean,
		saving: boolean,
	},
	SettingsPanel
))

local function group(name: string): SoundGroup
	return SoundService:WaitForChild(name) :: SoundGroup
end

-- A label on the left, the control's frame on the right; returns the control's frame.
local function row(body: Instance, order: number, label: string): Frame
	local r = Ui.frame(body, label, UDim2.fromScale(1, 0.18))
	r.LayoutOrder = order
	Ui.list(r, Enum.FillDirection.Horizontal, 0.03)
	local t = Ui.text(r, "Label", UDim2.fromScale(0.28, 1), "body", "OnPanel", 28)
	t.Text = label
	return Ui.frame(r, "Control", UDim2.fromScale(0.69, 1))
end

function SettingsPanel.new(player: Player): SettingsPanel
	local gui = Instance.new("ScreenGui")
	gui.Name = "Settings"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 12 -- above the HUD and the shop
	gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
	gui.Enabled = false
	gui:SetAttribute("Modal", true)

	local dim = Instance.new("ScreenGui")
	dim.Name = "SettingsDim"
	dim.ResetOnSpawn = false
	dim.DisplayOrder = 11
	dim.ScreenInsets = Enum.ScreenInsets.None
	dim.Enabled = false
	local backdrop = Instance.new("TextButton")
	backdrop.Name = "Backdrop"
	backdrop.Size = UDim2.fromScale(1, 1)
	backdrop.Text = ""
	backdrop.AutoButtonColor = false
	backdrop.BorderSizePixel = 0
	backdrop:SetAttribute("LintFree", true)
	Ui.tone(backdrop, "Fill", "Backdrop")
	backdrop.BackgroundTransparency = 0.5
	backdrop.Parent = dim

	-- wide, not 4:3: on a 667×375 phone the rows then clear the 44 px tap floor and "Reduced" fits
	-- its segment at the 16 px button text floor (worked out on paper; the Studio lint confirms)
	local dialog = Ui.plate(gui, "Dialog", UDim2.fromScale(0.9, 0.9), 1.8)
	dialog.AnchorPoint = Vector2.new(0.5, 0.5)
	dialog.Position = UDim2.fromScale(0.5, 0.5)
	local cap = Instance.new("UISizeConstraint")
	cap.MaxSize = Vector2.new(560, 320)
	cap.Parent = dialog

	local body = Ui.frame(dialog, "Body", UDim2.fromScale(1, 1))
	Ui.pad(body, 0.07, 0.07)
	Ui.list(body, Enum.FillDirection.Vertical, 0.03, Enum.HorizontalAlignment.Center)
	local title = Ui.text(body, "Title", UDim2.fromScale(1, 0.11), "display", "OnPanel", 34)
	title.Text = "Settings"
	title.TextXAlignment = Enum.TextXAlignment.Center
	title.LayoutOrder = 1

	local self: SettingsPanel
	local values = Settings.validate(nil)

	-- Effects: three segments, the chosen level filled with Accent
	local effects = row(body, 2, "Effects")
	Ui.list(effects, Enum.FillDirection.Horizontal, 0.03)
	local segments = {}
	for i, level in LEVELS do
		local b = Ui.button(
			effects,
			level,
			UDim2.fromScale(0.32, 1),
			level,
			"Disabled",
			"OnDisabled",
			function()
				self:change("effects", level)
			end
		)
		b.LayoutOrder = i
		segments[level] = b
	end
	local device = Ui.text(body, "Device", UDim2.fromScale(1, 0.07), "body", "Muted", 22)
	device.Text = "Reduced (your Roblox setting)"
	device.TextXAlignment = Enum.TextXAlignment.Right
	device.LayoutOrder = 3

	-- a slider: tap or drag the track; the knob follows, the coin plays at each tenth
	local sliders = {}
	local function slider(order: number, label: string, key: string)
		local control = row(body, order, label)
		local track = Instance.new("TextButton")
		track.Name = "Track"
		track.Text = ""
		track.AutoButtonColor = false
		track.BorderSizePixel = 0
		track.Size = UDim2.fromScale(1, 0.4)
		track.AnchorPoint = Vector2.new(0, 0.5)
		track.Position = UDim2.fromScale(0, 0.5)
		Ui.tone(track, "Fill", "Disabled")
		Ui.corner(track, 8)
		track.Parent = control
		local fill = Ui.frame(track, "Fill", UDim2.fromScale(0, 1), "Accent")
		Ui.corner(fill, 8)
		local knob = Ui.frame(track, "Knob", UDim2.fromScale(0, 1.8), "OnPanel")
		knob.AnchorPoint = Vector2.new(0.5, 0.5)
		knob.Position = UDim2.fromScale(0, 0.5)
		Ui.aspect(knob, 1)
		local round = Instance.new("UICorner")
		round.CornerRadius = UDim.new(0.5, 0)
		round.Parent = knob
		Ui.outline(knob)

		local function show(v: number)
			fill.Size = UDim2.fromScale(v / 100, 1)
			knob.Position = UDim2.fromScale(v / 100, 0.5)
		end
		sliders[key] = show
		local dragging = false
		local function at(x: number)
			local v = math.clamp((x - track.AbsolutePosition.X) / track.AbsoluteSize.X, 0, 1) * 100
			local before = (self.values :: any)[key]
			self:change(key, v)
			local now = (self.values :: any)[key]
			if math.floor(now / 10) ~= math.floor(before / 10) then
				Ui.sound(SAMPLE)
			end
		end
		track.InputBegan:Connect(function(input)
			local t = input.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				dragging = true
				at(input.Position.X)
			end
		end)
		UserInputService.InputChanged:Connect(function(input)
			local t = input.UserInputType
			if
				dragging
				and (t == Enum.UserInputType.MouseMovement or t == Enum.UserInputType.Touch)
			then
				at(input.Position.X)
			end
		end)
		UserInputService.InputEnded:Connect(function(input)
			local t = input.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				dragging = false
			end
		end)
		-- ponytail: touch and mouse only; a gamepad needs left/right on the selected track
	end
	slider(4, "Music", "music")
	slider(5, "Sound effects", "sound")

	local note = Ui.text(body, "Note", UDim2.fromScale(1, 0.07), "body", "Muted", 22, 15)
	note.TextXAlignment = Enum.TextXAlignment.Center
	note.LayoutOrder = 6

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
		values = values,
		ready = false,
		segments = segments,
		device = device,
		sliders = sliders,
		note = note,
		dirty = false,
		saving = false,
	}, SettingsPanel)
	backdrop.Activated:Connect(function()
		self:close()
	end)

	-- the server's copy: until it arrives the rows show the defaults, greyed (Loading)
	local function load()
		local raw = player:GetAttribute(Net.SETTINGS)
		if typeof(raw) ~= "string" then
			return
		end
		local ok, decoded = pcall(HttpService.JSONDecode, HttpService, raw)
		self.values = Settings.validate(if ok then decoded else nil)
		self.ready = true
		self:apply()
	end
	player:GetAttributeChangedSignal(Net.SETTINGS):Connect(function()
		if not self.ready then
			load()
		end
	end)
	load()
	self:apply()

	local playerGui = player:WaitForChild("PlayerGui")
	dim.Parent = playerGui
	gui.Parent = playerGui
	return self
end

-- Puts the current values into effect and onto the controls.
function SettingsPanel.apply(self: SettingsPanel)
	local v = self.values
	Juice.set(v)
	group("Music").Volume = v.music / 100
	group("Effects").Volume = v.sound / 100
	local level = Juice.level()
	for name, b in self.segments do
		local on = self.ready and name == level -- Loading: every segment greyed
		Ui.tone(b, "Fill", if on then "Accent" else "Disabled")
		Ui.tone(b, "Text", if on then "OnAccent" else "OnDisabled")
		b.Active = self.ready
	end
	self.device.Visible = v.effects == "Auto" and level == "Reduced"
	for key, show in self.sliders do
		show((v :: any)[key])
	end
end

function SettingsPanel.change(self: SettingsPanel, key: string, value: any)
	if not self.ready then
		return
	end
	local raw = table.clone(self.values) :: any
	raw[key] = value
	self.values = Settings.validate(raw)
	self:apply()
	self.dirty = true
	self:save()
end

-- One save in flight at a time, at most once a second; the latest values always go out.
function SettingsPanel.save(self: SettingsPanel)
	if self.saving then
		return
	end
	self.saving = true
	task.spawn(function()
		while self.dirty do
			self.dirty = false
			local remote = ReplicatedStorage:WaitForChild(Net.SAVE_SETTINGS) :: RemoteFunction
			local ok, saved = pcall(remote.InvokeServer, remote, self.values)
			self.note.Text = if ok and saved == true
				then ""
				else "Couldn't save. Your settings work this session."
			task.wait(SAVE_GAP)
		end
		self.saving = false
	end)
end

function SettingsPanel.open(self: SettingsPanel)
	self.dim.Enabled = true
	self.gui.Enabled = true
	Juice.pop(self.dialog)
end

function SettingsPanel.close(self: SettingsPanel)
	self.gui.Enabled = false
	self.dim.Enabled = false
end

function SettingsPanel.toggle(self: SettingsPanel)
	if self.gui.Enabled then
		self:close()
	else
		self:open()
	end
end

return SettingsPanel
