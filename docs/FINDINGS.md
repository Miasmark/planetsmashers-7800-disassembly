# Planet Smashers (Atari 7800, NTSC, 1990): findings

ROM: `Planet Smashers (NTSC) (Atari) (1990) (4E3B9E64).a78`, 128K SuperGame, header `$0012`
(SuperGame, bank 6 at `$4000`), TIA sound, no cart RAM, no POKEY. Work copy: `work/ps.a78`
(not to be shared).

Evidence tags: **(live)** watched in MAME (a tap, a RAM series, a poke that changed behaviour);
**(code)** read from the listing only; **(hint)** a guess. Addresses are `bank:address` as
`annotations.json` keys them: `f7` is the fixed bank at `$C000`, `b0`-`b5` the window at
`$8000`, `f6` bank 6 at `$4000`. Runs named below are in `work/runs/<name>/`, made by
`tools/run.py` (windowless MAME, `tools/run.lua`).

Contents: 1 waves, 2 bosses, 3 pool and collision, 4 frame and display lists, 5 backdrop,
6 banks, 7 sound, 8 other, 9 coverage, 10 dead ends and corrections, 11 not determined.

## 0. The game in one paragraph

A vertical shooter. Each of 7 levels is 14 waves of 20 seconds, then a wait for the screen to
clear, a warp, a level boss with a 70-second limit (levels 1-6) and an asteroid field; level 7
ends at a screen-wide final boss, then the ending. Enemies that get past the bottom drain a
second bar, the Earth shield; when it is gone the game is over. A saucer drops capsules (weapon,
shield, cloak, warp letters, extra ship). Two players alternate.

## 1. Waves and enemy behaviour

### The wave record: a threshold and three slot floors (live)

- `b1:B900` `LoadWave` builds a row index `dat1_B948[Level] + WaveIndex` (`B948` = 0, 14, 28 ...
  84: 14 rows a level, 7 levels, 98 rows) and reads four parallel 98-byte tables into zero page:

  | table | to | meaning |
  |---|---|---|
  | `b1:B94F` | `$43` | spawn threshold: a family spawns in a frame when `Random >= $43` |
  | `b1:B9B1` | `$44` | first slot the "homer" (type 6) may use; 0 = family off |
  | `b1:BA13` | `$45` | first slot of the "wanderer" (type 5) |
  | `b1:BA75` | `$46` | first slot of the "bomber" (type 4) |

- Each wave frame runs three spawn rolls, `f7:D46A` (homer), `f7:D0F3` (wanderer), `f7:CE23`
  (bomber). Each one: return if the player is not type 0 (dead or entering); draw a random byte
  and return if it is below `$43`; load X with the family's floor and return if it is 0; scan
  `ObjType,X` upward to `$1F` for a free slot; fill it in.
- **The floor is the cap.** A family with floor `$1D` can have three alive (`$1D-$1F`); `$14`
  gives twelve. Families share the top slots, so the caps overlap rather than add. There is no
  "alive" counter anywhere.
- **Difficulty is +1 on every non-zero floor** on Easy (`Difficulty` `$1A94,X` = 0): one enemy
  fewer per family (`B916`: `(Difficulty EOR 1) + floor, AND #$1F`). Nothing else in the wave
  code reads the difficulty. Elsewhere it changes what an asteroid costs the Earth shield
  (`f7:C6E0`: `$0100` on Easy, `$012C` on Hard) and is read at `f7:CC65` (capsule code, not
  followed).
- Rate: `$FF` = 1 in 256 a frame (0.23 a second), `$FE` 0.47/s, `$FD` 0.70/s, `$FC` 0.94/s,
  `$F8` 1.9/s, per family, while a slot is free.
- Evidence:
  - `long1` (40,000 frames, Easy): `$43-$46` at every wave equal the tables' rows with +1 on the
    floors (level 1 wave 0: `FE 1F 00 1F` from `FE 1E 00 1E`; wave 4: `FE 1D 00 1F`; wave 12:
    `FE 00 1D 00`; level 2 wave 0: `FD 15 00 00`).
  - `tools/slothist.py long1`: type 6 never below its floor (`$15` under floor `$15`, ten alive;
    `$1C` under `$1C`, four alive), type 4 only in `$1F`, type 5 in `$1D-$1F`.
  - Poke test `poke44` against `base44` (same inputs): holding `$44=$14` and `$43=$F0` gave type
    6 in slots `$14-$1F` with 12 alive at once (2,285 alive-snapshots against 69).

