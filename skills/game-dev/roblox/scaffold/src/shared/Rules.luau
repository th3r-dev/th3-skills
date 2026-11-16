--!strict
-- The rules, with no Roblox instance in them: the server applies them, and
-- tests/run.luau checks them headless under Lune. Keep `game` out of this folder's
-- rule modules so they stay testable.

local Rules = {}

export type State = { coins: number, goal: number }

function Rules.newState(goal: number?): State
	return { coins = 0, goal = goal or 10 }
end

-- A collected coin. The server calls this; a client never sets coins itself.
function Rules.collect(state: State, amount: number): State
	assert(amount > 0, "amount must be above 0")
	return { coins = math.min(state.coins + amount, state.goal), goal = state.goal }
end

function Rules.won(state: State): boolean
	return state.coins >= state.goal
end

return Rules
