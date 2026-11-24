-- Headless tests for the instance-free modules in src/shared, under Lune:
--   lune run tests/run
-- The UI itself (ScreenGuis, tweens, the StyleSheet) is checked in a Studio playtest at three
-- device sizes; see the README. One `FAIL <name>: <error>` line per failure, then a count; exit 1 on any.

local process = require("@lune/process")

local Count = require("../src/shared/Count")
local Gold = require("../src/shared/Gold")
local KeyOffer = require("../src/shared/KeyOffer")
local LayoutRules = require("../src/shared/LayoutRules")
local Progress = require("../src/shared/Progress")
local Settings = require("../src/shared/Settings")
local Tokens = require("../src/shared/Tokens")

local tests: { { name: string, fn: () -> () } } = {}
local function test(name: string, fn: () -> ())
	table.insert(tests, { name = name, fn = fn })
end

local function luminance(hex: string): number
	local function channel(i: number): number
		local c = tonumber(hex:sub(i, i + 1), 16) :: number / 255
		return if c <= 0.03928 then c / 12.92 else ((c + 0.055) / 1.055) ^ 2.4
	end
	return 0.2126 * channel(2) + 0.7152 * channel(4) + 0.0722 * channel(6)
end

local function contrast(a: string, b: string): number
	local la, lb = luminance(a), luminance(b)
	return (math.max(la, lb) + 0.05) / (math.min(la, lb) + 0.05)
end

test("every text token passes 4.5:1 on its plate", function()
	assert(math.abs(contrast("#000000", "#FFFFFF") - 21) < 0.01, "contrast formula")
	for _, pair in Tokens.textPairs do
		local ratio = contrast(Tokens.colors[pair[1]], Tokens.colors[pair[2]])
		assert(ratio >= 4.5, `{pair[1]} on {pair[2]} is {string.format("%.2f", ratio)}:1`)
	end
end)

test("the thumbnail's red stays off text on the panel", function()
	assert(
		contrast(Tokens.colors.Danger, Tokens.colors.Panel) < 4.5,
		"Danger is for fills, PriceShort for text"
	)
end)

test("font weights are Enum.FontWeight names", function()
	-- Studio: `Black is not a valid member of "Enum.FontWeight"` stopped the whole client once
	local weights = {
		"Thin",
		"ExtraLight",
		"Light",
		"Regular",
		"Medium",
		"SemiBold",
		"Bold",
		"ExtraBold",
		"Heavy",
	}
	for kind, f in Tokens.fonts do
		assert(table.find(weights, f.weight), `{kind} weight {f.weight} is not an Enum.FontWeight`)
	end
end)

test("gold reads with thousands separators", function()
	assert(Gold.format(0) == "0")
	assert(Gold.format(999) == "999")
	assert(Gold.format(12500) == "12,500")
	assert(Gold.format(9999999) == "9,999,999")
	assert(Gold.delta(250) == "+250" and Gold.delta(999) == "+999")
	assert(
		Gold.delta(8340) == "+8.3K" and Gold.delta(-1500) == "-1.5K" and Gold.delta(10000) == "+10K"
	)
	assert(Gold.delta(2500000) == "+2.5M")
end)

test("huge gold gets a suffix from 100K, rounded down", function()
	assert(Gold.short(99999) == "99,999", "exact below 100K")
	assert(Gold.short(100000) == "100K" and Gold.short(125400) == "125.4K")
	assert(Gold.short(1000000) == "1M" and Gold.short(9999999) == "9.9M", "never rounds up to 10M")
	assert(Gold.short(1e9) == "1B" and Gold.short(2.5e12) == "2.5T")
	assert(
		Gold.short(3e15) == "3Qa" and Gold.short(1e18) == "1Qi" and Gold.short(-250000) == "-250K"
	)
end)

test("progress levels up and stops at the farm cap", function()
	local p = Progress.new()
	assert(p:add(100) == 1 and p.level == 2 and p.xp == 0)
	assert(math.abs(p:fraction() - 0) < 1e-9)
	p:add(100000)
	assert(p.level == Progress.FARM_CAP and p:fraction() == 1)
	assert(p:add(50) == 0, "no XP past the cap")
end)

test("the key is locked below the farm cap", function()
	local v = KeyOffer.view({ gold = 99999, level = KeyOffer.UNLOCK_LEVEL - 1, owned = false })
	assert(v.state == "locked" and not v.enabled and v.button == "Reach LVL 10")
end)

test("short on gold: red price, the gap on the button", function()
	local v = KeyOffer.view({ gold = 9340, level = 10, owned = false })
	assert(
		v.state == "unaffordable"
			and v.priceToken == "PriceShort"
			and v.button == "Need 3,160 more"
			and not v.enabled
	)
end)

test("enough gold: the button buys", function()
	local v = KeyOffer.view({ gold = 12500, level = 10, owned = false })
	assert(v.state == "affordable" and v.enabled and v.button == "Buy key" and v.price == "12,500")
end)

test("pending, failed and owned", function()
	assert(
		KeyOffer.view({ gold = 13000, level = 10, owned = false, pending = true }).state
			== "loading"
	)
	local failed = KeyOffer.view({ gold = 13000, level = 10, owned = false, failed = true })
	assert(failed.state == "error" and failed.enabled and failed.note == "Couldn't buy. Try again.")
	local owned = KeyOffer.view({ gold = 0, level = 10, owned = true })
	assert(owned.state == "owned" and not owned.enabled and owned.note == "The gate is open")
end)

