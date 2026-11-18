# Planet Smashers (Atari 7800) disassembly notes

An annotated disassembly project for *Planet Smashers* (NTSC, Atari, 1990; `Planet Smashers (NTSC) (Atari) (1990) (4E3B9E64).a78`, 128K SuperGame).

## How this was made, and how far to trust it

This is the output of **one automated research pass** on 2026-11-18: a single AI agent
session (Claude, working through the a7800-toolkit and MAME) given a list of questions and
about half an hour, not a long-running hand disassembly like
[galaga-7800-disassembly](https://github.com/Miasmark/galaga-7800-disassembly) and its
siblings. A second session then checked the report's main tables and routines against the
ROM's bytes; they matched. Nothing here was checked on a console.

Treat a **live** tag as "one agent saw this in MAME once", a **code** tag as a reading, and
the coverage figures below as what the tracer reached, not what was understood.

## Effort: a deep single-game pass

| | |
|---|---|
| Session | one agent, about 28 minutes, 114 tool calls |
| Questions asked | waves and enemy behaviour as data; bosses; the object pool and collision; the frame and the display-list builder; the backdrop; banking; sound |
| Coverage | fixed bank 85.1% traced as code (the rest is 54 table ranges); bank 3 14.5%, bank 1 6.4%, bank 4 3.5%; banks 0, 2, 5 and 6 are graphics. Round trip passes |
| Read closely | the phase machine, the spawners, the three enemy families, shots, every hit test, boss 0's routine, the final boss's build and zones, the NMI, the list builder, the stars, the sound tick |
| Skimmed or not read | saucer and capsule handlers, the final boss's turrets, bosses 1-5 beyond their shape, the menu, the title music |
| Live checks | RAM series over 40,000 frames, poke tests (a wave's slot floor, a boss kill), cycle budgets, 120 labels |
| Not determined | bank 5's odd blocks, the warp letters' rule, whether a zone list can overflow in play |

## What is here, and what is not

- `annotations.json`: entry points, labels, RAM names, data blocks and comments, in the
  [a7800-toolkit](https://github.com/Miasmark/a7800-toolkit)'s format.
- `docs/FINDINGS.md`: what the code does, with addresses, record formats and an evidence
  tag on every claim: **live** (watched in MAME: a tap, a trace, a RAM model, a poke that
  changed behaviour), **code** (read from the listing only), **hint** (a guess). Dead ends
  and corrections are kept in it.
- `tools/`: the probes and scripts the findings were made with.

**No ROM is here, and no listing.** A listing is the game's machine code in readable form;
it is rebuilt from `annotations.json` and your own legally owned dump with the toolkit's
`disasm.py`, and checked byte for byte with its `verify.py`. Captures, memory dumps,
renders of the graphics and traces are left out for the same reason.

## Running the tools

The scripts look for three things in the environment:

| Variable | What | Default |
|---|---|---|
| `A7800_ROMS` | the folder with your ROM dumps, named as below | `roms` |
| `A7800_TOOLKIT` | the a7800-toolkit's `tools` folder | `a7800-toolkit/tools` |
| `A7800_MAME` | a MAME with the Atari 7800 driver | `a78.exe` |

The live runs were made on [Miasmark/mame-Atari8bit7800](https://github.com/Miasmark/mame-Atari8bit7800),
windowless (`-video none -sound none -nothrottle`).

## Licence

MIT (see `LICENSE`) for the annotations, the findings and the tools. It does not cover the
games, which belong to their owners; nothing of theirs is distributed here.

## The session's own notes

A byte-identical disassembly of *Planet Smashers* (NTSC, Atari, 1990, 128K SuperGame with bank 6
at `$4000`), made with the a7800-toolkit and MAME (the Atari fork) as the instrument.

**The ROM is not part of this project.** `work/ps.a78` is a local work copy of
`Planet Smashers (NTSC) (Atari) (1990) (4E3B9E64).a78`; do not share it. The listing in `src/`
is generated from `annotations.json` and the ROM.

## Layout

| path | what |
|---|---|
| `annotations.json` | entry points, labels, RAM names, comments, data blocks: all the judgement |
| `src/` | generated listing, one file per space (`f7` fixed bank, `b0`-`b5` window, `f6` bank 6) |
| `docs/` | `FINDINGS.md` |
| `tools/` | this project's scripts |
| `work/` | the ROM copy, traces, runs (`work/runs/<name>/`), bank pictures (`work/gfx/`) |

## Regenerating

```
sh tools/regen.sh        # disasm.py + verify.py: must print ROUND-TRIP PASSED
```

The toolkit is expected at `Documents\Atari 7800\a7800-toolkit` (used read-only).

## Tools

| script | what |
|---|---|
| `tools/run.py NAME KEY=VALUE...` | one windowless MAME run of `tools/run.lua` in `work/runs/NAME` (never opens a window) |
| `tools/run.lua` | random or scripted player, pokes, held bytes, peeks, RAM snapshots, write and read taps, execution coverage, a frame probe, and `PS_ALSO` to load a toolkit probe beside it |
| `tools/slothist.py RUN` | object types by slot, and by wave parameters, from a run's RAM snapshots |
| `tools/fpstats.py RUN` | main-loop passes a frame and the NMI's length by number of live objects |
| `tools/rtstables.py SPACE` | entry points from `LDA tbl+1,i / PHA / LDA tbl,i / PHA / RTS` dispatch tables |
| `tools/compact.py SPACE A0 A1` | a dense view of a range of the listing |
| `tools/hexd.py BANK ADDR LEN` | hex dump of ROM bytes as mapped |
| `tools/bankpic.py` | every bank's 4K blocks drawn as 16-line strips, and their share of zeros |
| `tools/ann.py` | add entries, labels, RAM names, comments, blocks to `annotations.json` |

## Coverage

| space | traced as code |
|---|---|
| f7 (fixed, all game logic) | 13,946 of 16,384 bytes (85.1%); the rest is 54 table ranges |
| b3 | 2,376 bytes (14.5%): display-list builder, stars, boss loader, sound start |
| b1 | 1,047 bytes (6.4%): screen set-up, menu, wave loader, boss blast |
| b4 | 577 bytes (3.5%): sound, title code |
| b0, b2, b5, f6 | none: graphics |

Not every routine in f7 has been read; the findings say which were.

## Runs worth keeping (in `work/runs/`)

| run | what it shows |
|---|---|
| `long1` | 40,000 frames with no death: the wave parameters against the tables, the phases, a boss timing out |
| `poke44`, `base44` | the slot floor and threshold poke test |
| `bosskill` | a level boss killed by zeroing its piece counter |
| `final` | level 7's boss reached by poke: zone hit points counting down |
| `fp1` | passes a frame and NMI length by object count |
| `cb1`, `cb2` | the cycle budget, and the same with the star map cut to one character |
| `xt1`-`xt3` | execution coverage of random play |
