--!strict
-- The factory every surface builds from: plates, text and buttons sized in Scale only (every Offset
-- is 0), shaped by aspect constraints, coloured by Theme tags, with press feedback on buttons.

local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")

local Theme = require("./Theme")
local Tokens = require("@game/ReplicatedStorage/Shared/Tokens")

local Ui = {}

local CLICK = "rbxasset://sounds/clickfast.wav"
local QUICK = TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

-- Colours an instance from a token: "Text" sets TextColor3, "Fill" the background (opaque), "Stroke"
-- a UIStroke's colour. The one place a colour is applied; the token name is kept as an attribute.
function Ui.tone(inst: Instance, prefix: "Text" | "Fill" | "Stroke", token: string)
	local c = Theme.color(token)
	if prefix == "Text" then
		(inst :: any).TextColor3 = c
	elseif prefix == "Fill" then
		(inst :: any).BackgroundColor3 = c;
		(inst :: any).BackgroundTransparency = 0
	else
		(inst :: UIStroke).Color = c
	end
	inst:SetAttribute(prefix .. "Token", token)
end

function Ui.aspect(inst: Instance, ratio: number)
	local c = Instance.new("UIAspectRatioConstraint")
	c.AspectRatio = ratio
	c.Parent = inst
end

function Ui.corner(inst: Instance, px: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, px) -- a radius is a token in px; it is a shape, not a position
	c.Parent = inst
end

function Ui.outline(inst: Instance)
	local s = Instance.new("UIStroke")
	s.Thickness = Tokens.outline
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = inst
	Ui.tone(s, "Stroke", "Outline")
end

function Ui.list(
	inst: Instance,
	dir: Enum.FillDirection,
	gap: number,
	align: Enum.HorizontalAlignment?
)
	local l = Instance.new("UIListLayout")
	l.FillDirection = dir
	l.Padding = UDim.new(gap, 0)
	l.SortOrder = Enum.SortOrder.LayoutOrder
	l.HorizontalAlignment = align or Enum.HorizontalAlignment.Left
	l.VerticalAlignment = Enum.VerticalAlignment.Center
	l.Parent = inst
	return l
end

function Ui.pad(inst: Instance, x: number, y: number)
	local p = Instance.new("UIPadding")
	p.PaddingLeft, p.PaddingRight = UDim.new(x, 0), UDim.new(x, 0)
	p.PaddingTop, p.PaddingBottom = UDim.new(y, 0), UDim.new(y, 0)
	p.Parent = inst
end

function Ui.frame(parent: Instance, name: string, size: UDim2, fill: string?): Frame
	local f = Instance.new("Frame")
	f.Name = name
	f.Size = size
	f.BorderSizePixel = 0
	f.BackgroundTransparency = 1
	if fill then
		Ui.tone(f, "Fill", fill)
	end
	f.Parent = parent
	return f
end

-- A rounded, outlined plate: the surface every text sits on (Tokens.Panel unless told otherwise).
function Ui.plate(
	parent: Instance,
	name: string,
	size: UDim2,
	aspect: number?,
	fill: string?
): Frame
	local f = Ui.frame(parent, name, size, fill or "Panel")
	Ui.corner(f, Tokens.radius.plate)
	Ui.outline(f)
	if aspect then
		Ui.aspect(f, aspect)
	end
	return f
end

-- TextScaled between a floor and a ceiling: the floor (14 px unless told) keeps secondary lines
-- readable on a phone, where Scale alone shrank them to about 8 px (the review found it).
function Ui.text(
	parent: Instance,
	name: string,
	size: UDim2,
	kind: "display" | "body",
	tone: string,
	maxSize: number,
	minSize: number?
): TextLabel
	local t = Instance.new("TextLabel")
	t.Name = name
	t.Size = size
	t.BackgroundTransparency = 1
	t.FontFace = Theme.font(kind)
	t.TextScaled = true
	t.TextXAlignment = Enum.TextXAlignment.Left
	local c = Instance.new("UITextSizeConstraint")
	c.MaxTextSize = maxSize
	c.MinTextSize = math.min(minSize or 14, maxSize)
	c.Parent = t
	Ui.tone(t, "Text", tone)
	t.Parent = parent
	return t
end