### The clock (live)

- A wave lasts 20 seconds of real time. `f7:FF63` `SecondsTimerTick` runs in the NMI: `$49`
  counts frames to 60, `$4A` seconds to `TimerPeriod` `$4C`, then `TimerFired` `$4B` is
  incremented. `f7:F809` sets the period (A = seconds).
- `f7:C312`: when `$4B` is non-zero the wave loop decrements it, increments `WaveIndex`
  `$47,X`, calls `LoadWave` and marks the HUD dirty. `long1`: `$47` stepped every 1,200 frames
  (358, 1558, 2758 ...), `$4C` = `$14`.
- At `WaveIndex` = 14 the phase moves on (`f7:C2DB`). Three warp capsules also end the level
  early (`f7:C2E1`: `$1A54` positive goes to `L_C32B`). (code)
- The timer is per player: on death its four bytes are saved to `$1A78,X*4` (`f7:F705`) and
  restored when that player's turn starts (`f7:F631`), so the other player's turn costs no wave
  time. (code)

### The phase machine (live for phases 0-5)

`f7:C2B1` dispatches on `Phase` `$B4,X` through the RTS table at `f7:C2C4`:

| phase | routine | what |
|---|---|---|
| 0 | `f7:C2D2` | waves |
| 1 | `f7:C332` | wait until slots `$12-$1F` are all free |
| 2 | `f7:C363` | warp out: `StarPeriod` runs down to 0, wave index to 14 |
| 3 | `f7:C3BC` | level boss, timer 70 s (`LDA #$46`) |
| 4 | `f7:C470` | asteroid field (asteroids from slot `$14`), bonus saucer if every one was shot (`$42` = `$41`) and the player was not hit |
| 5 | `f7:C527` | final boss (taken instead of 3 when `Level` >= 6, `f7:C3AF`) |
| 6 | `f7:C5AE` | end of turn |

`long1`: 0 until frame 17,158, then 1, 2 (17,383), 3 (17,392, `BossId` 0, 4 pieces), back to 0
at 21,607 with `Level` 1. A boss that times out skips phase 4 (`f7:C3E2`); a killed one goes to
4 (`bosskill`: phase 4 at 18,022).

### How the ramp is spread (code, tables decoded with `tools/hexd.py`)

- Level 1: threshold `$FE` throughout; homers floor `$1E` then `$1C` (2, then 4); bombers `$1E`;
  wanderers appear only in the last two waves.
- Level 2: homers open and close the level at floor `$14` (12 at once) with threshold `$FD`/`$F8`.
- Level 5 is a staircase: all three floors step `$1F, $1E ... $14` wave by wave.
- Levels 6-7 mix floor `$14` waves with empty families and thresholds from `$FE` to `$F8`.
- Per wave within a level (index = `WaveIndex`): `f7:F2B1` star period `4,4,4,4,4,3,3,3,3,2,2,2,1,1,1`
  (the stars speed up toward the warp; live in `long1`: 4 to 3 at wave 5, 2 at 9, 1 at 12), and
  seven more 15-byte tables `f7:F248-F2A2` that redraw a HUD gauge.
- Per level: `f7:F64F` `2,4,5,6,7,9,10` caps the weapon level a capsule may raise (below);
  `f7:CB30` points at the level's capsule order.
- No loops: after level 7's boss the ending runs (`f7:F903`), then the title.

### Enemy behaviour is code, one handler per type (code)

`f7:DE3D` `RunObjects` walks X from `$1F` to 0; a slot whose type has bit 7 clear is dispatched
through the RTS table `f7:DE62` (35 types); every handler ends `JMP ObjNext` (`f7:DE5D`).
Paths are not stored as data. The three wave families:

- **Homer, type 6** (`f7:D4F6`). Falls at `$C0/256` a frame (8.8 fraction in `ObjF`). Every 8
  frames (`ObjC`) `f7:D5A2` sets its x velocity to `player x + 7 - own x` taken as a signed 8.8
  fraction, with a floor of +/-`$60`: proportional homing, slower near the player. If the player
  is dead or cloaked it turns into a type 3 drifter. Past the bottom it costs the Earth shield
  `$0200` (`EarthDamage` index 4) and is freed. Two hits to kill (`ObjG` = 2).
