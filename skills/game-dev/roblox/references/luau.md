# Luau: house style, OOP + factory, and what the engine rewards

Read before writing or reviewing Luau. The base is Roblox's own style guide. Where the other
sources disagree with it, this file names the choice and why. StyLua enforces the formatting
(`stylua.toml`), so formatting is never a review comment.

## Sources (read 2026-11-16)

| Source | What it gives | Weight |
|---|---|---|
| [Roblox Lua Style Guide](https://roblox.github.io/lua-style-guide/) | file layout, requires, naming, the typed class pattern, errors | **base** |
| [luau.org: Performance](https://luau.org/performance) | what the VM and compiler optimise | **base** for speed |
| [luau.org: Object-oriented programs](https://luau.org/types/object-oriented-programs) | annotating `self` | **base** for typed classes |
| [Roblox: Native code generation](https://create.roblox.com/docs/luau/native-code-gen) | `--!native`, `@native` | **base** for native |
| [Roblox: `require`](https://create.roblox.com/docs/reference/engine/globals/LuaGlobals) | require-by-string (`./`, `../`, `@self/`, `@game/`) | **base** |
| [evaera: Best practices](https://gist.github.com/evaera/fee751d4e228dd262fe1174ba142a719) | naming, composition, cleanup, errors as values | adopted |
| [Aqua's Luau style guide](https://devforum.roblox.com/t/aquas-luau-style-guide-promotes-consistency-and-readability/2523951) ([full text](https://hackmd.io/@aquaisaquafina/aquas_luau_style_guide)) | section template, single-script architecture, composition, typed signatures | partly adopted (see Conflicts) |
| [Luau Internals 101](https://devforum.roblox.com/t/luau-internals-101/3244837) | bytecode, registers, GC objects, comment directives | background; one claim corrected below |
| [CoddyKit: Module patterns](https://www.coddykit.com/courses/learn_lua/module-patterns-and-best-practices-4041986) | `local M = {}` … `return M`; private locals | only its indexed summary was readable |

## Conflicts, and the choice made

| Topic | Roblox guide | Aqua | Chosen | Why |
|---|---|---|---|---|
| Local names | camelCase | PascalCase | **camelCase** | the base; matches evaera and most Roblox open source |
| Early return | on its own lines | one line `if x then return end` | **own lines** | StyLua formats it so; easier to add a log line later |
| Framework | none | Knit | **none** | the classes and factories below are the structure; no dependency to keep alive |
| Section banners (`--[[ Services ]]--`) | file order only | banners | **order only** | StyLua and the fixed order make banners redundant |
| Tab width | tabs | 3 spaces | **tabs** | StyLua `indent_type = "Tabs"` |

## File layout (every module)

1. `--!strict`, then one comment line on **why** the file exists (no name, author or date)
2. Services: `local Players = game:GetService("Players")`
3. Requires, at the top only, sorted; a sibling is `require("./Sibling")`, a child
   `require("@self/Child")`, a fixed place `require("@game/ReplicatedStorage/Shared/X")`
4. Constants: `LOUD_SNAKE_CASE`
5. Module-level locals and private functions (private state stays a local: an upvalue no
   caller can reach)
6. The table the module returns, its functions
7. `return` the table: one value per module, the file named after it

Lune resolves `./` and `../` the same way, so shared modules that only require each other run
under Lune in tests as they do in Studio.

## Names

- Spell words out: `player`, not `plr`. Booleans read as questions: `isAvailable`, `hasWon`.
- Classes, modules, types: `PascalCase`. Locals, functions, methods, fields: `camelCase`.
  Constants: `LOUD_SNAKE_CASE`. Private fields: `_camelCase`.
- Event handlers say when they run: `onPlayerAdded`.
- No boolean arguments that switch behaviour, and no `nil` placeholders: pass an options table
  last.

## Classes (OOP)

The typed prototype pattern from the Roblox guide. The type is written once next to the class, and
the checker flags drift between the type and `new`.

```lua
--!strict
-- A player's coins. Pure state, so Lune can test it.

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

function Wallet.add(self: Wallet, amount: number): number
	assert(amount > 0, "amount must be above 0")
	self.coins = math.min(self.coins + amount, self.goal)
	return self.coins
end

return Wallet
```

- **Methods are defined `Class.method(self: T, …)`** and called `obj:method(…)`. Luau cannot yet
  share one `self` type across `:`-defined methods, so annotate `self` (luau.org).
- **Every field is in the constructor's table literal**, `nil` ones included. Luau builds such
  objects from a template, which is faster than adding fields later (luau.org).
- **`__index` is the class table itself**, never a function and never a deep chain: method calls
  on `obj:method()` are then a fast path (luau.org).
- **Composition, not inheritance.** A class *has* other objects (`Pickup` has a `Definition`)
  instead of extending a base class. Ask "has a / uses a / can do", not "is a" (evaera, Aqua).
- **Rules classes take time and input as arguments** (`pickup:take(now)`), never `os.clock()` or
  `task.wait` inside, so they run under Lune.
- **What a class creates, it cleans up.** A class that makes Instances or connections keeps them
  in fields and has `destroy()` that disconnects and destroys them all (evaera: "be tidy").

## Factories

One module per family of objects, holding the only list of kinds. Adding a kind is one row, and
callers never call `Class.new` with hand-built data.

```lua
--!strict
-- The one place pickups are made. A new kind is one row in DEFINITIONS.

local Pickup = require("./Pickup")

local DEFINITIONS: { [string]: Pickup.Definition } = table.freeze({
	coin = table.freeze({ kind = "coin", value = 1, respawnSeconds = 3 }),
	gem = table.freeze({ kind = "gem", value = 5, respawnSeconds = 10 }),
})

local PickupFactory = {}

function PickupFactory.create(kind: string): Pickup.Pickup
	local definition = DEFINITIONS[kind]
	assert(definition, `unknown pickup kind "{kind}"`)
	return Pickup.new(definition)
end

return PickupFactory
```

- **Definitions are frozen data** (`table.freeze`): tuning lives in one table, and nothing changes
  it at run time.
- **An unknown kind fails loudly** at the factory (`assert`), not later as a `nil` field. It is a
  usage error, the case the Roblox guide keeps `error`/`assert` for.
- **The factory makes only pure objects.** Anything that touches the world (a Part, a connection)
  is a separate class on the server (`PickupSpawner`) that asks the factory for its rules object.
  The rules stay testable, and the world code stays small.

## Where code lives

| Folder (Rojo) | In Studio | Holds |
|---|---|---|
| `src/shared/` | ReplicatedStorage.Shared | classes and factories both sides need; **no `game` in rules modules** |
| `src/server/` | ServerScriptService.Server | the one server Script (`init.server.luau`) and server-only classes |
| `src/client/` | StarterPlayerScripts.Client | the one client script and client-only classes |

One Script and one LocalScript; everything else is a module they wire up (Aqua's "1:1 rule").
Code only the server needs stays out of ReplicatedStorage: the client can read everything there.

## Errors

- A function that can fail in normal play returns `ok, result` (or `nil, reason`). Do not use
  `error` for control flow (Roblox guide, evaera).
- `assert`/`error` only for misuse: wrong types, unknown kinds, broken invariants.
- Calls that throw (DataStores, HTTP) go in `pcall`, with a comment naming the failure expected.

## Performance: what Luau rewards

From luau.org/performance unless marked.

- `t.field` with a constant name is cached; keep fields on the object, methods on the metatable.
- Calling a builtin directly (`math.max(x, 1)`) is a fast call. Caching methods in locals gains
  nothing in Luau.
- `getfenv`, `setfenv` and `loadstring` deoptimise the whole environment: never use them.
- Each closure created allocates a function object. Luau caches closures with no upvalues, or
  whose upvalues are immutable and module-scope. Inside hot loops, hoist callbacks to module level
  instead of building them per call.
- Append with `table.insert`; for a known size, `table.create(n)` then index writes.
- `for k, v in t do` and the `ipairs`/`pairs` forms are all specialised.
- `--!native` (Roblox docs): only on modules that do heavy computation, or `@native` on the hot
  function. It costs compile time and memory and has a game-wide limit; measure with the Script
  Profiler. Typed arguments, especially `Vector3`, generate better native code.
- `--!optimize 2` inlines and hurts debugging (Internals 101); leave the default unless measured.

## Internals worth knowing (Luau Internals 101, checked)

- Luau compiles to bytecode for a register-based VM.
- Strings, tables and buffers are garbage-collected heap objects; numbers, booleans, `nil` and
  vectors are plain values. A `Vector3` math loop allocates nothing; building strings in a loop
  does.
- Tables have an array part and a hash part: keep arrays dense from 1.
- **Correction:** the post says each closure creates a new `lua_State`. A `lua_State` belongs to a
  thread (a coroutine or task). A closure is a function object, which luau.org says is allocated
  per creation unless cached. The advice still holds for hot paths: don't create closures you
  don't need.

## Review checklist

- [ ] `--!strict` at the top; every function's arguments and return typed; `self` annotated
- [ ] File order: why-comment, services, requires, constants, locals, module, `return`
- [ ] A new kind of thing went into its factory's table, not a new hand-built call site
- [ ] Rules modules hold no `game`, no clock, no waits, and have a test in `tests/run.luau`
- [ ] Every class that creates Instances or connections has `destroy()`, and someone calls it
- [ ] The server decides anything a player could gain; client input is checked for type, range
      and rate
- [ ] No `getfenv`/`setfenv`/`loadstring`; no `__index` functions in hot classes
- [ ] `stylua --check` and `selene src` are clean
