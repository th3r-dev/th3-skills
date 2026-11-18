# Ability effects: rocks out of the ground

Adapted from [nonlooped/roblox-suite@fc1c3dd `EffectBurst.lua`](https://github.com/nonlooped/roblox-suite/blob/fc1c3dd26fef67ee4d7b6e20b1299b44fc6101ae/roblox-vfx/scripts/EffectBurst.lua) (MIT, © 2026 nonlooped) and the DevForum thread [Roblox VFX and power abilities](https://devforum.roblox.com/t/roblox-vfx-and-power-abilities/1537223).

The flow is in [`../SKILL.md`](../SKILL.md). Style, classes and the review checklist:
[`../../roblox/references/luau.md`](../../roblox/references/luau.md). The snippets are `--!strict`
and pass that checklist, but they were checked with Selene and StyLua only (no type checker ran).

| File | Side | Role |
|---|---|---|
| `src/shared/VfxDefinitions.luau` | both | frozen id to definition table; no `game` |
| `src/client/Effect.luau` | client | clones a template's emitters, `play`, `destroy` |
| `src/client/RockRise.luau` | client | rocks in an arc, tween up, dust, sink, `destroy` |
| `src/client/VfxFactory.luau` | client | the only place an id becomes an object |
| `src/client/init.client.luau` | client | key press, `OnClientEvent`, distance cull |
| `src/server/init.server.luau` | server | request checks, cooldown, the hit, `FireAllClients` |

Templates are made in Studio under `ReplicatedStorage.VfxTemplates`: a Folder `RockDust` holding
the dust `ParticleEmitter`s, a part `Rock`, and a layered hit `Impact` built the way
[`look.md`](look.md) describes. Nothing here mutates them.

Per-emitter attributes, set in Studio on a template's emitters:

| Attribute | Type | Effect |
|---|---|---|
| `EmitCount` | number | particles for this emitter; default the definition's `burst` |
| `EmitDelay` | number | seconds after `play`; this is how one template holds flash, impact and residue |
| `NoColor` | boolean | the definition's `tint` skips it (black layers, white flashes) |

`EmitDuration` (emission spread over time) is not read: add it when a template needs it.

## Definitions

```lua
--!strict
-- Effect definitions by id. No `game`: server and client read the same table. A new effect is one row.

export type Definition = {
	kind: "burst" | "rockRise",
	template: string, -- emitters, under ReplicatedStorage.VfxTemplates
	burst: number, -- particles per emitter without an EmitCount attribute
	tint: Color3?, -- multiplies Color on every emitter without NoColor; white templates take it as is
	rock: string?, -- rockRise: BasePart template name
	rocks: number?,
	distance: number?, -- studs in front of the root
	height: number?, -- studs the rocks rise
	hold: number?, -- seconds up before sinking
}

local VfxDefinitions: { [string]: Definition } = table.freeze({
	impactDust = table.freeze({ kind = "burst", template = "RockDust", burst = 20 }),
	-- one white layered template, recoloured per element
	impactFire = table.freeze({
		kind = "burst",
		template = "Impact",
		burst = 1,
		tint = Color3.fromRGB(255, 120, 20),
	}),
	impactFrost = table.freeze({
		kind = "burst",
		template = "Impact",
		burst = 1,
		tint = Color3.fromRGB(70, 150, 255),
	}),
	rockRise = table.freeze({
		kind = "rockRise",
		template = "RockDust",
		burst = 25,
		rock = "Rock",
		rocks = 5,
		distance = 8,
		height = 4,
		hold = 1.5,
	}),
})

return VfxDefinitions
```

## Effect (emitters only)

Port of `EffectBurst`: clone every emitter under the template, never touch the template, emit each
by its `EmitCount` at its `EmitDelay`, destroy after the last delay plus its `Lifetime.Max`. The
clones sit under a tiny invisible part, so Sphere and Cylinder shapes work and the `CFrame` aims them.

```lua
--!strict
-- One playing burst: cloned emitters under a holder part, each emitted by its EmitCount at its
-- EmitDelay, removed once the last one has finished.

local VfxDefinitions = require("@game/ReplicatedStorage/Shared/VfxDefinitions")

local function numberAttribute(instance: Instance, name: string, default: number): number
	local value = instance:GetAttribute(name)
	return if typeof(value) == "number" then value else default
end

local function tinted(sequence: ColorSequence, tint: Color3): ColorSequence
	local keypoints = {}
	for _, keypoint in sequence.Keypoints do
		local c = keypoint.Value
		local value = Color3.new(c.R * tint.R, c.G * tint.G, c.B * tint.B)
		table.insert(keypoints, ColorSequenceKeypoint.new(keypoint.Time, value))
	end
	return ColorSequence.new(keypoints)
end

local Effect = {}
Effect.__index = Effect

export type Effect = typeof(setmetatable(
	{} :: {
		_holder: Part,
		_emitters: { ParticleEmitter },
		_burst: number,
		_lifetime: number,
		_pending: { thread },
		_cleanup: thread?,
		_destroyed: boolean,
	},
	Effect
))

function Effect.new(templates: Instance, definition: VfxDefinitions.Definition): Effect
	local template = templates:FindFirstChild(definition.template)
	assert(template, `unknown effect template "{definition.template}"`)

	local holder = Instance.new("Part")
	holder.Name = definition.template
	holder.Size = Vector3.one * 0.1
	holder.Transparency = 1
	holder.Anchored = true
	holder.CanCollide = false
	holder.CanQuery = false
	holder.CanTouch = false

	local emitters: { ParticleEmitter } = {}
	local lifetime = 0
	for _, descendant in template:GetDescendants() do
		if descendant:IsA("ParticleEmitter") then
			local emitter = descendant:Clone()
			emitter.Enabled = false
			emitter.Rate = 0
			if definition.tint and emitter:GetAttribute("NoColor") ~= true then
				emitter.Color = tinted(emitter.Color, definition.tint)
			end
			emitter.Parent = holder
			table.insert(emitters, emitter)
			lifetime =
				math.max(lifetime, numberAttribute(emitter, "EmitDelay", 0) + emitter.Lifetime.Max)
		end
	end
	assert(#emitters > 0, `template "{definition.template}" has no ParticleEmitter`)

	local self = {
		_holder = holder,
		_emitters = emitters,
		_burst = definition.burst,
		_lifetime = lifetime,
		_pending = {} :: { thread },
		_cleanup = nil :: thread?,
		_destroyed = false,
	}
	return setmetatable(self, Effect)
end

function Effect.play(self: Effect, cframe: CFrame)
	if self._destroyed or self._cleanup then
		return
	end
	self._holder.CFrame = cframe
	self._holder.Parent = workspace
	for _, emitter in self._emitters do
		local count = numberAttribute(emitter, "EmitCount", self._burst)
		local delay = numberAttribute(emitter, "EmitDelay", 0)
		if delay > 0 then
			table.insert(
				self._pending,
				task.delay(delay, function()
					emitter:Emit(count)
				end)
			)
		else
			emitter:Emit(count)
		end
	end
	self._cleanup = task.delay(self._lifetime, function()
		self._cleanup = nil
		self:destroy()
	end)
end

function Effect.destroy(self: Effect)
	if self._destroyed then
		return
	end
	self._destroyed = true
	if self._cleanup then
		task.cancel(self._cleanup)
		self._cleanup = nil
	end
	for _, pending in self._pending do
		if coroutine.status(pending) == "suspended" then
			task.cancel(pending)
		end
	end
	table.clear(self._pending)
	for _, emitter in self._emitters do
		emitter.Enabled = false
		emitter:Clear()
	end
	self._holder:Destroy()
end

return Effect
```

## RockRise

The rocks start below ground (`root * CFrame.new(0, -h, -dist)`), rise on a tween, hold, then sink.
They are anchored, `CanCollide = false` visual copies: the tween moves their `CFrame`, so no
physics, no `BodyVelocity`. For rocks that must block or push a player, make them real
server parts and move them with a `LinearVelocity` or `AlignPosition`; that is gameplay, not VFX.

```lua
--!strict
-- Rocks burst out of the ground in an arc in front of the player. Visual copies only.

local TweenService = game:GetService("TweenService")

local Effect = require("./Effect")
local VfxDefinitions = require("@game/ReplicatedStorage/Shared/VfxDefinitions")

local ROOT_ABOVE_GROUND = 3 -- HumanoidRootPart centre over the floor, studs
local ARC = math.rad(100)
local RISE_SECONDS = 0.35
local SINK_SECONDS = 0.6
local RISE_INFO = TweenInfo.new(RISE_SECONDS, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local SINK_INFO = TweenInfo.new(SINK_SECONDS, Enum.EasingStyle.Quad, Enum.EasingDirection.In)

local rng = Random.new()

local RockRise = {}
RockRise.__index = RockRise

export type RockRise = typeof(setmetatable(
	{} :: {
		_definition: VfxDefinitions.Definition,
		_rock: BasePart,
		_dust: Effect.Effect,
		_rocks: { BasePart },
		_task: thread?,
		_destroyed: boolean,
	},
	RockRise
))

function RockRise.new(templates: Instance, definition: VfxDefinitions.Definition): RockRise
	local rock = templates:FindFirstChild(definition.rock or "")
	assert(rock and rock:IsA("BasePart"), `unknown rock template "{definition.rock}"`)
	local self = {
		_definition = definition,
		_rock = rock,
		_dust = Effect.new(templates, definition),
		_rocks = {} :: { BasePart },
		_task = nil :: thread?,
		_destroyed = false,
	}
	return setmetatable(self, RockRise)
end

function RockRise.play(self: RockRise, root: CFrame)
	if self._destroyed or self._task then
		return
	end
	local definition = self._definition
	local count = definition.rocks or 5
	local distance = definition.distance or 8
	local height = definition.height or 4
	local hold = definition.hold or 1.5

	for index = 1, count do
		local angle = if count == 1 then 0 else ((index - 1) / (count - 1) - 0.5) * ARC
		local depth = ROOT_ABOVE_GROUND + self._rock.Size.Y / 2
		local tilt = CFrame.Angles(rng:NextNumber(-0.3, 0.3), rng:NextNumber(0, math.pi * 2), 0)
		local start = root * CFrame.Angles(0, angle, 0) * CFrame.new(0, -depth, -distance) * tilt

		local part = self._rock:Clone()
		part.Anchored = true
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
		part.CFrame = start
		part.Parent = workspace
		table.insert(self._rocks, part)

		TweenService:Create(part, RISE_INFO, { CFrame = start + Vector3.new(0, height, 0) }):Play()
	end

	self._dust:play(root * CFrame.new(0, -ROOT_ABOVE_GROUND, -distance))

	self._task = task.spawn(function()
		task.wait(RISE_SECONDS + hold)
		for _, part in self._rocks do
			local sunk = part.CFrame - Vector3.new(0, height, 0)
			TweenService:Create(part, SINK_INFO, { CFrame = sunk }):Play()
		end
		task.wait(SINK_SECONDS)
		self._task = nil
		self:destroy()
	end)
end

function RockRise.destroy(self: RockRise)
	if self._destroyed then
		return
	end
	self._destroyed = true
	if self._task then
		task.cancel(self._task)
		self._task = nil
	end
	for _, part in self._rocks do
		part:Destroy()
	end
	table.clear(self._rocks)
	self._dust:destroy()
end

return RockRise
```

## Factory

```lua
--!strict
-- The one place effects are made. A new kind is a row in VfxDefinitions.

local Effect = require("./Effect")
local RockRise = require("./RockRise")
local VfxDefinitions = require("@game/ReplicatedStorage/Shared/VfxDefinitions")

local VfxFactory = {}

function VfxFactory.play(effectId: string, templates: Instance, cframe: CFrame)
	local definition = VfxDefinitions[effectId]
	assert(definition, `unknown effect "{effectId}"`)
	if definition.kind == "rockRise" then
		RockRise.new(templates, definition):play(cframe)
	else
		Effect.new(templates, definition):play(cframe)
	end
end

return VfxFactory
```

`templates` is passed in, so the factory holds no `game`. Each effect destroys itself when its
`play` ends, so the caller keeps no handle and no union type is needed.

## Client script

Input, the `OnClientEvent` hook and the distance cull. The client trusts nothing about gameplay: it
only draws.

```lua
--!strict
-- Reads the ability key and plays effects the server announces.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local VfxFactory = require("@self/VfxFactory")

local MAX_DISTANCE = 200 -- studs from the camera; farther effects are skipped
local KEYS: { [Enum.KeyCode]: string } = { [Enum.KeyCode.E] = "rockRise" }

local remote = ReplicatedStorage:WaitForChild("AbilityRemote") :: RemoteEvent
local templates = ReplicatedStorage:WaitForChild("VfxTemplates")

UserInputService.InputBegan:Connect(function(input: InputObject, processed: boolean)
	local abilityId = KEYS[input.KeyCode]
	if processed or not abilityId then
		return
	end
	remote:FireServer(abilityId)
end)

remote.OnClientEvent:Connect(function(effectId: unknown, cframe: unknown)
	if type(effectId) ~= "string" or typeof(cframe) ~= "CFrame" then
		return
	end
	local camera = workspace.CurrentCamera
	if camera and (cframe.Position - camera.CFrame.Position).Magnitude > MAX_DISTANCE then
		return
	end
	VfxFactory.play(effectId, templates, cframe)
end)
```

## Server script

The server owns *whether* the ability happened. The origin comes from the server's own view of the
character, so there is no client position to range-check; if you add an aimed target, clamp it:
`(point - root.Position).Magnitude <= reach`.

```lua
--!strict
-- Ability requests: check, apply the hit, then tell every client to draw it.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type Ability = {
	cooldown: number, -- seconds between uses, per player
	reach: number, -- studs in front of the root where the hit is centred
	radius: number,
	damage: number,
}

local ABILITIES: { [string]: Ability } = table.freeze({
	rockRise = table.freeze({ cooldown = 4, reach = 8, radius = 8, damage = 20 }),
})

local lastUsed: { [Player]: number } = {}

local remote = Instance.new("RemoteEvent")
remote.Name = "AbilityRemote"
remote.Parent = ReplicatedStorage

local function getLivingRoot(player: Player): BasePart?
	local character = player.Character
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if humanoid and humanoid.Health > 0 and root and root:IsA("BasePart") then
		return root
	end
	return nil
end

remote.OnServerEvent:Connect(function(player: Player, abilityId: unknown)
	if type(abilityId) ~= "string" then
		return
	end
	local ability = ABILITIES[abilityId]
	local root = getLivingRoot(player)
	local character = player.Character
	if not ability or not root or not character then
		return
	end

	local now = os.clock()
	if now - (lastUsed[player] or -math.huge) < ability.cooldown then
		return
	end
	lastUsed[player] = now

	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { character }
	local center = (root.CFrame * CFrame.new(0, 0, -ability.reach)).Position
	local damaged: { [Model]: boolean } = {}
	for _, part in workspace:GetPartBoundsInRadius(center, ability.radius, params) do
		local model = part:FindFirstAncestorOfClass("Model")
		local humanoid = if model then model:FindFirstChildOfClass("Humanoid") else nil
		if model and humanoid and not damaged[model] then
			damaged[model] = true
			humanoid:TakeDamage(ability.damage)
		end
	end

	remote:FireAllClients(abilityId, root.CFrame)
end)

Players.PlayerRemoving:Connect(function(player: Player)
	lastUsed[player] = nil
end)
```

## Checklist for a new ability

- [ ] Gameplay numbers (cooldown, reach, radius, damage) are in the server's table, not the client's
- [ ] The effect is one row in `VfxDefinitions` and one template under `VfxTemplates`
- [ ] Every class that makes Instances has `destroy()`, and every `play` path reaches it
- [ ] Visual parts are anchored with `CanCollide`, `CanTouch` and `CanQuery` off
- [ ] No `BodyVelocity` or other BodyMover, no global `wait`/`spawn`/`delay`, no `Humanoid:LoadAnimation`
- [ ] Layered templates: one role per emitter, `EmitDelay` per stage, black layers and flashes tagged `NoColor` ([`look.md`](look.md))
- [ ] Played in Studio at the lowest and highest quality level; Fill Rate read; frozen frames captured per stage; otherwise NOT ASSESSED
