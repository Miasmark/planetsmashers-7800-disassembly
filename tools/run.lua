-- run.lua -- windowless scripted run of Planet Smashers for the probes in this project.
-- Environment (all optional):
--   PS_FRAMES   frames to run (default 3600)
--   PS_SEED     seed for the pseudo-random stick/fire player (default 1); PS_PLAY=0 leaves inputs alone
--   PS_START    "f1,f2,..." frames at which fire is pulsed for 10 frames (default 125,345)
--   PS_XT       file: execution coverage log in exectrace.lua's format (slow)
--   PS_RAM      file: binary RAM snapshots (zp $40-$FF, $1800-$1FFF, $2200-$27FF) every PS_RAMEVERY frames
--   PS_RAMEVERY default 60
--   PS_SNAP     every N frames a screenshot (0 = none)
--   PS_POKES    "frame:addr=val,addr=val;frame:..." hex addr/val, written at that frame
--   PS_LOCK     "addr=val,addr=val" written every frame (cheats)
--   PS_LOCKFROM frame from which PS_LOCK applies (default 700)
--   PS_PEEK     "addr,addr,..." hex; PS_PEEKOUT file gets "frame v v v" on every change
--   PS_WTAP     "lo-hi" hex: log every CPU write in the range: PS_WTAPOUT "frame pc addr val" (bank from $B7)
--   PS_RTAP     "lo-hi" hex: log CPU data reads in range (PC != addr): PS_RTAPOUT, aggregated "bank:pc addr count"
--   PS_RTAPFROM frame from which reads are counted
--   PS_SCRIPT   "frame:keys;frame:keys" explicit inputs: keys from U D L R F G (G = button 2), '-' none;
--               each entry holds until the next. Disables the random player.
local M = manager.machine
local cpu = M.devices[":maincpu"]
local mem = cpu.spaces["program"]
local function env(n, d) local v = os.getenv(n) if v == nil or v == "" then return d end return v end
local FRAMES = tonumber(env("PS_FRAMES", "3600"))
local SEED = tonumber(env("PS_SEED", "1"))
local PLAY = env("PS_PLAY", "1") ~= "0"
local RAMEVERY = tonumber(env("PS_RAMEVERY", "60"))
local SNAP = tonumber(env("PS_SNAP", "0"))
local LOCKFROM = tonumber(env("PS_LOCKFROM", "700"))