- **Wanderer, type 5** (`f7:D1CE`, `NewWaypoint` `f7:D317`). Enters at one of 32 points on the
  screen's edge (`f7:D18E`/`D1AE`). Picks a random point, walks to it one pixel a frame along a
  Bresenham line (`|dx|`, `|dy|`, step signs, error = major/2, steps left = the major length),
  fires an aimed shot on arrival (`f7:D285`, type `$0A`, the same line maths at 2 pixels a
  step), picks another point. Cloaked or dead player: half the time it becomes a drifter.
- **Bomber, type 4** (`f7:CEAB`). Four-state path through the RTS table `f7:CFBD` (across, down
  16, back, up). Drops a bomb (type 7) each time its x reaches the player x it last sampled
  (`f7:CEE2`), and samples again.
- Others: asteroid type 3 (`f7:C6A6`, spawned by `f7:C5FF` every `$A0` wave frames into slots
  from `$18`, four sizes); saucer type 1 in slot `$13` (`f7:C7AD`: 1 chance in 256 a frame while
  the slot is free); capsule type 2.
- Animation: `f7:D4FC`: every 4 frames `ObjGfxLo ^= ObjD`: two frames from one XOR byte.

## 2. Bosses

### Level bosses: a block of slots, loaded as rows (live for the counter and the kill, code otherwise)

- `f7:F79C` `LoadBoss` switches to bank 3 and calls `b3:9B00` `BossLoad` with the boss number.
  `b3:9B5A` holds 4 bytes a boss: **the bank its art is in** (3, 3, 3, 3, 4, 4; returned in A and
  stored to the bank register, so that bank stays in during the fight), **piece count N** (5, 7,
  9, 10, 11, 10), and a pointer to the definition. `b3:9B72` gives `BossPiecesLeft` `$90`
  (4, 6, 6, 9, 10, 7: pieces with hit points).
- The definition is **14 rows of N bytes, copied straight into the slot arrays** at slots
  `$20-N .. $1F`: type, x, y, graphics low, graphics page, palette/width, hit-box x offset, y
  offset, box height, box width, hit points (`$FF`/negative = not a target), gun x offset
  (negative = no gun), gun y offset, wreck graphics low. 70 to 154 bytes a boss.
- **One brain.** Every piece has the boss's type (`$10+`), but the handler (`f7:E207` for boss
  0; `E2E3`, `E3B3`, `E483`, `E559`, `E647` are the same shape) stores the boss's first slot in
  `CurSlot` before it returns, so the object loop skips the other pieces. It runs once a pass.
- **Firing, one piece a pass.** `$1A75` walks the boss's slots round robin. The piece of the
  pass fires if it is alive, has a gun, `Random >= $E0` (1 in 8) and a shot slot is free from
  `$0E` down to `$0A` (`f7:CE9F`). Every fourth pass (`$99 AND 3`) the shot is aimed at the
  player (`f7:E8B6`), unless cloaked; otherwise it falls straight (type `$1C`).
- **Movement script.** Pairs (count, move) at `f7:E2C9` and the like; count 0 = jump to the
  index in the next byte. The move indexes a 9-entry RTS table per boss (`f7:E2B7`): stop and
  eight directions, each an unrolled run of `INC`/`DEC` on the pieces' absolute x and y cells
  (`f7:E922-EAC5`), **entered at a different point for each boss size** so one run of code
  serves 5 to 11 pieces.
- **Speed by pieces left.** The boss moves every `dat_E8AB[BossPiecesLeft]` passes:
  `4,3,2,1,1...`, so every pass with three or more pieces, every second with two, every third
  with one. Read as mercy on the last piece (hint).
- **Time limit.** `f7:E858`: when the 70 s timer fires the boss flies off the bottom, the Earth
  shield loses `$4000` (index 6) and the level carries on without the asteroid field. `long1`:
  boss 0 stayed 4,215 frames and left. (live)
- **Death.** `BossPiecesLeft` = 0 goes to `f7:E82E`: score from `f7:E84C`/`E852`, then
  `b1:BB00` plays a five-step blast from 5-byte records (`b1:BBC5`) with `BACKGRND` flashes
  from `b1:BBBC`. Poke test `bosskill`: writing `$90=0` at frame 18,000 added 5,000 to the
  score on the next frame, cleared `BossId` 20 frames later and moved to phase 4. (live)

