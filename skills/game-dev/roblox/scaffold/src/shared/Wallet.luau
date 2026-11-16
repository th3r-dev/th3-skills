--!strict
-- A player's coins. Pure state, no Roblox instance, so tests/run.luau checks it under Lune.
-- The server owns one per player; a client never holds or changes one.

local Wallet = {}
Wallet.__index = Wallet

export type Wallet = typeof(setmetatable(
	{} :: {
		coins: number,
		goal: number,
	},
	Wallet
))

function Wallet.new(goal: number): Wallet
	assert(goal > 0, "goal must be above 0")
	local self = {
		coins = 0,
		goal = goal,
	}
	return setmetatable(self, Wallet)
end

-- Adds coins, stopping at the goal. Returns the new count.
function Wallet.add(self: Wallet, amount: number): number
	assert(amount > 0, "amount must be above 0")
	self.coins = math.min(self.coins + amount, self.goal)
	return self.coins
end

function Wallet.hasWon(self: Wallet): boolean
	return self.coins >= self.goal
end

return Wallet
