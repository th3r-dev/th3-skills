# Layouts

Five ways to lay out "brand on one side, four steps of what it does", collected from Dribbble
and the Inspo archive on 2026-11-15 and 2026-11-16. Each keeps the brand as the core zone, reads the
steps in order and ends on the one CTA. Pick by what the four steps are.

| Layout | The four steps are… | Reads as | Built in the example as |
|---|---|---|---|
| **columns** | four parallel jobs of a toolkit | a menu with a verb per column | `columns` |
| **rail** | a sequence, each step needs room for detail | a checklist down a timeline | `rail` |
| **stairs** | a progression that climbs or descends (setup to scale) | a path with momentum | `stairs` |
| **bento** | four uneven things that each want a tile | a product sheet, a dashboard | `bento` |
| **stack** | four layers of one system (front to back, top to bottom) | an architecture diagram | `stack` |
| **cover** | none: a post or article title, with one motif | a magazine cover | `cover` |

Every layout takes any style from [sizes-and-styles.md](sizes-and-styles.md#art-directions)
and passes the same bench.

## columns

Brand panel left (~32%), four equal columns right, a numbered rule over each, the CTA bar under them.

- Seen in: process infographics that put four shapes in a row with a title over each, e.g.
  Parvin Mahyar, ["Minimal Infographic in 4 shapes idea"](https://dribbble.com/shots/27750915-Minimal-Infographic-in-4-shapes-idea);
  feature-stack heroes in Inspo (CircleCI, GitHub features) that line features up under one headline.
- Use when the steps carry equal weight. One step with far more to say than the others breaks it.
- Column width caps the detail: at 1280 × 640 a column holds about 16 mono characters a line.

## rail

Brand panel left, four rows on a vertical line with a dot per step, the number and verb on the
left of each row, the detail and proof on the right.

- Seen in: Tracebit's platform page in Inspo (`tracebit-com--platform-aws`), a numbered vertical
  rail with a heading and a pill list per layer; the "how it works" timelines under Dribbble's
  [process steps banner](https://dribbble.com/search/process%20steps%20banner) search.
- Use when order matters and each step carries a list (skills, features, integrations). Each row
  gets the full width of the right side, so long names fit on one line.
- Dots on the line, aligned numbers and equal row heights are what make it read as a sequence.

## stairs

Four bands stepping down and to the right, each indented from the last, so the eye walks
diagonally from the brand to the CTA.

- Seen in: a SaaS banner under Dribbble's [saas banner](https://dribbble.com/search/saas%20banner)
  search (Sri Krishna Sai K S) that stacks "policy & procedure", "strategic support", "migration
  process" as tabbed bands stepping down a pastel ground.
- Use when the steps build on each other. The diagonal is the strongest motion of the five, so the
  CTA under the last step lands hardest.
- The indent shrinks the last band: keep the longest proof line on the first band.

## bento

The brand as one tall tile, the four steps as a 2 × 2 grid of tiles beside it, the CTA as a
wide tile under the grid. Rounded corners, one gap size everywhere.

- Seen in: UIGO Studio, ["Flankgan – AI Customer Feedback Aggregator Bento Branding"](https://dribbble.com/shots/27407313-Flankgan-AI-Customer-Feedback-Aggregator-Bento-Branding);
  Taqwah, ["Modern Fintech Branding Bento"](https://dribbble.com/shots/26309546-Modern-Fintech-Branding-Bento-Wealth-Management-Taqwah)
  (an oversized brand tile beside smaller detail tiles); Frameblox's
  ["Bento grid Hero section"](https://dribbble.com/shots/25594301-Bento-grid-Hero-section-for-Framer-built-with-Frameblox-UI-kit).
- Use when the steps are different kinds of thing, or the banner sits among other product imagery.
- One gap, one radius. Tiles that differ in padding or corner break the grid.

## stack

Four layers stacked like an architecture diagram, each slab offset by a shadow so it reads as
depth, a dashed request line running down through every layer and ending in the CTA.

- Seen in: the th3r-dev GitHub profile hero, where a request travels down Interface, Services,
  Data and Platform and back; Tracebit's layered platform page in Inspo (`tracebit-com--platform-aws`);
  ["Platform Diagram – Layered Stack for Security Platform"](https://dribbble.com/shots/23407362-Platform-Diagram-Layered-Stack-for-Security-Platform)
  and ["Firebase app architecture – Android stack"](https://dribbble.com/shots/27518650-Firebase-app-architecture-Android-stack),
  both flat layer diagrams; Ilker Durmaz's isometric stack of glowing planes and Method's isometric
  planes carrying tech logos (JS, React, PHP), both under Dribbble's
  [system architecture diagram](https://dribbble.com/search/system%20architecture%20diagram) search.
- Use for a person or a platform whose four steps are layers of one system. The request line
  shows what happens to a client's request, and it lands on the hire or sign-up CTA.
- Tools go in pills on each layer, three at most. The layer name is the step; a verb is optional.
- A label along the request line (`through` in the spec) names what carries the request through
  every layer, such as the AI agents in the th3r example.
- Next step if flat slabs feel plain: the isometric version from the references above, where each
  layer is a plane seen from 30° and the request drops through them. It costs legibility at phone
  width, so keep the flat version as the primary.

## cover

A blog or article cover has no steps. The title is the only core element: a kicker above it, a
handwritten note under it, the author at the foot, and one motif on the right that shows the post's
subject. Built for marketing/social-media's blog-cover sub-skill.

- The benchmark cover uses a risograph look: deep blue and fluorescent pink on warm paper, the title
  printed twice with the pink copy offset (misregistration), halftone dots, tilted print cards.
  The motif fans out thumbnails of the five layouts above, because that post is about them.
- The pink copy of the title sits in `data-zone="decor"`, so its contrast isn't benched; the ink copy
  carries the reading.
- Thai titles set in Kanit need room above: Thai ascenders and Kanit's overhang reach past the text
  box, so the layout insets the column by 8px.

## showcase

A work sample, centred: a kicker and title above, the work under them, a caption and tags below.
`images` (up to three screenshots of one project) puts the first large and stacks the rest beside
it at their own proportions, since a fixed frame would crop logos and headings; `client` adds a
sticker naming who the work was for. With no image the window shows a placeholder ("Coming soon"),
so the listing can go live before the first project and the same spec becomes the real sample later.

## orbit

A person's capabilities as a system map, for a profile cover: the name in the centre with a glow,
capability nodes on a dashed orbit (an icon disc, a label in the buyer's language, the platform's own
skill names under it), a spoke from the centre to each. `angles` places the nodes; leave a gap where
the platform puts the avatar. Fastwork's profile shows the full 16:9 on desktop and a ~2.9:1 band on
mobile with the avatar over its bottom centre, so bench it twice:
`bench.py cover.svg --safe-ratio 29:10 --clear 960,871,150` and `--safe-ratio 16:9`. Optional decoration,
drawn in the decorative zone so the bench ignores it: `circuits` (traces from the edges, 45-degree bends,
a pad at each end; keep them off the text) and `cat` (a small cat sitting on one node's card).

## halo

A profile cover where the platform's avatar is the hub: rings radiate from `hub` (the avatar's
centre, design units), capability icons sit on the rings with a label under each, the name and
tagline and site on the left, one big number on the right. Seen on integration-hub pages
(icons orbiting a centre logo); here the person replaces the logo. Put nothing at the hub: the photo
covers it on mobile. Space nodes so neighbours' labels don't meet near the top of the ring.

## Marketplace service images

What sellers put in a service's image gallery, from Dribbble's [fiverr gig image](https://dribbble.com/search/fiverr%20gig%20image),
[website mockup presentation](https://dribbble.com/search/website%20mockup%20presentation),
[how it works infographic](https://dribbble.com/search/how%20it%20works%20infographic) and
[pricing packages cards](https://dribbble.com/search/pricing%20packages%20cards) searches (2026-11-16).
A gallery reads in order, so each image does one job: what is sold, how it works, what it costs,
proof it was done before.

| Job | Pattern | Seen in | Note |
|---|---|---|---|
| What is sold | Bold service title, a short checklist of what's included, real work beside it | Subhan Khan (services checklist beside site screenshots, "open for free consultation"); Bhavana ("Figma UI/UX Design" over fanned page screenshots) | the checklist is the package's deliverables in buyer words; most gig images add a face photo, which needs the seller's own |
| What is sold | Service title over tool logos and a portrait | Nur Mohammad Rahim ("Full Stack Website Development") | the common Fiverr look; logos are the stack, so skip them when the listing avoids stack names |
| Proof | Screenshots in a device or browser frame (laptop, monitor, a browser bar with three dots) | New–Renew, ["MacBook Pro 16" Mockup"](https://dribbble.com/shots/27383395-MacBook-Pro-16-Mockup-LUX-15-New-Renew); Pranjali Sanap (site in a laptop with floating props) | a frame tells the eye "a real website" at thumbnail size; a browser bar is cheap to draw in SVG |
| Proof | Page screenshots tilted in perspective, fanned like printed pages | KL-Webmedia, ["The Perspective Mockup"](https://dribbble.com/shots/18333194-The-Perspective-Mockup); MarkeStac (template pages scattered around a monitor) | shows several pages of one site at once; tilt costs legibility, so keep one page flat |
| How it works | Three or four numbered cards in a row, an icon on each | Nur Hossen ("Transfer unlimited data by simple 3 steps") | the plainest process image; fits the 4:3 card crop well |
| How it works | A winding road with each step at a bend | Kate K8.S., ["Web Site Development Infographic"](https://dribbble.com/shots/5693414-Web-Site-Development-Infographic) | the most-liked process shot in the search; reads as a journey, takes more room |
| How it works | A vertical line with nodes, a screenshot beside each step | Sophia Yip, Ishan Singh ("How Gamma works") | the `rail` layout plus a picture per step |
| What it costs | Three package cards, the middle one raised, coloured and badged "most popular" | Monir ("Simple, transparent pricing"), Kevin (Basic / Professional), Omar Abela ("Our Packages", the middle card taller) | the decoy and anchoring pattern from pricing.md, drawn; prices and days must match the listing |

## Personal and freelancer banners

A person selling their own work on a marketplace (Fastwork, Fiverr, Upwork) needs three things a
product banner can skip: who they are, proof they are real, and that they are available.

| Pattern | Seen in | Take for a freelancer |
|---|---|---|
| Labelled facts row: WHAT / WHERE / HOW / WHEN under the headline | Oz Gultekin's portfolio in Inspo (`ozgur-design`) | turn "4+ years · Thailand · freelance" into labelled facts a buyer scans |
| A thin "Open for freelance" bar above everything | Bruno Cisco's portfolio in Inspo (`brunocis-co`) | an availability badge on the brand panel |
| Giant name filling the width | Bruno Cisco (`brunocis-co`), Dipsy (`eng-dipsy-team`) | the brand side at 120px when there is no logo |
| Portrait beside bold skill words and a chart | Anik Karmoker, under Dribbble's [freelancer cover](https://dribbble.com/search/freelancer%20cover) search | a photo builds trust on a people marketplace; needs the person's own photo |
| Hub and spoke: one centre node, services around it with mono labels | Studio Scale, under the [system architecture diagram](https://dribbble.com/search/system%20architecture%20diagram) search | "one person, many services" on a square post |

Fiverr's gig image is 550 × 370 px according to [Kapwing's guide](https://kapwing.com/resources/how-to-create-the-perfect-fiverr-gig-image-to-gain-customers);
Fastwork publishes no size, and its service pages show images in a 16:9 box (measured 840 × 473 on
the page, 960 × 540 served).

## Also seen, not built

Patterns from the same searches that fit other briefs:

| Pattern | Seen in | Fits |
|---|---|---|
| Verb chain headline: "Think it. Build it. Extend it." with no columns | n8n in Inspo (`n8n-io--features`) | a 4:1 cover where steps can't fit, only verbs |
| Giant wordmark filling the width, one line under it | Miro, ["GrowTree"](https://dribbble.com/shots/14282155-GrowTree-Freebie) | brand awareness, no steps |
| Text left, a mosaic or pixel grid right | Toms Stals, ["Web banner design for a domain company"](https://dribbble.com/shots/27812564-Web-banner-design-for-a-domain-company) | one idea plus texture |
| Numbered list left, one hero object right | PixelCraft Studio, ["Our Vision – Crypto Wealth Banner"](https://dribbble.com/shots/26555610-Our-Vision-Crypto-Wealth-Banner) | steps plus a product shot |
| Terminal or mono list of roles beside a portrait | Dribbble [github banner](https://dribbble.com/search/github%20banner) search | personal profile README |

## Research notes

- Dribbble search pages render with JavaScript, so a plain fetch returns nothing. Load them in a
  browser (headless Chromium works) and read the shot links and the screenshots.
- Dribbble reorders results between loads. Cite a shot by a link only when its title confirms the
  match; otherwise credit the designer and link the search.
- UI8 sits behind a bot check, so a script stops there. Browse it by hand if a template is needed.
- Under "banner" Dribbble shows mostly web heroes and ads. Searching the pattern ("process steps
  banner", "bento banner", "system architecture diagram") finds layouts.
- Take the composition from a reference. Its images, logos and copy never go into a banner.
