--!strict
-- Reads the live ScreenGuis into LayoutRules nodes and prints one `LINT <rule> <path>: <detail>`
-- line per finding. Runs by itself in Studio a few seconds after the HUD is up; a playtest can also
-- call LayoutLint.run() through execute_luau (Client) after forcing a state, and read the output log.
-- Only what the player sees counts: a filled frame, text with characters, an image.

local Players = game:GetService("Players")

local LayoutRules = require("@game/ReplicatedStorage/Shared/LayoutRules")

local LayoutLint = {}

local function shown(g: GuiObject, gui: ScreenGui): boolean
	local at: Instance? = g
	while at and at ~= gui do
		if at:IsA("GuiObject") and not at.Visible then
			return false
		end
		at = at.Parent
	end
	return true
end

local function seen(g: GuiObject): boolean
	if g:IsA("TextLabel") or g:IsA("TextButton") then
		return (g.Text ~= "" and g.TextTransparency < 1) or g.BackgroundTransparency < 1
	elseif g:IsA("ImageLabel") or g:IsA("ImageButton") then
		return g.Image ~= "" or g.BackgroundTransparency < 1
	end
	return g.BackgroundTransparency < 1
end

function LayoutLint.nodes(): { LayoutRules.Node }
	local out: { LayoutRules.Node } = {}
	local guis = Players.LocalPlayer:WaitForChild("PlayerGui"):GetChildren()
	-- an open modal (a ScreenGui with the Modal attribute) covers everything below it on purpose:
	-- lint only the modal and what sits above it
	local floor = -math.huge
	for _, gui in guis do
		if gui:IsA("ScreenGui") and gui.Enabled and gui:GetAttribute("Modal") == true then
			floor = math.max(floor, gui.DisplayOrder)
		end
	end
	for _, gui in guis do
		if not gui:IsA("ScreenGui") or not gui.Enabled or gui.DisplayOrder < floor then
			continue
		end
		for _, d in gui:GetDescendants() do
			if not d:IsA("GuiObject") or not shown(d, gui) then
				continue
			end
			local hasChildren = d:FindFirstChildWhichIsA("GuiObject") ~= nil
			if not seen(d) and not hasChildren then
				continue
			end
			local ancestors = {}
			local button: string? = nil
			local at = d.Parent
			while at and at ~= gui do
				if at:IsA("GuiObject") then
					table.insert(ancestors, at:GetFullName())
					if not button and at:IsA("GuiButton") then
						button = at:GetFullName()
					end
				end
				at = at.Parent
			end
			local n: LayoutRules.Node = {
				path = d:GetFullName(),
				x = d.AbsolutePosition.X,
				y = d.AbsolutePosition.Y,
				w = d.AbsoluteSize.X,
				h = d.AbsoluteSize.Y,
				ancestors = ancestors,
				hasChildren = hasChildren,
				-- a frame that only holds others (no fill) can't overlap anything the player sees
				free = d:GetAttribute("LintFree") == true or not seen(d),
			}
			if (d:IsA("TextLabel") or d:IsA("TextButton")) and d.Text ~= "" then
				-- ponytail: one-line text, so the rendered height is the text size; wrapped text
				-- would need TextBounds / line count
				n.text = d.TextBounds.Y
				n.textWidth = d.TextBounds.X
			end
			if (d:IsA("ImageLabel") or d:IsA("ImageButton")) and button then
				n.iconOf = button
			end
			table.insert(out, n)
		end
	end
	return out
end

function LayoutLint.run(): number
	local found = LayoutRules.check(LayoutLint.nodes())
	for _, f in found do
		print(LayoutRules.line(f))
	end
	print(`LINT done: {#found} finding(s)`)
	return #found
end

return LayoutLint