test("the server's check agrees with the view", function()
	assert(KeyOffer.canBuy(12500, 10, false))
	assert(select(2, KeyOffer.canBuy(12499, 10, false)) == "short")
	assert(select(2, KeyOffer.canBuy(99999, 9, false)) == "locked")
	assert(select(2, KeyOffer.canBuy(99999, 10, true)) == "owned")
end)

test("settings: anything in, valid settings out", function()
	local d = Settings.validate(nil)
	assert(d.music == 60 and d.sound == 80 and d.effects == "Auto")
	local s = Settings.validate({ music = 140, sound = -3, effects = "Full" })
	assert(s.music == 100 and s.sound == 0 and s.effects == "Full")
	local bad = Settings.validate({ music = 0 / 0, sound = "loud", effects = "Max" })
	assert(bad.music == 60 and bad.sound == 80 and bad.effects == "Auto")
	assert(Settings.validate({ music = 33.6 }).music == 34, "rounds to whole numbers")
	assert((Settings.validate({ admin = true }) :: any).admin == nil, "unknown keys dropped")
end)

test("settings: the device's reduced motion counts only on Auto", function()
	local auto = Settings.validate({})
	assert(Settings.level(auto, true) == "Reduced" and Settings.level(auto, false) == "Full")
	assert(Settings.level(Settings.validate({ effects = "Full" }), true) == "Full")
	assert(Settings.level(Settings.validate({ effects = "Off" }), false) == "Off")
	assert(Settings.allows("Full", "Full") and Settings.allows("Reduced", "Reduced"))
	assert(not Settings.allows("Reduced", "Full") and not Settings.allows("Off", "Reduced"))
	assert(Settings.allows("Off", "Off"), "feedback marked Off plays at every level")
end)

test("a counter's steps rise and end exactly on the new value", function()
	for _, case in { { 0, 250 }, { 9340, 12500 }, { 5, 8 }, { 100, 100 }, { 0, 1e9 } } do
		local steps = Count.steps(case[1], case[2], 10)
		assert(steps[#steps] == case[2], `{case[1]}->{case[2]} ends at {steps[#steps]}`)
		assert(#steps <= 10)
		local last = case[1]
		for i, v in steps do
			assert(v == math.floor(v), "whole numbers")
			assert(v > last or (i == #steps and v == case[2]), "always rising")
			last = v
		end
	end
	assert(#Count.steps(5, 8, 10) == 3, "a small rise doesn't repeat numbers")
end)

local function node(path: string, x: number, y: number, w: number, h: number, extra: any?): any
	local n = { path = path, x = x, y = y, w = w, h = h, ancestors = {} }
	for k, v in extra or {} do
		n[k] = v
	end
	return n
end

local function rules(nodes: { any }): { string }
	local out = {}
	for _, f in LayoutRules.check(nodes) do
		table.insert(out, f.rule)
	end
	table.sort(out)
	return out
end

test("layout lint: a clean HUD gives nothing", function()
	local plate = node("Hud.Gold", 10, 100, 200, 48, { hasChildren = true })
	local amount = node("Hud.Gold.Amount", 60, 108, 120, 32, {
		ancestors = { "Hud.Gold" },
		text = 28,
		textWidth = 90,
	})
	local shop = node("Hud.Shop", 700, 160, 64, 64, { hasChildren = true })
	local icon =
		node("Hud.Shop.Icon", 712, 172, 40, 40, { ancestors = { "Hud.Shop" }, iconOf = "Hud.Shop" })
	local touching = node("Hud.Level", 10, 52, 200, 48)
	assert(#LayoutRules.check({ plate, amount, shop, icon, touching }) == 0)
end)

test("layout lint: each defect fires its own rule once", function()
	local function only(n: { any }, want: string)
		local got = rules(n)
		assert(#got == 1 and got[1] == want, `{want}: got {table.concat(got, ",")}`)
	end
	only({ node("A", 0, 0, 100, 40), node("B", 50, 20, 100, 40) }, "overlap")
	only({ node("Sheet.Body", 0, 0, 300, 0, { hasChildren = true }) }, "zero")
	only({ node("Count", 0, 0, 40, 12, { text = 10 }) }, "small-text")
	only({ node("Wear", 0, 0, 111, 30, { text = 16, textWidth = 186 }) }, "text-overflow")
	only({
		node("Slot", 0, 0, 60, 60, { hasChildren = true }),
		node("Slot.Icon", 21, 21, 18, 18, { ancestors = { "Slot" }, iconOf = "Slot" }),
	}, "small-icon")
end)

test("layout lint: a free node (backdrop, toast) may overlap", function()
	local backdrop = node("Shop.Backdrop", 0, 0, 1280, 720, { free = true })
	assert(#LayoutRules.check({ backdrop, node("Hud.Gold", 10, 100, 200, 48) }) == 0)
	assert(LayoutRules.line({ rule = "zero", path = "P", detail = "d" }) == "LINT zero P: d")
end)

local failed = 0
for _, t in tests do
	local ok, err = pcall(t.fn)
	if not ok then
		failed += 1
		print(`FAIL {t.name}: {err}`)
	end
end
print(`Tests: {#tests - failed} passed, {failed} failed`)
if failed > 0 then
	process.exit(1)
end