### Hits on a level boss (code)

With `BossId` >= 0 a player shot tests **only the boss's slots** (`f7:DA47`, first slot from
`f7:E8A5` = `$1B,$19,$17,$16,$15,$16`), not the 31 slots of the ordinary test. A hit decrements
the piece's hit points (`f7:DB6D`). At -1 the piece's art becomes its wreck art, the shot turns
into a blast (type `$0C`) and 1,000 points are added; otherwise the shot turns into a spark
(type `$0E`). Boss 5 also tests slots from `$15` the ordinary way (`f7:DA38`).

### The final boss: a picture in the list heads, eleven zones (live)

- It is not made of objects. `f7:FA4C`/`FAA9` build it as **fixed heads of the zone lists**:
  six 4-byte headers a zone (24 bytes, `ZoneHeadLen` `$B1` = `$18`), five zones tall, art in
  bank 5, which stays in the window for the fight (`final`: `$B7` = 5).
- Scroll-in: the star head of every list is first copied `$26` bytes up and the DLL's pointers
  moved there, which frees `$00-$25` of each list to be built unseen. Then each row is drawn
  by adding 1 to every header's high byte 16 times (`f7:FD53`; rows start at page `$70` or
  `$90`, which read blank, and end at `$80` or `$A0`), and each time a row is home the rows
  are copied one list down and the next row loaded from `f7:FCAB-FD3B`.
- Hits: `f7:DBB0` tests a shot against 11 zones in four arrays: `ZoneHp` `$1AA0`, `ZoneRight`
  `$1AAB`, `ZoneWidth` `$1AB6`, `ZoneBottom` `$1AC1`, loaded from `b1:BF2A`.
- **Locked weak points.** Hit points start `0E 0E 0E 0E 80 1D 80 1D 80 02 02`. A negative byte
  is skipped by the test (`BMI`), so `$80` is "not yet a target" and `$FF` is "dead" with the
  same branch. When a zone dies its own handler (RTS table `f7:DC19`, 11 entries) writes the
  wrecked art's addresses into the fixed list bytes (`f7:DCAE`: `$2300`, `$2302`, `$2380` ...)
  and, when both of a pair are dead, writes `$1D` into a locked zone to open it (`f7:DC59`).
- `BossPiecesLeft` starts at 9. `final` (poked to level 7): hit points counted down one a hit,
  the `$80` zones stayed `$80`, `$90` went 9, 8, 7 as zones reached `$FF`. A zone dies on the
  hit after it reaches 0, so `$0E` is 15 hits.
- Its turrets are ordinary objects in slots `$1B` and `$1F` (types `$1F`, `$20`: state machines
  of 18 and 16 states, `f7:EAC6`, `f7:EDE1`), launched by `f7:C554`. Not read in detail.

## 3. Object pool and collision

### The arrays (live for the slot map)

32 slots, sixteen parallel arrays of 32 bytes at `$1800-$19FF`:

| address | name | use |
|---|---|---|
| `$1800` | `ObjType` | bit 7 set = free (`$FF`); else the handler index |
| `$1820` | `ObjX` | 0-`$9F` on screen; `$A0-$EF` = not drawn |
| `$1840` | `ObjY` | zone = y >> 4, 11 zones |
| `$1860` | `ObjGfxLo` | graphics low byte |
| `$1880` | `ObjGfxPage` | graphics page: `$60` common art, `$80`/`$A0` banked art |
| `$18A0` | `ObjPalWidth` | header byte 2; bit 7 swaps palette 0-3 for 4-7 |
| `$18C0`, `$18E0` | `ObjBoxW`, `ObjBoxH` | hit box (bosses: box offsets) |
| `$1900-$19E0` | `ObjA`-`ObjH` | per-type state (velocities, fractions, timers, hit points) |

Slot map (`tools/slothist.py long1`, 2,000 snapshots):

| slots | holder |
|---|---|
| 0 | the player (type 0; 8 while entering; 9 exploding, its debris in 0-7) |
| 1-9 | the player's shots: 1 up to `ShotTopSlot` `$79`, which grows with the weapon level |
| `$0A-$12` | enemy shots and bombs (types 7, `$0A`, `$0B`, `$1C`) |
| `$13` | the saucer, then its capsule (types 1 and 2, never anywhere else) |
| `$14-$1F` | enemies by floor; asteroids from `$18`; boss pieces at the top |

