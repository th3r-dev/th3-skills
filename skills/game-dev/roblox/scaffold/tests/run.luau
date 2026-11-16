-- Headless tests for the instance-free classes in src/shared, under Lune:
--   lune run tests/run
-- Anything that needs `game` (parts, players, replication) is checked in a Studio playtest
-- instead, by hand or through the Studio MCP server.
-- Output test-run.sh reads: one `FAIL <name>: <error>` line per failed test, then
-- `Tests: <n> passed, <n> failed`, or `No tests found`. Exit 1 on any failure.

local process = require("@lune/process")

local Pickup = require("../src/shared/Pickup")
local PickupFactory = require("../src/shared/PickupFactory")
local Wallet = require("../src/shared/Wallet")

local tests: { { name: string, fn: () -> () } } = {}
local function test(name: string, fn: () -> ())
	table.insert(tests, { name = name, fn = fn })
end

test("a new wallet is empty", function()
	assert(Wallet.new(10).coins == 0)
end)

test("a wallet stops at its goal", function()
	local wallet = Wallet.new(3)
	assert(wallet:add(5) == 3 and wallet:hasWon())
end)

test("a wallet refuses a non-positive amount", function()
	assert(not pcall(Wallet.add, Wallet.new(3), 0))
end)

test("a pickup pays once, then respawns", function()
	local pickup = Pickup.new({ kind = "coin", value = 1, respawnSeconds = 3 })
	assert(pickup:take(0) == 1)
	assert(pickup:take(1) == 0)
	assert(pickup:take(3) == 1)
end)

test("the factory builds every kind it lists", function()
	for _, kind in PickupFactory.kinds() do
		assert(PickupFactory.create(kind).definition.kind == kind)
	end
end)

test("the factory refuses an unknown kind", function()
	assert(not pcall(PickupFactory.create, "nope"))
end)

test("definitions cannot be changed at run time", function()
	local definition = PickupFactory.create("coin").definition
	assert(not pcall(function()
		(definition :: any).value = 99
	end))
end)

if #tests == 0 then
	print("No tests found")
	process.exit(1)
end
local failed = 0
for _, t in tests do
	local ok, err = pcall(t.fn)
	if not ok then
		failed += 1
		print(`FAIL {t.name}: {err}`)
	end
end
print(`Tests: {#tests - failed} passed, {failed} failed`)
process.exit(if failed > 0 then 1 else 0)
