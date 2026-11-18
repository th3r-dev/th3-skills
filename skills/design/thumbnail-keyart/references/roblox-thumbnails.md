# Roblox thumbnails: what the sources say

Three sources, read November 2026. Their ideas are restated here and the pages are linked;
check Roblox's own creator docs before relying on a number, since platform limits change.

- **Roblox staff**: [5 tips to get the most out of Thumbnail Personalization](https://devforum.roblox.com/t/5-tips-from-roblox-staff-to-get-the-most-out-of-thumbnail-personalization/3471689)
  (DevForum, February 2025).
- **Simplified**: [Proven techniques for Roblox thumbnail design](https://simplified.com/blog/ai-design/proven-techniques-for-roblox-thumbnail-design).
- **ToyBox AI**: [What makes a good thumbnail](https://toyboxai.io/blog/what-makes-a-good-thumbnail/).

## The file

| Rule | Value | Source |
|---|---|---|
| Ratio and size | 16:9, 1920 × 1080 | Simplified, ToyBox |
| File size | under 3 MB | ToyBox |
| Bottom edge | no text there: the player count is drawn over it | ToyBox |
| Active thumbnails | 2-5 (personalization picks per player, up to 5) | ToyBox, Roblox staff |
| Detail page | up to 10 images or videos, each moderated | ToyBox |

The bench: `bench.py --bottom 120 --max-kb 3000` at 1080 (`--bottom 80` at 720).

## Personalization (Roblox staff)

Experiences that use it saw an average +12% relative lift in qualified play-through rate
(qPTR), some up to +56%.

1. **Don't restart a test within 7 days**, or before the next content update. Each restart throws
   away what the model learned, and the best thumbnail can change over time.
2. **Keep as many variations active as you can, up to 5.** More variations measured larger gains.
3. **Show new content.** A new thumbnail with each update tells players the game is maintained.
   Clickbait can trigger low-quality warnings, so show what is really there.
4. **Make variants different.** Thumbnails that look alike can't be told apart by the model. Vary
   the gameplay shown (combat, puzzles, exploration), the characters, the environment, or the
   **player motivation** each one speaks to (competition, creativity, social).
5. **Watch qPTR over time.** It can dip after a surge of homepage recommendations brings new
   players, then settle.

From the thread: winning segments are reported by age group; staff said gender is being tested.

## Composition and type (Simplified, ToyBox)

- **One moment of stakes** (a boss, a reward, a near miss) with **one focal point**: the character
  or the key object, big and seen first.
- Rule of thirds for the subject; **leading lines** (a path, a bridge, a fence) into it;
  foreground, midground and background for depth.
- Separate the subject from the background with **light against dark**; saturated colour with
  darker edges stands out in a feed.
- Palette by mood: warm for excitement and urgency, blue for calm. Complementary colours for
  punch, analogous for harmony.
- Characters in an **action pose** that shows who they are; a low camera makes them look
  powerful; signature items (weapon, vehicle) in the pose, not floating.
- Text: **about three words or none** besides the name, a heavy font that fits the genre, an
  outline or shadow, never over a busy patch. Words add to the title, they don't repeat it.

## Testing

- The **thumb test**: shrink to about a thumb's width on a phone; the subject and every word
  should read in one second. Then **grayscale**: if the subject sinks into the background, raise
  the contrast. Then put it **beside current thumbnails** in the same genre.
- A/B one variable at a time (background, expression, text), run at least a week, and check the
  difference isn't noise. Weekends and holidays skew results.

## Rules of the platform

Family-friendly, no sexual or graphically violent content, no hate, no personal information,
assets you have the rights to, and no misrepresenting the game.