### Finding and freeing (code)

- Free = `LDA #$FF / STA ObjType,X` (`f7:DEA8`). No free list.
- Spawners scan upward from their floor (above). Shots scan downward from a ceiling:
  `f7:D79A` from `ShotTopSlot` to 1, `f7:CE9F` from a given slot down to `$0A`. A failed scan
  drops the spawn.
- **Effects take no slot.** A destroyed enemy's own type is rewritten to a blast (`$0D`,
  `f7:E121`, script of (frames, graphics, palette) triples at `f7:E1DC`, negative ends and
  frees) or the in-place blast `$0F`; the shot that hit turns into the spark `$0E`; the saucer
  turns into its capsule (`f7:CA2F`). An effect can never fail for want of a slot.

### Shot against enemies (code; cost live)

- `f7:D9DD` (small shots) and `f7:DAA1` (big shots): Y from `$1F` down to 1, skip free slots
  and **any type >= 8**: the type numbers are ordered so that 1-7 are exactly the things a shot
  can hit (saucer, capsule, asteroid, the three families, bombs). Then a box test against the
  target's `ObjBoxH`/`ObjBoxW`, and `f7:DE0E` dispatches on the target's type through the RTS
  table `f7:DE1E` (hit handlers: `f7:D062` two-hit enemies, `f7:C76D` asteroid, `f7:CA2F`
  saucer, `f7:D0CF` bomb ...).
- No cells, no spreading over frames, no early out beyond the type test. Measured (`cb1`, up to
  3 shots, about 16 objects): 400 to 1,300 cycles a frame in `f7:D7B6-DE3C`.
- Scores come from a class stored in the object at spawn (`ObjF` indexes `f7:C7A7`:
  25, 50, 75, 100, 300, 500).

### Enemy against player (code)

Each enemy handler carries its own copy of the test (`f7:D552`, `CF09`, `D239`, `C6EF`, and
`f7:D902`/`D93F`/`D97C` for the three shot sizes): skip if the player's type is not 0, then
`|dy|` and `|dx|` against constants on one side and the enemy's box on the other. A hit turns
the enemy into a blast and calls `f7:F6E7` `PlayerHit`: one shield point off; with none left the
player dies unless `$1A74` is set. About eight copies of some 60 bytes.

## 4. Frame architecture and the display-list builder

### One interrupt a frame, and it does the drawing (live)

- The DLL (`$1F00`, image at `b1:9656`): 16 and 9 blank lines, 11 zones of 16 lines (`$4F`:
  holey DMA 16) with lists at `$2200, $2280 ... $2700` (128 bytes each), an 8-line HUD bar
  (`$2780`), 2 blank lines, **an 8-line text zone with the DLI bit** (`$27C0`), 16 and 9 blank.
- The NMI (`f7:FD99`) polls Reset and Select, then `JMP ($1A50)`: `f7:FE02` in play, `f7:FEED`
  on title and end screens, `f7:FF23` paused. `fp1`: entered on raster 227 in 8,299 of 8,299
  frames.
- `f7:FE02`, in order: CTRL `$4B` (320 text) and the text colour; seconds timers; `b3:B800`
  sound start if a request is posted; `b4:9000` sound tick; **`b3:9000` the display-list
  build**; `b3:B000` the stars every `StarPeriod` frames; CTRL `$58` (160, two-byte characters)
  and the colour back; blink timers; **restore the bank from `BankShadow` `$B7`**; `INC $70`.
- **It switches banks three times inside the interrupt** (`f7:FE45`, `FE4D`, `FE55`) and puts
  the main program's bank back at `f7:FEB0`. Main-thread code keeps `$B7` current by storing it
  before every switch (`LDA #n / STA $B7 / STA $BFFF`). This is the SuperGame trick the BankSet
  rules forbid.
- The main loop waits for the NMI with `f7:F83C` (`LDA $70 / CMP $70 / BEQ`). No frame debt,
  no skipped frames: `fp1` saw exactly one pass a frame for 8,299 frames with 5 to 24 objects.

### The builder (code; timing live)

- `b3:9000`: if `BuildGate` `$73` is 0, return. `DEC $73` (so an NMI arriving during the build
  skips it: a re-entrancy guard), set the 11 fill bytes `$4F-$59` to `ZoneHeadLen`, then for Y
  = `$1F` down to 0: skip free slots and x in `$A0-$EF`; `LDX ObjY,Y` and push
  `PlacerByY[x]` (`b3:906D` high bytes, `b3:916D` low bytes, 512 bytes) for an RTS dispatch.
