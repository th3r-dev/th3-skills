-- Headless tests for the instance-free modules in src/shared, under Lune:
--   lune run tests/run
-- The UI itself (ScreenGuis, tweens, the StyleSheet) is checked in a Studio playtest at three
-- device sizes; see the README. One `FAIL <name>: <error>` line per failure, then a count; exit 1 on any.

local process = require("@lune/process")

local Gold = require("../src/shared/Gold")
local KeyOffer = require("../src/shared/KeyOffer")
local Progress = require("../src/shared/Progress")
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