-- A button with a floor at Tokens.minTap px, a press scale and a click; `onClick` runs only when
-- the button is Active.
function Ui.button(
	parent: Instance,
	name: string,
	size: UDim2,
	label: string,
	fill: string,
	tone: string,
	onClick: () -> ()
): TextButton
	local b = Instance.new("TextButton")
	b.Name = name
	b.Size = size
	b.AutoButtonColor = false
	b.Text = label
	b.FontFace = Theme.font("display")
	b.TextScaled = true
	b.BorderSizePixel = 0
	Ui.tone(b, "Fill", fill)
	Ui.tone(b, "Text", tone)
	Ui.corner(b, Tokens.radius.button)
	Ui.outline(b)
	local floor = Instance.new("UISizeConstraint")
	floor.MinSize = Vector2.new(Tokens.minTap, Tokens.minTap)
	floor.Parent = b
	local textMax = Instance.new("UITextSizeConstraint")
	textMax.MaxTextSize = 32
	textMax.MinTextSize = 16
	textMax.Parent = b
	local pad = Instance.new("UIPadding")
	pad.PaddingTop, pad.PaddingBottom = UDim.new(0.18, 0), UDim.new(0.18, 0)
	pad.PaddingLeft, pad.PaddingRight = UDim.new(0.06, 0), UDim.new(0.06, 0)
	pad.Parent = b
	local scale = Instance.new("UIScale")
	scale.Parent = b
	local function to(v: number)
		TweenService:Create(scale, QUICK, { Scale = v }):Play()
	end
	b.MouseEnter:Connect(function()
		if b.Active then
			to(1.05)
		end
	end)
	b.MouseLeave:Connect(function()
		to(1)
	end)
	b.MouseButton1Down:Connect(function()
		if b.Active then
			to(0.94)
		end
	end)
	b.MouseButton1Up:Connect(function()
		to(1)
	end)
	b.Activated:Connect(function()
		if b.Active then
			Ui.sound(CLICK)
			onClick()
		end
	end)
	b.Parent = parent
	return b
end

-- Enables or disables a button and gives it the matching fill and text tones.
function Ui.enable(b: TextButton, on: boolean, fill: string?, tone: string?)
	b.Active = on
	Ui.tone(b, "Fill", if on then fill or "Accent" else "Disabled")
	Ui.tone(b, "Text", if on then tone or "OnAccent" else "OnDisabled")
end

-- A spinner for a button's loading state: a ring whose stroke fades along a gradient, turning.
-- Hidden until shown with .Visible.
function Ui.spinner(parent: Instance, size: UDim2): Frame
	local ring = Ui.frame(parent, "Spinner", size)
	ring.AnchorPoint = Vector2.new(0, 0.5)
	ring.Position = UDim2.fromScale(0.04, 0.5)
	Ui.aspect(ring, 1)
	local round = Instance.new("UICorner")
	round.CornerRadius = UDim.new(0.5, 0)
	round.Parent = ring
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 3
	stroke.Parent = ring
	Ui.tone(stroke, "Stroke", "OnPanel") -- cream: the review found OnDisabled too faint on a disabled button
	local fade = Instance.new("UIGradient")
	fade.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.5, 0.2),
		NumberSequenceKeypoint.new(1, 1),
	})
	fade.Parent = stroke
	local turn = TweenService:Create(
		fade,
		TweenInfo.new(0.8, Enum.EasingStyle.Linear, Enum.EasingDirection.In, -1),
		{ Rotation = 360 }
	)
	ring:GetPropertyChangedSignal("Visible"):Connect(function()
		if ring.Visible then
			turn:Play()
		else
			turn:Cancel()
		end
	end)
	ring.Visible = false
	return ring
end

-- A drawn coin (a circle in Accent with the outline), not an emoji: emoji glyphs are missing on
-- some platforms (the coin emoji rendered as an empty box in Studio).
function Ui.coin(parent: Instance, size: UDim2): Frame
	local c = Ui.frame(parent, "Coin", size, "Accent")
	local round = Instance.new("UICorner")
	round.CornerRadius = UDim.new(0.5, 0)
	round.Parent = c
	Ui.outline(c)
	Ui.aspect(c, 1)
	local shine = Ui.frame(c, "Shine", UDim2.fromScale(0.5, 0.5), "OnPanel")
	shine.AnchorPoint = Vector2.new(0.5, 0.5)
	shine.Position = UDim2.fromScale(0.5, 0.5)
	shine.BackgroundTransparency = 0.6
	local inner = Instance.new("UICorner")
	inner.CornerRadius = UDim.new(0.5, 0)
	inner.Parent = shine
	return c
end

function Ui.sound(id: string)
	local s = Instance.new("Sound")
	s.SoundId = id
	s.Volume = 0.5
	s.SoundGroup = SoundService:FindFirstChild("Effects") :: SoundGroup? -- the Settings slider's group
	SoundService:PlayLocalSound(s)
	s:Destroy()
end

return Ui
