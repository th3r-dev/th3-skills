-- Headless tests for the pure rules in src/shared, under Lune:
--   lune run tests/run
-- Anything that needs `game` (parts, players, replication) is checked in a
-- Studio playtest instead, by hand or through the Studio MCP server.
-- Output test-run.sh reads: one `FAIL <name>: <error>` line per failed test, then
-- `Tests: <n> passed, <n> failed`, or `No tests found`. Exit 1 on any failure.

local process = require("@lune/process")
local Rules = require("../src/shared/Rules")

local tests: { { name: string, fn: () -> () } } = {}
local function test(name: string, fn: () -> ())
	table.insert(tests, { name = name, fn = fn })
end

test("a new game starts at zero coins", function()
	assert(Rules.newState().coins == 0)
end)

test("a coin adds to the count", function()
	assert(Rules.collect(Rules.newState(), 1).coins == 1)
end)

test("the count stops at the goal", function()
	local state = Rules.collect(Rules.newState(3), 5)
	assert(state.coins == 3 and Rules.won(state))
end)

test("a non-positive amount is refused", function()
	assert(not pcall(Rules.collect, Rules.newState(), 0))
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
