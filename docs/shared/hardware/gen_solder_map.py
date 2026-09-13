#!/usr/bin/env python3
"""Perma-Proto HALF-size (#1609) solder map for the Teensy 4.0 + dual LS7366R carrier.

Real board topology (landscape, as silkscreened):
  - 30 numbered columns run left->right.
  - Each column has a 5-hole node in the top band (F-J) and another in the bottom
    band (A-E), split by the center trench. Those vertical 5-hole groups are the
    pre-soldered ties. Two nets in the same column+band are SHORTED.
  - 4 power buses on the long edges, marked +/- (they alternate: top = - then +,
    bottom = + then -). Assigned here: top+ =5V, top- =GND, bottom+ =3.3V, bottom- =GND.
Every part is placed in its own columns so nothing shares a node.
"""
from pathlib import Path

PITCH=30; X0,Y0=70,70; TRENCH=22
NCOL=30
# vertical lines: (label, kind)  top->bottom
VROWS=[("-","g"),("+","p"),("F","b"),("G","b"),("H","b"),("I","b"),("J","b"),
       ("A","b"),("B","b"),("C","b"),("D","b"),("E","b"),("+","p"),("-","g")]
VI={"tN":0,"tP":1,"F":2,"G":3,"H":4,"I":5,"J":6,"A":7,"B":8,"C":9,"D":10,"E":11,"bP":12,"bN":13}
def cx(col): return X0+(col-1)*PITCH
def vy(v):
    y=Y0+v*PITCH
    return y+TRENCH if v>=7 else y
W=cx(NCOL)+40; H=vy(13)+90

# Teensy pins along cols 2..15; bottom row in band B, top row in band I
tb=["GND","0","1","2","3","4","5","6","7","8","9","10","11","12"]  # bottom side (A-E band)
tt=["VIN","AGND","3V3","23","22","21","20","19","18","17","16","15","14","13"]  # top side (F-J band)
def bcol(n): return 2+tb.index(n)
def tcol(n): return 2+tt.index(n)
TBROW=VI["B"]; TTROW=VI["I"]
# encoder header cols 18..24 in band C ; OLED cols 25..28 in band H ; reset col 17
enc=["VCC","GND","SCK","MOSI","MISO","SS1","SS2"]; ENC0=18; ENCV=VI["C"]
oled=["VCC","GND","SDA","SCL"]; OLED0=25; OLEDV=VI["H"]
RSTC=17
def encc(n): return ENC0+enc.index(n)
def oledc(n): return OLED0+oled.index(n)

C={"p5":"#d97b16","g":"#7b8494","v3":"#7a4bd6","spi":"#0f8f96","ser":"#2f8f5b","i2c":"#bf3d9e","rst":"#c93a3a"}
J=[]
# power
J.append((tcol("VIN"),TTROW, tcol("VIN"),VI["tP"],"p5"))     # VIN -> top+ (5V)
J.append((tcol("3V3"),TTROW, tcol("3V3"),VI["bP"],"v3"))     # 3V3 out -> bottom+ (3V3), crosses
J.append((bcol("GND"),TBROW, bcol("GND"),VI["bN"],"g"))      # Teensy GND -> bottom- (GND)
J.append((NCOL,VI["tN"], NCOL,VI["bN"],"g"))                 # tie top- and bottom- grounds (col 30)
# SPI teensy -> encoder
J.append((tcol("13"),TTROW, encc("SCK"),ENCV,"spi"))
J.append((bcol("11"),TBROW, encc("MOSI"),ENCV,"spi"))
J.append((bcol("12"),TBROW, encc("MISO"),ENCV,"spi"))
J.append((bcol("6"),TBROW,  encc("SS1"),ENCV,"spi"))
J.append((bcol("5"),TBROW,  encc("SS2"),ENCV,"spi"))
J.append((encc("VCC"),ENCV, encc("VCC"),VI["bP"],"v3"))      # enc VCC -> bottom+ (3V3)
J.append((encc("GND"),ENCV, encc("GND"),VI["bN"],"g"))       # enc GND -> bottom- (GND)
# OLED
J.append((tcol("18"),TTROW, oledc("SDA"),OLEDV,"i2c"))
J.append((tcol("19"),TTROW, oledc("SCL"),OLEDV,"i2c"))
J.append((oledc("VCC"),OLEDV, oledc("VCC"),VI["bP"],"v3"))   # OLED VCC -> bottom+ (3V3)
J.append((oledc("GND"),OLEDV, oledc("GND"),VI["tN"],"g"))    # OLED GND -> top- (GND)
# reset switch across trench at col 17: E (On/Off) & F (GND)
J.append((RSTC,VI["F"], RSTC,VI["tN"],"g"))                  # reset GND leg -> top- rail