- **24 unrolled placers** (`b3:926D-9736`), two per zone plus the edges: "y is a multiple of
  16" writes one 4-byte header; any other y writes two, into that zone and the next. Each
  placer has its zone's list address and fill byte hard-coded: `LDX $4F / LDA ObjGfxLo,Y / STA
  $2200,X / INX ...`. The header is graphics low, palette/width, `ObjGfxPage | (y AND 15)` (minus
  `$10` in the lower zone), x.
- At the end a zero is written after each list's last header (`b3:9031`).
- **No overflow check and no DMA check.** A list holds the head (10 bytes) and 29 headers;
  nothing stops a thirtieth. Nothing is dropped or flickered when a zone is crowded.
- Vertical clipping needs no holes for the common art: sprites are in pages `$60-$6F` (bank 6
  at `$4000`) and **the 4K blocks on either side, `$5000` and `$7000`, are all zeros**
  (`tools/bankpic.py`: 100% zero). Banked art (`$80`, `$A0` pages) relies on holey DMA's holes
  at `$9000` and `$B000`.
- Every sprite is 160B: each list's head ends with a 5-byte header at x = `$E0` whose only job
  is to set write mode 1 for the 4-byte headers after it (`b1:96D9`: `00 C0 1B 1F E0`). The
  empty list at `$1F36` is the same dummy.
- Timing (`fp1`, `cb1`): the NMI lasts 25 raster lines with 5 objects and up to 54 with 23,
  about one line an object, so it ends by raster 18 of the next frame at worst; the first drawn
  zone starts at raster 41. The build itself took 2,240 to 2,870 cycles a frame with about 16
  objects alive: roughly 150 cycles an object, plus about 350 fixed.
- The lists are built from the live arrays while the main program may be half-way through
  moving an object. Nothing guards that.

### The frame's budget (live, `cb1`: probes/cyclebudget.lua, about 16 objects alive)

| share | cycles a frame |
|---|---|
| MARIA's DMA | 12,200-12,900 (42%) |
| main program idle in `WaitNmi` | 9,300-11,400 |
| NMI | 2,700-3,400, of which the list build 2,240-2,870 |
| object handlers `f7:DE3D-F0ED` | 1,150-1,300 |
| shot handlers and their tests | 400-1,300 |

### HUD (code)

Fixed lists at `$2780-$27CF` copied from `b1:9789` and poked in place by `f7:F115` (when
`HudDirty` `$86` is set) and `f7:F47C` (score digits, when `ScoreDirty` `$87`). Leading zeros
are blanked (`f7:F4EB`).

## 5. Backdrop: stars as a character map

- (code) `$1B00` is a map of 20 columns by 11 rows. Each zone list starts with a 5-byte
  indirect header onto its row (`b1:96D9`: low = row * 20, `$60`, `$1B`, `$EE` = palette 7,
  18 characters, x = 8). CTRL `$58` makes characters two bytes wide.
- 18 stars, **one per column** (`StarPos` `$9B,X` = row * 20 + X). The character set has the
  same dot at each height of the cell, so a step is `map[pos] += 2`; at the end of the star's
  set the cell is blanked (`$E0`) and the star moves 20 bytes on, into the next zone
  (`b3:B000`). Stars come in classes (sets starting `$80`, `$A0`, `$B0`, `$C0`, `$CC`, `$D6`)
  for brightness and step.
- Speed is one number: the NMI runs the step every `StarPeriod` `$72` frames; the warp is the
  period running to 0.
- **Cost (live).** CPU: 18 short steps every 1 to 5 frames. MARIA: with the star header cut to
  one character (poke test `cb2`, bytes `$2203, $2283 ... $2703` held at `$FF`) DMA fell from
  about 12,500 to about 5,700 cycles a frame. **The star map costs about 6,800 CPU cycles a
  frame, 23% of the frame**, whatever is on screen.

## 6. Banking

| bank | holds | evidence |
|---|---|---|
| 0 | the title picture, all 16K as a bitmap | live: MARIA read `b0:$8000-$BFEF` on the title |
| 1 | `$8000`/`$A000`: big message letters and blast art. `$9000`: game screen set-up (`9051`), palettes (`915C`), DLL and list-head images (`9656`, `96D9`), menu code (`9E00-9F5D`). `$B000`: end text (`B7B0`), wave tables (`B900-BAD6`), boss blast (`BB00`), final boss zones (`BF00`) | code; picture by `tools/bankpic.py` |
| 2 | a full-screen picture for the end sequence | live: bank 2 in under the title NMI at `f7:FF06`; picture by render (hint for which screen) |
| 3 | `$8000`/`$A000`: art of bosses 0-3. `$9000`: list builder (`9000-9736`), messages (`9800`), boss loader and definitions (`9B00`). `$B000`: stars (`B000`), set-up (`B200-B300`), sound start (`B800`) | code; bank byte in `b3:9B5A` |
| 4 | `$8000`/`$A000`: art of bosses 4-5 (hint, from the bank byte). `$9000`: sound tick (`9000`), title music (`9100`), streams, title code (`9D00-9F00`). `$B000`: streams | code |
| 5 | the final boss's art (`$8000` and `$A000` blocks used) | live: `$B7` = 5 during the fight |
| 6 | fixed at `$4000`: characters at `$4000`, zeros at `$5000`, sprites at `$6000`, zeros at `$7000` | live: MARIA read only `f6` in play |
| 7 | fixed at `$C000`: all game logic; 85% code, the rest tables | disassembly |

- **Art in the even 4K blocks, code and tables in the odd ones.** In banks 1, 3 and 4 all code
  sits at `$9000-$9FFF` and `$B000-$BFFF`: the blocks MARIA reads as zero in a holey-16 zone.
  Nothing is wasted on padding there.
- Switches from the main program: always `LDA #n / STA $B7 / STA $BFFF` in bank 7 (25 sites,
  listed by `disasm.py`). In play the window holds bank 1 (wave tables; the common art is in
  bank 6, so nothing drawn depends on it), bank 3 or 4 during a level boss, bank 5 for the last.
