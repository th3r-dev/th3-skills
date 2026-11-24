--!strict
-- The layout lint's rules, on plain rectangles so Lune can test them. client/LayoutLint turns the
-- live ScreenGuis into these nodes. Each rule is a defect a game built with this skill shipped and
-- its owner found by eye: plates overlapping, a sheet whose body had no height, labels wider than
-- their buttons, 10 px counts, an 18 px icon half under its keycap.

local LayoutRules = {}

LayoutRules.MIN_TEXT = 14 -- px
LayoutRules.MIN_ICON = 0.6 -- an icon's shorter side, as a share of its button's shorter side

export type Node = {
	path: string, -- full name, also the identity used for ancestry
	x: number,
	y: number,
	w: number,
	h: number,
	ancestors: { string }, -- paths of every GuiObject above it
	text: number?, -- rendered text height in px, for text
	textWidth: number?, -- rendered text width in px, for text
	iconOf: string?, -- the path of the button an image sits in
	hasChildren: boolean?,
	free: boolean?, -- may overlap anything (a backdrop, a toast); set with the LintFree attribute
}

export type Finding = { rule: string, path: string, detail: string }

local function overlap(a: Node, b: Node): boolean
	local TOUCH = 1 -- px: edges that touch are not an overlap
	return a.x + a.w - TOUCH > b.x
		and b.x + b.w - TOUCH > a.x
		and a.y + a.h - TOUCH > b.y
		and b.y + b.h - TOUCH > a.y
end

local function related(a: Node, b: Node): boolean
	return table.find(a.ancestors, b.path) ~= nil or table.find(b.ancestors, a.path) ~= nil
end

function LayoutRules.check(nodes: { Node }): { Finding }
	local found: { Finding } = {}
	local byPath: { [string]: Node } = {}
	for _, n in nodes do
		byPath[n.path] = n
	end
	local function add(rule: string, path: string, detail: string)
		table.insert(found, { rule = rule, path = path, detail = detail })
	end

	for _, n in nodes do
		if n.hasChildren and (n.w < 1 or n.h < 1) then
			add("zero", n.path, `{n.w}x{n.h} with content inside`)
		end
		if n.text and n.text < LayoutRules.MIN_TEXT then
			add("small-text", n.path, `{n.text} px < {LayoutRules.MIN_TEXT}`)
		end
		if n.textWidth and n.textWidth > n.w + 1 then
			add("text-overflow", n.path, `text {n.textWidth} px in a {n.w} px box`)
		end
		local button = if n.iconOf then byPath[n.iconOf] else nil
		if button then
			local need = LayoutRules.MIN_ICON * math.min(button.w, button.h)
			if math.min(n.w, n.h) < need then
				add("small-icon", n.path, `{math.min(n.w, n.h)} px < {math.floor(need)} px`)
			end
		end
	end

	-- ponytail: every pair, O(n²); a HUD has tens of nodes. Sweep by x if a screen reaches thousands.
	for i = 1, #nodes do
		local a = nodes[i]
		for j = i + 1, #nodes do
			local b = nodes[j]
			if not a.free and not b.free and not related(a, b) and overlap(a, b) then
				add("overlap", a.path, `overlaps {b.path}`)
			end
		end
	end
	return found
end

function LayoutRules.line(f: Finding): string
	return `LINT {f.rule} {f.path}: {f.detail}`
end

return LayoutRules
