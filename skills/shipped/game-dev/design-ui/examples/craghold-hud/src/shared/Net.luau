--!strict
-- Names shared by server and client: the remote and the player attributes the HUD reads.

return {
	BUY_KEY = "BuyKey", -- RemoteFunction: the client asks, the server decides
	SAVE_SETTINGS = "SaveSettings", -- RemoteFunction: the client sends its settings, the server cleans and keeps them
	SETTINGS = "Settings", -- the server's clean copy as JSON, which the Settings panel starts from
	GOLD = "Gold",
	LEVEL = "Level",
	XP = "Xp",
	HAS_KEY = "HasKey",
	HEARTBEAT = "Heartbeat", -- server time of the last tick; the HUD shows "Reconnecting…" when it stops
}
