--!strict
-- Names shared by server and client: the remote and the player attributes the HUD reads.

return {
	BUY_KEY = "BuyKey", -- RemoteFunction: the client asks, the server decides
	GOLD = "Gold",
	LEVEL = "Level",
	XP = "Xp",
	HAS_KEY = "HasKey",
	HEARTBEAT = "Heartbeat", -- server time of the last tick; the HUD shows "Reconnecting…" when it stops
}