def hole(c,v,r=4.5,ex=""): return f'<circle cx="{cx(c)}" cy="{vy(v)}" r="{r}" {ex}/>'
svg=[f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Adafruit Perma-Proto half-size solder map in landscape. 30 numbered columns; each column has a top band F to J and a bottom band A to E, pre-soldered as vertical 5-hole nodes and split by the center trench. Four power rails run along the top and bottom edges marked plus and minus. The Teensy occupies columns 2 to 15 straddling the trench; the encoder header, OLED header and reset switch sit in their own columns so no two nets share a node. Colored lines are jumper wires.">']
# rail bars (horizontal)
def railbar(v,color):
    svg.append(f'<rect x="{cx(1)-12}" y="{vy(v)-8}" width="{cx(NCOL)-cx(1)+24}" height="16" rx="8" fill="{color}" opacity="0.15"/>')
railbar(VI["tN"],"#7b8494"); railbar(VI["tP"],"#d97b16")
railbar(VI["bP"],"#7a4bd6"); railbar(VI["bN"],"#7b8494")
# pre-soldered vertical 5-hole ties per column (top band F-J, bottom band A-E)
for c in range(1,NCOL+1):
    for a,b in ((VI["F"],VI["J"]),(VI["A"],VI["E"])):
        svg.append(f'<rect x="{cx(c)-6}" y="{vy(a)-10}" width="12" height="{vy(b)-vy(a)+20}" rx="6" fill="#8f99a8" opacity="0.16"/>')
# column numbers (top and bottom)
for c in range(1,NCOL+1):
    for yy in (vy(VI["tN"])-24, vy(VI["bN"])+30):
        svg.append(f'<text x="{cx(c)}" y="{yy}" text-anchor="middle" style="font:500 9px ui-monospace,monospace" fill="#9aa4b2">{c}</text>')
# row letters / rail marks on the left
for v,(lab,kind) in enumerate(VROWS):
    col = {"g":"#7b8494","p":("#d97b16" if v==VI["tP"] else "#7a4bd6")}.get(kind,"#9aa4b2") if kind!="b" else "#9aa4b2"
    txt = lab if kind=="b" else ("+" if kind=="p" else "−")
    svg.append(f'<text x="{X0-30}" y="{vy(v)+4}" text-anchor="middle" style="font:600 11px ui-monospace,monospace" fill="{col}">{txt}</text>')
# rail net labels on the right
def raillbl(v,txt,color):
    svg.append(f'<text x="{cx(NCOL)+14}" y="{vy(v)+4}" style="font:600 10px ui-monospace,monospace" fill="{color}">{txt}</text>')
raillbl(VI["tN"],"GND","#7b8494"); raillbl(VI["tP"],"5V","#d97b16")
raillbl(VI["bP"],"3V3","#7a4bd6"); raillbl(VI["bN"],"GND","#7b8494")
# holes
for c in range(1,NCOL+1):
    for v in range(len(VROWS)):
        svg.append(hole(c,v,4.5,'fill="#c9ced6"'))
# component outlines + labels
def outline(c0,v0,c1,v1,label,above=True):
    x=cx(c0)-12;y=vy(v0)-12;w=cx(c1)-cx(c0)+24;h=vy(v1)-vy(v0)+24
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-dasharray="4 4"/>')
    ly = y-6 if above else y+h+14
    svg.append(f'<text x="{x}" y="{ly}" style="font:600 12px system-ui" fill="currentColor" opacity="0.8">{label}</text>')
outline(2,TTROW,15,TBROW,"TEENSY 4.0  (USB ◄ col 2 end, straddles trench)")
outline(ENC0,ENCV,ENC0+6,ENCV,"LS7366R header (row C)",above=False)
outline(OLED0,OLEDV,OLED0+3,OLEDV,"OLED header (row H)")
outline(RSTC,VI["F"],RSTC,VI["E"],"RESET")
# pin labels
def plabel(c,v,t,dyc=1):
    dy = -10 if dyc<0 else 14
    svg.append(f'<text x="{cx(c)}" y="{vy(v)+dy}" text-anchor="middle" style="font:500 8.5px ui-monospace,monospace" fill="currentColor">{t}</text>')
for n in tb: plabel(bcol(n),TBROW,n,1)
for n in tt: plabel(tcol(n),TTROW,n,-1)
for n in enc: plabel(encc(n),ENCV,n,1)
for n in oled: plabel(oledc(n),OLEDV,n,-1)
plabel(RSTC,VI["E"],"On/Off",1); plabel(RSTC,VI["F"],"GND",-1)
# occupied teensy holes
for n in tt:
    if n in ("VIN","3V3","18","19","13"): svg.append(hole(tcol(n),TTROW,5.5,'fill="currentColor"'))
for n in tb:
    if n in ("GND","5","6","8","11","12"): svg.append(hole(bcol(n),TBROW,5.5,'fill="currentColor"'))
# jumpers
for (cf,vf,ct,vt,net) in J:
    col=C[net]
    svg.append(f'<path d="M{cx(cf)} {vy(vf)} L{cx(ct)} {vy(vt)}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round" opacity="0.92"/>')
    svg.append(hole(cf,vf,5.5,f'fill="{col}"')); svg.append(hole(ct,vt,5.5,f'fill="{col}"'))
# serial tag near pin 8
svg.append(f'<text x="{cx(bcol("8"))}" y="{vy(TBROW)+24}" text-anchor="middle" style="font:500 8px ui-monospace,monospace" fill="#2f8f5b">→SabS1</text>')
svg.append('</svg>')

rows=[("5V","5V rail (top +)","Teensy VIN (col 2, F-J)","from 5V bus"),
 ("3.3V","Teensy 3V3 (col 4, F-J)","3V3 rail (bottom +)","powers encoder+OLED; crosses board"),
 ("GND","Teensy GND (col 2, A-E)","GND rail (bottom -)",""),
 ("GND","top - rail","bottom - rail (col 30)","tie the two GND buses once"),
 ("SPI","Teensy 13 (col 15, F-J)","enc SCK (col 20, A-E)","crosses trench"),
 ("SPI","Teensy 11 (col 14, A-E)","enc MOSI (col 21, A-E)",""),
 ("SPI","Teensy 12 (col 15, A-E)","enc MISO (col 22, A-E)","the joint that read 0x00"),
 ("SPI","Teensy 6 (col 9, A-E)","enc SS1 (col 23, A-E)","left"),
 ("SPI","Teensy 5 (col 8, A-E)","enc SS2 (col 24, A-E)","right"),
 ("3.3V","3V3 rail","enc VCC (col 18)",""),
 ("GND","GND rail","enc GND (col 19)",""),
 ("I2C","Teensy 18 (col 10, F-J)","OLED SDA (col 27, F-J)","optional"),
 ("I2C","Teensy 19 (col 9, F-J)","OLED SCL (col 28, F-J)","optional"),
 ("3.3V/GND","rails","OLED VCC/GND (col 25/26)","optional"),
 ("Reset","On/Off pad","reset leg (col 17, row E)","flying lead from Teensy pad"),
 ("Reset","reset leg (col 17, row F)","GND rail","other leg; press bridges the trench"),
 ("Reset","Jetson GPIO -> NPN","On/Off","remote; button in parallel"),
 ("Serial","Teensy 8 (col 11, A-E)","-> Sabertooth S1","off-board; + Teensy GND -> Sab 0V"),
 ("Enc in","LEFT wheel A/B/I/V+/GND","LS7366R CH1","off-board"),
 ("Enc in","RIGHT wheel A/B/I/V+/GND","LS7366R CH2","off-board")]
trows="".join(f"<tr><td>{a}</td><td><code>{b}</code></td><td><code>{c}</code></td><td>{d}</td></tr>" for a,b,c,d in rows)

html=f'''<title>Perma-Proto Half Solder Map</title>
<style>
:root{{--bg:#f4f5f7;--card:#fff;--ink:#1d2330;--muted:#5c6675;--border:#d5dae2;--sans:system-ui,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#14171d;--card:#1e232b;--ink:#e8ebf0;--muted:#9aa4b2;--border:#343c48}}}}
:root[data-theme=dark]{{--bg:#14171d;--card:#1e232b;--ink:#e8ebf0;--muted:#9aa4b2;--border:#343c48}}
body{{background:var(--bg);color:var(--ink);font-family:var(--sans);margin:0}}
.wrap{{max-width:1400px;margin:0 auto;padding:26px 22px 46px}}
.eyebrow{{font:600 11px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}}
h1{{font:600 24px var(--sans);margin:2px 0 0}}h2{{font:600 17px var(--sans);margin:26px 0 8px}}
.sub{{font:400 13px var(--mono);color:var(--muted);margin-top:4px}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 16px;padding:11px 15px;margin:14px 0;background:var(--card);border:1px solid var(--border);border-radius:10px}}
.key{{display:inline-flex;align-items:center;gap:7px;font:500 11px var(--mono)}}
.sw{{width:22px;height:0;border-top:3px solid;border-radius:2px}}.sw.bar{{height:11px;width:14px;border:0;border-radius:5px;background:#8f99a8;opacity:.5}}
.board{{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow-x:auto;padding:10px;color:var(--ink)}}
.board svg{{display:block;width:100%;min-width:1000px;height:auto}}
table{{border-collapse:collapse;width:100%;font:13px/1.5 var(--sans);margin-top:6px}}
th,td{{border:1px solid var(--border);padding:6px 10px;text-align:left}}th{{background:var(--card);font-weight:600}}td code{{font:500 12px var(--mono)}}
.notes{{padding-left:1.2em;color:var(--muted);font:400 13px/1.7 var(--sans)}}.notes code{{font:500 12px var(--mono);color:var(--ink)}}
.warn{{color:#c93a3a;font-weight:600}}
</style>
<div class="wrap">
<div class="eyebrow">Robomo · solder map</div>
<h1>Perma-Proto HALF Solder Map — Teensy 4.0 + LS7366R</h1>
<div class="sub">Adafruit #1609, 30 columns. Coords are <code>col · band</code>. Grey bars = pre-soldered 5-hole nodes (vertical). Rails run the long edges.</div>
<div class="legend">
<span class="key"><span class="sw bar"></span>pre-soldered node</span>
<span class="key"><span class="sw" style="border-color:#d97b16"></span>5 V</span>
<span class="key"><span class="sw" style="border-color:#7a4bd6"></span>3.3 V</span>
<span class="key"><span class="sw" style="border-color:#7b8494"></span>GND</span>
<span class="key"><span class="sw" style="border-color:#0f8f96"></span>SPI</span>
<span class="key"><span class="sw" style="border-color:#bf3d9e"></span>I²C</span>
<span class="key"><span class="sw" style="border-color:#c93a3a"></span>Reset</span>
</div>
<div class="board">{''.join(svg)}</div>
<h2>Jumper / connection list</h2>
<table><tr><th>Net</th><th>From</th><th>To</th><th>Note</th></tr>{trows}</table>
<h2>How to read it</h2>
<ul class="notes">
<li class="warn">Grey bars = the 5 holes in one column+band, already connected on the board. Never land two nets on the same bar — that's a short. Every part here sits in its own columns for that reason.</li>
<li>The board is landscape: 30 columns, top band <b>F–J</b> and bottom band <b>A–E</b> split by the trench. Rails run the top and bottom edges; their <b>+ / −</b> markings alternate. Here: top <b>+</b> = 5 V, top <b>−</b> = GND, bottom <b>+</b> = 3.3 V, bottom <b>−</b> = GND. Match by the printed <b>+/−</b>, and tie the two GND rails together once (col 30).</li>
<li>Mount the Teensy on female headers across <b>columns 2–15</b>, straddling the trench — bottom pins in the A–E band, top pins in the F–J band. Each pin owns its column's 5-hole bar; jumper from any free hole in that bar.</li>
<li class="warn">3.3 V on the SPI/encoder/OLED side; only the 5 V rail and pin 8 → Sabertooth are 5 V.</li>
<li><b>On/Off</b> is a pad on the Teensy underside — flying-lead it to the reset switch (col 17, row E). The switch straddles the trench; its other leg (row F) → GND. A Jetson GPIO drives the same pad through an NPN for remote reset.</li>
<li>Dark holes = occupied Teensy pins; colored holes = jumper endpoints. Slide the cluster along the columns to taste — only relative placement matters.</li>
</ul>
</div>'''
Path(__file__).resolve().with_name("perma-proto-solder-map.html").write_text(html)
print("wrote", len(html), "bytes")
