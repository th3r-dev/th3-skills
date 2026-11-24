--!strict
-- The UI's motion in one place (references/juice.md). Every recipe reads the effects level from the
-- player's settings and falls back to an instant change below its level, so one Settings switch
-- reaches every effect. Only the recipes this game uses are here: tick-up, pop and flash.

local GuiService = game:GetService("GuiService")
local TweenService = game:GetService("TweenService")

local Count = require("@game/ReplicatedStorage/Shared/Count")
local Settings = require("@game/ReplicatedStorage/Shared/Settings")
local Ui = require("./Ui")

local Juice = {}

local current: Settings.Settings = Settings.validate(nil)
local ticking: { [TextLabel]: number } = setmetatable({}, { __mode = "k" }) :: any

-- The Settings panel hands its validated table here.
function Juice.set(s: Settings.Settings)
	current = s
end

function Juice.level(): Settings.Level
	-- ReducedMotionEnabled mirrors the player's Roblox Reduce Motion toggle (hidden in the class
	-- list, readable by scripts); a read that errors counts as off
	local ok, reduced = pcall(function()
		return GuiService.ReducedMotionEnabled
	end)
	return Settings.level(current, ok and reduced == true)
end

-- A rising counter steps up to its new value over about 0.4 s. A newer rise replaces an older one.
function Juice.tick(label: TextLabel, from: number, to: number, format: (number) -> string)
	local run = (ticking[label] or 0) + 1
	ticking[label] = run
	if to <= from or not Settings.allows(Juice.level(), "Reduced") then
		label.Text = format(to)
		return
	end
	task.spawn(function()
		for _, v in Count.steps(from, to, 10) do
			if ticking[label] ~= run then
				return
			end
			label.Text = format(v)
			task.wait(0.04)
		end
	end)
end

local function scaleOf(inst: GuiObject): UIScale
	local s = inst:FindFirstChild("JuiceScale")
	if s and s:IsA("UIScale") then
		return s
	end
	local made = Instance.new("UIScale")
	made.Name = "JuiceScale"
	made.Parent = inst
	return made
end

-- A bounce: small, past full size, back (Back easing). Below Full it just shows at full size.
function Juice.pop(inst: GuiObject)
	if not Settings.allows(Juice.level(), "Full") then
		return
	end
	local s = scaleOf(inst)
	s.Scale = 0.6
	TweenService:Create(s, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
		Scale = 1,
	}):Play()
end

-- Recolours text for `seconds`, then back: a state change, so it shows at every level. The pop
-- on top of it is motion and follows the level.
function Juice.flash(label: TextLabel, token: string, back: string, seconds: number)
	Ui.tone(label, "Text", token)
	Juice.pop(label)
	task.delay(seconds, function()
		Ui.tone(label, "Text", back)
	end)
end

return Juice