- Switches in the NMI: section 4.
- `f7:F0EE` copies bank 6's 16K to `$4000-$7FFF` at reset. On this cart that is a write to ROM
  and does nothing; it reads as written for a board with RAM at `$4000` (hint).
- Stage data and art are **not** paired by level: all wave tables are in bank 1, all enemy art
  in bank 6. Only the bosses pair a definition (bank 3) with art in a named bank.

## 7. Sound (code)

- One request byte, `SoundRequest` `$BA`: an id, `$7F` = silence both, negative = nothing
  posted. The NMI calls `b3:B800` while it is non-negative.
- `b3:B877`: two bytes an id, **the stream for voice 0 and the stream for voice 1** (`$FF` =
  leave that voice alone). So an id fixes its own channels; there is no allocator and no
  priority. The newest request wins, except that the shot's sound is posted only when the byte
  is negative (`f7:D7AD`).
- In play (`b4:9000`): a stream is 4-byte steps, AUDC, AUDF, AUDV, frames; frames = 0 ends.
- Title music (`b4:9100`): 5-byte records, a tempo divider (`$1AFD`/`$1AFE`) and an envelope
  stepped through `JMP ($1A6F)`. Not decoded further.
- Against the `7800-sound-drivers` skill: this is its "Mailbox" pattern (Midnight Mutants) with
  the id-to-stream-pair table added. Nothing better than the skill's allocators.

## 8. Other

- **Capsule order with a need test** (code). `f7:CB30` gives each level a ring of 40 capsule
  kinds (`f7:CB40`, 280 bytes). `f7:CA4C` takes the next kind and dispatches (`f7:CA68`); each
  kind first asks whether the player needs it and otherwise moves on to the next: warp letter
  only before wave 8 (`CA74`), weapon only below the level's cap `f7:F64F` (`CA94`), shield
  below 6 (`CAB6`), cloak below 6 (`CAC8`), extra ship below 9 and once a level (`CADA`),
  points always (`CB11`).
- **Weapon level** `$7C` 0-10 picks the fire pattern through `f7:D608` (one shot, one big shot,
  three, three big), the autofire period (`f7:CDAF`) and how many shot slots there are
  (`f7:CDBA`). Dying costs two levels (`f7:F5BC`).
- **Earth shield**: 16 bits at `$82/$83,X`; `f7:F4FF` subtracts `f7:F52F[X]` (`$0100`, `$012C`,
  `$0200`, `$4000`); at zero the lives are zeroed.
