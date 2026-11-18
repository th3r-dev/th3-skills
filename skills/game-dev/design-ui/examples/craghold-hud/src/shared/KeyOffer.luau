--!strict
-- The dungeon key's offer: one function from what the player has to what the shop shows, so every
-- state in design/features/key-shop/design.md is decided in one place and tested under Lune.
-- The server uses `canBuy` with its own values; the client's view never grants anything.

local Gold = require("./Gold")
local Progress = require("./Progress")

local KeyOffer = {}

KeyOffer.PRICE = 12500
KeyOffer.UNLOCK_LEVEL = Progress.FARM_CAP

export type State = "locked" | "unaffordable" | "affordable" | "loading" | "owned" | "error"

export type View = {
	state: State,
	price: string,
	priceToken: string, -- a Tokens.colors name
	button: string,
	enabled: boolean,
	note: string?,
}

export type Facts = {
	gold: number,
	level: number,
	owned: boolean,
	pending: boolean?,
	failed: boolean?,
}

function KeyOffer.canBuy(gold: number, level: number, owned: boolean): (boolean, string?)
	if owned then
		return false, "owned"
	end
	if level < KeyOffer.UNLOCK_LEVEL then
		return false, "locked"
	end
	if gold < KeyOffer.PRICE then
		return false, "short"
	end
	return true, nil
end

function KeyOffer.view(facts: Facts): View
	local price = Gold.format(KeyOffer.PRICE)
	local short = math.max(KeyOffer.PRICE - facts.gold, 0)
	if facts.owned then
		return {
			state = "owned",
			price = price,
			priceToken = "Muted",
			button = "Owned",
			enabled = false,
			note = "The gate is open",
		}
	end
	if facts.level < KeyOffer.UNLOCK_LEVEL then
		return {
			state = "locked",
			price = price,
			priceToken = "Muted",
			button = `Reach LVL {KeyOffer.UNLOCK_LEVEL}`,
			enabled = false,
		}
	end
	if facts.pending then
		return {
			state = "loading",
			price = price,
			priceToken = "Accent",
			button = "Buying…",
			enabled = false,
		}
	end
	local view: View = if short > 0
		then {
			state = "unaffordable",
			price = price,
			priceToken = "PriceShort",
			button = `Need {Gold.format(short)} more`,
			enabled = false,
		}
		else {
			state = "affordable",
			price = price,
			priceToken = "Accent",
			button = "Buy key",
			enabled = true,
		}
	if facts.failed then
		view.state = "error"
		view.note = "Couldn't buy. Try again."
	end
	return view
end

return KeyOffer
