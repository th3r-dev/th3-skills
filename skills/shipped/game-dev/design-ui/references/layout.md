# Layout: positions, constraints, safe areas, devices

Roblox's own rules first ([position and size](https://create.roblox.com/docs/ui/position-and-size),
[on-screen containers](https://create.roblox.com/docs/ui/on-screen-containers)), then the DevForum
practice that fills their gaps ([UI designing tips](https://devforum.roblox.com/t/ui-designing-tips/2423307)).
design-core's composition rules ([visual-principles.md](../../../design/core/references/visual-principles.md))
still decide grouping and spacing; this file is how to make them hold on every screen.

## Position and size

- `Position` and `Size` are UDim2: **Scale** is a fraction of the parent, **Offset** a fixed pixel
  amount, and the two add. Use Scale and leave every Offset at 0. A pixel you think you need is a
  missing layout object: padding (`UIPadding`), a gap (`UIListLayout.Padding`), a fixed shape
  (`UIAspectRatioConstraint`), a floor or ceiling (`UISizeConstraint`, `UITextSizeConstraint`).
- `AnchorPoint` is where the element grows from. Put it at the corner it lives in: `(0, 0)`
  top-left, `(1, 0)` top-right, `(0.5, 0.5)` a centred dialog, `(0, 1)` bottom-left. Then
  `Position` names that corner.
- Type values in Properties. The on-canvas draggers write Scale and Offset hybrids that break on
  other screens.
- Layering: `ZIndex` among siblings; `DisplayOrder` between ScreenGuis (a modal shop sits above the
  HUD).

## Layout objects do the arithmetic

| Need | Object |
|---|---|
| A row or column, gaps, alignment | `UIListLayout` (with `Wraps` and flex for growing items) |
| A grid of tiles (inventory, shop) | `UIGridLayout`, with `CellSize` in Scale plus `UIAspectRatioConstraint` on the cells |
| Inner margins | `UIPadding` (Scale) |
| A shape that never stretches (icons, square buttons, cards) | `UIAspectRatioConstraint` |
| A size floor and ceiling (a tap target, a panel on ultrawide) | `UISizeConstraint` |
| Text that fits | `TextScaled = true` with `UITextSizeConstraint.MaxTextSize`, or a fixed `TextSize` that was checked on the phone capture |
| Scale the whole HUD per device | one `UIScale`, set from the screen size in one place |

## Safe areas and reserved zones

- `ScreenGui.ScreenInsets = CoreUISafeInsets` (the default) keeps interactive UI clear of the top
  bar buttons and screen cutouts. Use it for anything the player taps; a full-screen backdrop can
  go edge to edge on its own ScreenGui.
- The **bottom-left and bottom-right corners** belong to the default thumbstick and jump button on
  touch devices. Place nothing that matters there; place your own action buttons relative to the
  jump button.
- `ResetOnSpawn = false` on HUD ScreenGuis that are direct children of StarterGui, or the HUD
  rebuilds on every respawn. (Nested inside a Folder, it resets anyway.)
- Keys Roblox keeps: **Escape** opens Roblox's menu and reaches the game already processed, so a
  dialog can't close on it; use the close button, the backdrop or the key that opened it. **/** focuses
  chat.
- **Chat** sits top-left on every device, and its input bar reaches about a third of the way down
  when active. Keep the HUD out of that corner, or move the chat window with TextChatService's
  `ChatWindowConfiguration`.
- The **People list** (PlayerList) opens top-right and grows down with the server's size; on a
  phone it covers a quarter of the screen. Capture the HUD with it open, at the server's full
  size, or the plates under it are found by the owner, not the review.
- Every HUD brief has a **Reserved zones** section naming what it keeps clear: chat, the People
  list, the top bar, the thumbstick and the jump button, plus any of the game's own permanent
  panels.
- Hide what you replace: `StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Health, false)` for your own
  health bar; `GuiService.TouchControlsEnabled = false` only when the game ships its own controls.

## Devices

| Device | Check at | What breaks first |
|---|---|---|
| Phone, landscape | about 844×390 | text overflow, buttons under the thumbs' reach, HUD covering the play area |
| Tablet | 1024×768 (4:3) | wide panels squeezed, thumb zones farther in: a button 40% from the top a phone reaches can be out of reach on a tablet |
| Desktop | 1280×720 baseline, then 1920×1080 | stretched panels and icons (missing aspect constraints) |
| Console / ten-foot | 1920×1080 from across a room | small text; every control must be reachable by gamepad selection |

Design at 1280×720 and scale up. A big, ten-foot-style UI also tends to be touch-friendly and
gamepad-navigable.

## Viewport matrix

Every state of every surface is captured at each of these before it goes to review. Three sizes
were not enough: a flyout that fitted 844×390 ran off a 667-tall screen, and a desktop window
with the browser's chrome is far shorter than 1080.

| Viewport | Why it is here |
|---|---|
| 667×375 | the smallest common phone; flyouts and stacks run out of height first |
| 844×390 | the usual phone; text floors and thumb reach |
| 1024×768 | tablet; wide panels squeezed, thumb zones farther in |
| 1270×557 | a desktop window with browser chrome; short and wide |
| 1920×1080 | full desktop and console; stretched panels, ten-foot text |
| any of the above at graphics quality 1 | SurfaceGuis and effects can draw blank at the lowest level |

Capture with the People list open and with every timed element showing at once (banners,
chips, badges, toasts). Overlaps hide in the states that rarely coincide.

## Thumb zones (touch)

- The frequent action sits where a thumb rests: the right side, above the jump button, for the
  right thumb. The left thumb is busy with the stick.
- Tap targets: big and spaced. Use a `UISizeConstraint` floor so a Scale-sized button never shrinks
  below what a thumb can hit, and keep a gap between neighbours so a miss doesn't press the wrong one.
- Avoid precision drags unless the game is built on them; prefer taps, snapping and auto-targeting.
- Show controls only when they apply (context-based UI, proximity prompts): fewer buttons on screen,
  fewer mis-taps.