- **Cloak**: button 2 spends one (`f7:DF3A`) for 20 s (`$4D/$4E`); the families test `$4D` and
  stop aiming or turn into drifters.
- **Score**: 4 BCD bytes a player at `$1A5C,X*4`, three entry points for three magnitudes
  (`f7:F7AC`, `F7BF`, `F7E1`), a dirty flag for the digits.
- **Two players** alternate; all per-player state is indexed by `CurPlayer` `$75` (wave,
  level, phase, lives, weapon, warp letters, timers).
- **Random** `f7:F7EC`: `new = $5B + $5E + $5F + carry`, a five-byte shift. The carry is
  whatever the caller left, and the NMI calls its own copy (`b3:B0E7`) for the stars, so the
  sequence depends on timing.
- **Reset and Select in the NMI** (`f7:FDB3`): the handler pulls the return address and pushes
  `$C028` or `$C0E4`, so the RTI lands in the restart code.
- **Attract mode** plays the game with random stick bytes (`f7:DEC5`, table `f7:DEB0`).

## 9. Coverage

| space | traced as code | notes |
|---|---|---|
| f7 | 13,946 of 16,384 bytes (85.1%), 6,014 instructions | the other 2,438 bytes are 54 table ranges; the large ones are named |
| b3 | 2,376 bytes (14.5%) | builder, stars, boss loader, sound start |
| b1 | 1,047 bytes (6.4%) | set-up, menu, wave loader, boss blast |
| b4 | 577 bytes (3.5%) | sound; title code |
| b0, b2, b5, f6 | none | graphics (rendered with `tools/bankpic.py`) |

- `verify.py`: round trip passes.
- Entry points came from the vectors, three 20,000-frame execution traces of random play
  (`work/runs/xt1-3`, merged in `work/xt_merged.log`), the RTS tables resolved by
  `tools/rtstables.py` (14 tables in f7), and the builder's table.
- **Read closely**: the phase machine, spawners, types 0, 3, 4, 5, 6, 7, the shots, all hit
  tests, boss 0's brain and the shared boss helpers, the final boss's build and zones, HUD,
  NMI, builder, stars, sound tick. **Skimmed or not read**: saucer and capsule handlers
  (`f7:C828-CE22`), types `$0A-$0C`, `$1D`, the final boss's turrets (`f7:EAC6-F0ED`), bosses
  1-5 beyond their shape, menu and end-sequence code, title music.
- Data blocks in banks 1, 3 and 4 are declared only where named in `annotations.json`; the rest
  of those banks lists as bytes.

## 10. Dead ends and corrections

- **The floors were first read as enemy types.** The values `$14-$1F` and the `AND #$1F` look
  like type numbers. The spawners use them as the start of a slot scan; the poke test settled it.
- **"The logic slows down under load" was wrong.** A first trace showed 486 passes of the wave
  frame in 600 frames. The other 114 were the death sequence's own loop (`f7:F537`). The frame
  probe shows one pass a frame at every load seen.
- **So the boss's divider is not slowdown compensation**, which was the first guess for
  `dat_E8AB`. It simply slows the boss when few pieces are left.
- **The star map's DMA was first estimated from the cost table** at about 8,100 cycles a frame.
  Measured: about 6,800.
- **`dyn.py` left 409 executed instructions unreached**: the builder's placers, reached only
  through a split high/low RTS table. They were added from the table by a script.
- **Port tags**: the first `run.lua` used `:joysticks`; the fork's tags are upper-case.
- **`init.py`'s 16.6% for f7** was the vectors alone; almost everything else hangs off RTS
  tables.
- **Holding fire in the first manual run** showed little; the scripted random player with
  `$1A74=1` (no death) and `$83=$7F` (Earth shield held) was what reached the bosses.

## 11. Not determined

- What bank 5's `$9000` and `$B000` blocks hold (they render as art, but a holey-16 zone cannot
  show them), and which screen bank 2's picture is.
- The final boss's turret machines and what `$AD`/`$AE` do there.
- Whether a zone list can overflow in real play (30 objects in one zone).
- The warp letters' matching rule (`$1A52-$1A5B`, table `b3:9F00`).
- Whether `Random` is uniform; spawn rates above are from the thresholds, not measured.
- Nothing was run on hardware or the Pocket core, and the PAL build was not looked at.