local starts = {}
for f in string.gmatch(env("PS_START", "125,345"), "%d+") do starts[#starts + 1] = tonumber(f) end

local pokes = {}
for fr, list in string.gmatch(env("PS_POKES", ""), "(%d+):([^;]+)") do
  local t = pokes[tonumber(fr)] or {}
  for ad, val in string.gmatch(list, "(%x+)=(%x+)") do t[#t + 1] = {tonumber(ad, 16), tonumber(val, 16)} end
  pokes[tonumber(fr)] = t
end
local locks = {}
for ad, val in string.gmatch(env("PS_LOCK", ""), "(%x+)=(%x+)") do locks[#locks + 1] = {tonumber(ad, 16), tonumber(val, 16)} end
local peeks = {}
for a in string.gmatch(env("PS_PEEK", ""), "%x+") do peeks[#peeks + 1] = tonumber(a, 16) end
local peekout = (#peeks > 0) and io.open(env("PS_PEEKOUT", "peek.txt"), "w") or nil
local lastpeek = ""

local script = nil
if env("PS_SCRIPT", "") ~= "" then
  script = {}
  for fr, keys in string.gmatch(env("PS_SCRIPT", ""), "(%d+):([UDLRFG%-]+)") do script[#script + 1] = {tonumber(fr), keys} end
  table.sort(script, function(a, b) return a[1] < b[1] end)
end

local ports = M.ioport.ports
-- port tags are upper-case on the fork (0.289), lower on 0.287
local function fld(n)
  for _, t in ipairs({":JOYSTICKS", ":BUTTONS", ":joysticks", ":buttons"}) do
    local f = ports[t] and ports[t].fields[n]
    if f then return f end
  end
end
local jU, jD, jL, jR, b1, b2 = fld("P1 Up"), fld("P1 Down"), fld("P1 Left"), fld("P1 Right"), fld("P1 Button 1"), fld("P1 Button 2")
local function set(up, dn, lf, rt, f1, f2)
  jU:set_value(up) jD:set_value(dn) jL:set_value(lf) jR:set_value(rt)
  b1:set_value(f1) b2:set_value(f2)
end

-- execution coverage (as probes/exectrace.lua)
local XT = env("PS_XT", "")
local bank = 0
local seen_x, seen_j, seen_s = {}, {}, {}
local pending_j = nil
local function key(addr)
  if addr >= 0x8000 and addr <= 0xBFFF then return string.format("b%d:%04X", bank, addr) end
  if addr < 0x8000 then return string.format("f6:%04X", addr) end
  return string.format("f7:%04X", addr)
end
TAPS = {}
TAPS[1] = mem:install_write_tap(0x8000, 0xBFFF, "banksel", function(offset, data)
  local v = data % 8
  if XT ~= "" then
    local k = string.format("%s %d", key(cpu.state["PC"].value), v)
    seen_s[k] = (seen_s[k] or 0) + 1
  end
  bank = v
  return data
end)
if XT ~= "" then
  TAPS[2] = mem:install_read_tap(0x4000, 0xFFFF, "exectrace", function(offset, data)
    local pc = cpu.state["PC"].value
    if pc ~= offset then return data end
    local k = key(pc)
    if pending_j then seen_j[pending_j .. " " .. k] = true pending_j = nil end
    seen_x[k] = true
    if data == 0x6C then pending_j = k end
    return data
  end)
end

local fno = 0
-- write tap
local wlo, whi = string.match(env("PS_WTAP", ""), "^(%x+)%-(%x+)$")
local wout = nil
if wlo then
  wout = io.open(env("PS_WTAPOUT", "wtap.txt"), "w")
  local WFROM = tonumber(env("PS_WTAPFROM", "0"))
  TAPS[3] = mem:install_write_tap(tonumber(wlo, 16), tonumber(whi, 16), "wtap", function(offset, data)
    if fno >= WFROM then
      wout:write(string.format("%d %d:%04X %04X %02X\n", fno, bank, cpu.state["PC"].value, offset, data))
    end
    return data
  end)
end
-- read tap (aggregated)
local rlo, rhi = string.match(env("PS_RTAP", ""), "^(%x+)%-(%x+)$")
local rseen = {}
local RFROM = tonumber(env("PS_RTAPFROM", "0"))
if rlo then
  TAPS[4] = mem:install_read_tap(tonumber(rlo, 16), tonumber(rhi, 16), "rtap", function(offset, data)
    local pc = cpu.state["PC"].value
    if fno >= RFROM and (pc > offset or pc + 2 < offset) then
      local k = string.format("%d:%04X %s", bank, pc, key(offset))
      rseen[k] = (rseen[k] or 0) + 1
    end
    return data
  end)
end

-- frame probe: PS_FPROBE file gets, per frame: frame, main-loop passes (fetches of $F83C, the frame
-- wait) since the last frame, the raster line the NMI was entered on ($FD99) and the line its RTI
-- ($FEEC) was fetched on (+263 when it ran past the frame's end), CPU cycles between the two is not
-- measured (lines only), and the number of live object slots.
local fpout = (env("PS_FPROBE", "") ~= "") and io.open(env("PS_FPROBE", ""), "w") or nil
local passes, nmi_in, nmi_out, nmi_inframe = 0, -1, -1, -1
local scr
for _, s in pairs(M.screens) do scr = s break end
local function rline()
  local lines = scr.frame_period / scr.scan_period
  local left = scr:time_until_pos(0, 0) / scr.scan_period
  return (lines - left) % lines
end
if fpout then
  TAPS[5] = mem:install_read_tap(0xF83C, 0xF83C, "fp1", function(offset, data)
    if cpu.state["PC"].value == 0xF83C then passes = passes + 1 end
    return data
  end)
  TAPS[6] = mem:install_read_tap(0xFD99, 0xFD99, "fp2", function(offset, data)
    if cpu.state["PC"].value == 0xFD99 then nmi_in = rline() nmi_inframe = fno end
    return data
  end)
  TAPS[7] = mem:install_read_tap(0xFEEC, 0xFEEC, "fp3", function(offset, data)
    if cpu.state["PC"].value == 0xFEEC then
      nmi_out = rline()
      if nmi_out < nmi_in then nmi_out = nmi_out + 263 end
      local live = 0
      for s = 0, 31 do if mem:read_u8(0x1800 + s) < 0x80 then live = live + 1 end end
      fpout:write(string.format("%d %d %.1f %.1f %d\n", fno, passes, nmi_in, nmi_out, live))
      passes = 0
    end
    return data
  end)
end

local ramout = (env("PS_RAM", "") ~= "") and io.open(env("PS_RAM", ""), "wb") or nil
local function ramsnap()
  local t = {}
  t[#t + 1] = string.pack("<I4", fno)
  local function blk(lo, hi)
    local b = {}
    for a = lo, hi do b[#b + 1] = string.char(mem:read_u8(a)) end
    t[#t + 1] = table.concat(b)
  end
  blk(0x40, 0xFF) blk(0x1800, 0x1FFF) blk(0x2200, 0x27FF)
  ramout:write(table.concat(t))
end

-- pseudo-random player
local rs = SEED * 2654435761 % 4294967296
local function rnd(n)
  rs = (rs * 1103515245 + 12345) % 4294967296
  return math.floor(rs / 65536) % n
end
local dir, dirleft, fire, fireleft, f2 = 0, 0, 0, 0, 0
local DIRS = { {0,0,0,0}, {0,0,1,0}, {0,0,0,1}, {1,0,0,0}, {0,1,0,0}, {1,0,1,0}, {1,0,0,1}, {0,1,1,0}, {0,1,0,1}, {0,0,1,0}, {0,0,0,1} }

local sidx = 1
local function inputs()
  for _, s in ipairs(starts) do
    if fno >= s and fno < s + 10 then set(0, 0, 0, 0, 1, 0) return end
  end
  if script then
    while sidx < #script and script[sidx + 1][1] <= fno do sidx = sidx + 1 end
    local k = (script[sidx][1] <= fno) and script[sidx][2] or "-"
    local function h(c) return string.find(k, c, 1, true) and 1 or 0 end
    set(h("U"), h("D"), h("L"), h("R"), h("F"), h("G"))
    return
  end
  if not PLAY then set(0, 0, 0, 0, 0, 0) return end
  if dirleft <= 0 then dir = rnd(#DIRS) + 1 dirleft = 6 + rnd(30) end
  if fireleft <= 0 then fire = (rnd(4) ~= 0) and 1 or 0 fireleft = (fire == 1) and (2 + rnd(6)) or (2 + rnd(5)) f2 = (rnd(40) == 0) and 1 or 0 end
  dirleft = dirleft - 1 fireleft = fireleft - 1
  local d = DIRS[dir]
  set(d[1], d[2], d[3], d[4], fire, f2)
end

local function finish()
  if XT ~= "" then
    local lines = {}
    for k in pairs(seen_x) do lines[#lines + 1] = "X " .. k end
    for k in pairs(seen_j) do lines[#lines + 1] = "J " .. k end
    for k, n in pairs(seen_s) do lines[#lines + 1] = string.format("S %s x%d", k, n) end
    table.sort(lines)
    local f = io.open(XT, "w")
    for _, l in ipairs(lines) do f:write(l, "\n") end
    f:close()
  end
  if rlo then
    local f = io.open(env("PS_RTAPOUT", "rtap.txt"), "w")
    local lines = {}
    for k, n in pairs(rseen) do lines[#lines + 1] = string.format("%s %d", k, n) end
    table.sort(lines)
    for _, l in ipairs(lines) do f:write(l, "\n") end
    f:close()
  end
  if ramout then ramout:close() end
  if peekout then peekout:close() end
  if wout then wout:close() end
end
local done = false
FRAME_CB = emu.add_machine_frame_notifier(function()
  if done then return end
  fno = fno + 1
  inputs()
  local p = pokes[fno]
  if p then for _, e in ipairs(p) do mem:write_u8(e[1], e[2]) end end
  if fno >= LOCKFROM then for _, e in ipairs(locks) do mem:write_u8(e[1], e[2]) end end
  if ramout and fno % RAMEVERY == 0 then ramsnap() end
  if SNAP > 0 and fno % SNAP == 0 then M.video:snapshot() end
  if peekout then
    local t = {}
    for _, a in ipairs(peeks) do t[#t + 1] = string.format("%02X", mem:read_u8(a)) end
    local s = table.concat(t, " ")
    if s ~= lastpeek then peekout:write(fno, " ", s, "\n") lastpeek = s end
  end
  if fno >= FRAMES then
    done = true
    finish()
    M:exit()
  end
end)

-- PS_ALSO: another probe to load beside this one (e.g. the toolkit's probes/cyclebudget.lua,
-- configured through its own A7800_* variables)
if env("PS_ALSO", "") ~= "" then dofile(env("PS_ALSO", "")) end
