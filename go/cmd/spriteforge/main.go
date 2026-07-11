// Command spriteforge is a native (Ebitengine) spritesheet maker for the Snake
// Roguelite project. It loads sprite PNGs from an assets folder, lets you
// compose animation frames from them (mirror / rotate / squash / offset), tile
// them into a grid, preview the animation, and export the sheet straight back
// into the assets folder that the game reads.
//
// Run from the go/ directory:
//
//	go run ./cmd/spriteforge            # loads ./assets
//	go run ./cmd/spriteforge -dir assets -out assets/enemy_spritesheet.png
package main

import (
	"flag"
	"fmt"
	"image"
	"image/color"
	_ "image/jpeg"
	"image/png"
	"log"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"github.com/hajimehoshi/ebiten/v2/vector"
)

const (
	winW = 1180
	winH = 760
)

// ---- Palette (dark editor theme) ----
var (
	cBG      = color.RGBA{0x14, 0x18, 0x14, 0xff}
	cPanel   = color.RGBA{0x1b, 0x21, 0x1a, 0xff}
	cPanel2  = color.RGBA{0x27, 0x2e, 0x24, 0xff}
	cHover   = color.RGBA{0x32, 0x3b, 0x2e, 0xff}
	cLine    = color.RGBA{0x3a, 0x42, 0x35, 0xff}
	cAccent  = color.RGBA{0x6c, 0xc5, 0x5f, 0xff}
	cAccentD = color.RGBA{0x2f, 0x4a, 0x2b, 0xff}
	cAmber   = color.RGBA{0xd9, 0xa4, 0x41, 0xff}
	cDanger  = color.RGBA{0xe0, 0x68, 0x5c, 0xff}
	cDangerD = color.RGBA{0x53, 0x2b, 0x28, 0xff}
	cCheckA  = color.RGBA{0x1b, 0x20, 0x1a, 0xff}
	cCheckB  = color.RGBA{0x23, 0x2a, 0x20, 0xff}
)

// ---- Model ----

// Source is a loaded sprite image plus its opaque bounding box (for trimming).
type Source struct {
	name string
	img  *ebiten.Image
	bbox image.Rectangle
	w, h int
}

// Frame references a source and the transform used to place it in a cell.
type Frame struct {
	src            int
	flipH, flipV   bool
	rot            int // degrees
	sx, sy         float64
	ox, oy         float64 // offset in cell pixels
}

func defaultFrame(src int) Frame { return Frame{src: src, sx: 1, sy: 1} }

// ---- App ----

type App struct {
	sources []*Source
	frames  []Frame
	cur     int

	cw, ch, cols int
	trim, smooth bool
	fps          int

	playing   bool
	tick       int
	animFrame  int
	animAccum  int
	cell       *ebiten.Image // reusable cw x ch scratch
	status     string
	outPath    string

	// per-frame input
	mx, my  float64
	clicked bool
}

func newApp(sources []*Source, out string) *App {
	a := &App{
		sources: sources,
		cw:      64, ch: 64, cols: 8,
		trim: true, smooth: false, fps: 6,
		playing: true, outPath: out,
	}
	// Preload a facing pair from enemy_lizard.png if present, else the first source.
	base := 0
	for i, s := range sources {
		if strings.Contains(strings.ToLower(s.name), "lizard") {
			base = i
			break
		}
	}
	if len(sources) > 0 {
		a.frames = append(a.frames, defaultFrame(base))
		mirror := defaultFrame(base)
		mirror.flipH = true
		a.frames = append(a.frames, mirror)
		a.cols = 8
		a.status = "Loaded " + fmt.Sprint(len(sources)) + " sprite(s). Facing pair ready."
	} else {
		a.status = "No PNGs found in assets folder. Drop sprites there and restart."
	}
	a.cell = ebiten.NewImage(a.cw, a.ch)
	return a
}

func (a *App) curFrame() *Frame {
	if a.cur < 0 || a.cur >= len(a.frames) {
		return nil
	}
	return &a.frames[a.cur]
}

func (a *App) region(f *Frame) image.Rectangle {
	s := a.sources[f.src]
	if a.trim {
		return s.bbox
	}
	return image.Rect(0, 0, s.w, s.h)
}

// drawFrame renders one frame filling a cw x ch cell, drawn onto dst with its
// top-left at (ox, oy).
func (a *App) drawFrame(dst *ebiten.Image, f *Frame, ox, oy, cw, ch float64) {
	s := a.sources[f.src]
	r := a.region(f)
	sub := s.img.SubImage(r).(*ebiten.Image)
	rw, rh := float64(r.Dx()), float64(r.Dy())
	const fill = 0.9
	base := math.Min(cw*fill/rw, ch*fill/rh)

	fh, fv := 1.0, 1.0
	if f.flipH {
		fh = -1
	}
	if f.flipV {
		fv = -1
	}

	op := &ebiten.DrawImageOptions{}
	if a.smooth {
		op.Filter = ebiten.FilterLinear
	} else {
		op.Filter = ebiten.FilterNearest
	}
	op.GeoM.Translate(-rw/2, -rh/2)
	op.GeoM.Scale(base*f.sx*fh, base*f.sy*fv)
	op.GeoM.Rotate(float64(f.rot) * math.Pi / 180)
	op.GeoM.Translate(ox+cw/2+f.ox, oy+ch/2+f.oy)
	dst.DrawImage(sub, op)
}

// renderCell draws a single frame (transparent background) into a.cell.
func (a *App) renderCell(f *Frame) {
	if a.cell.Bounds().Dx() != a.cw || a.cell.Bounds().Dy() != a.ch {
		a.cell = ebiten.NewImage(a.cw, a.ch)
	}
	a.cell.Clear()
	if f != nil && f.src < len(a.sources) {
		a.drawFrame(a.cell, f, 0, 0, float64(a.cw), float64(a.ch))
	}
}

// buildSheet renders every frame onto a fresh transparent image (for export /
// sheet preview).
func (a *App) buildSheet() (*ebiten.Image, int, int) {
	n := len(a.frames)
	cols := clampi(a.cols, 1, 20)
	rows := maxi(1, (n+cols-1)/cols)
	sheet := ebiten.NewImage(cols*a.cw, rows*a.ch)
	for i := range a.frames {
		ox := float64((i % cols) * a.cw)
		oy := float64((i / cols) * a.ch)
		a.drawFrame(sheet, &a.frames[i], ox, oy, float64(a.cw), float64(a.ch))
	}
	return sheet, cols, rows
}

func (a *App) exportPNG() {
	sheet, cols, rows := a.buildSheet()
	w, h := sheet.Bounds().Dx(), sheet.Bounds().Dy()
	buf := make([]byte, 4*w*h)
	sheet.ReadPixels(buf)
	rgba := &image.RGBA{Pix: buf, Stride: 4 * w, Rect: image.Rect(0, 0, w, h)}

	if err := os.MkdirAll(filepath.Dir(a.outPath), 0o755); err != nil {
		a.status = "Export failed: " + err.Error()
		return
	}
	fp, err := os.Create(a.outPath)
	if err != nil {
		a.status = "Export failed: " + err.Error()
		return
	}
	defer fp.Close()
	if err := png.Encode(fp, rgba); err != nil {
		a.status = "Export failed: " + err.Error()
		return
	}
	abs, _ := filepath.Abs(a.outPath)
	a.status = fmt.Sprintf("Saved %dx%d (%dx%d grid) -> %s", w, h, cols, rows, abs)
}

// ---- Update ----

func (a *App) Update() error {
	a.tick++
	a.mx, a.my = func() (float64, float64) { x, y := ebiten.CursorPosition(); return float64(x), float64(y) }()
	a.clicked = inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft)

	// Animation advance.
	if a.playing && len(a.frames) > 0 {
		a.animAccum++
		step := 60 / maxi(a.fps, 1)
		if a.animAccum >= step {
			a.animAccum = 0
			a.animFrame = (a.animFrame + 1) % len(a.frames)
		}
	}

	// Keyboard nudges for the selected frame's offset (fine control).
	if f := a.curFrame(); f != nil {
		if inpututil.IsKeyJustPressed(ebiten.KeyLeft) {
			f.ox--
		}
		if inpututil.IsKeyJustPressed(ebiten.KeyRight) {
			f.ox++
		}
		if inpututil.IsKeyJustPressed(ebiten.KeyUp) {
			f.oy--
		}
		if inpututil.IsKeyJustPressed(ebiten.KeyDown) {
			f.oy++
		}
	}
	if inpututil.IsKeyJustPressed(ebiten.KeySpace) {
		a.playing = !a.playing
	}
	if inpututil.IsKeyJustPressed(ebiten.KeyM) {
		a.mirrorCopy()
	}
	if inpututil.IsKeyJustPressed(ebiten.KeyEscape) {
		return ebiten.Termination
	}
	return nil
}

func (a *App) mirrorCopy() {
	f := a.curFrame()
	if f == nil {
		return
	}
	c := *f
	c.flipH = !c.flipH
	a.insertFrame(a.cur+1, c)
	a.cur++
}

func (a *App) insertFrame(i int, f Frame) {
	if i > len(a.frames) {
		i = len(a.frames)
	}
	a.frames = append(a.frames, Frame{})
	copy(a.frames[i+1:], a.frames[i:])
	a.frames[i] = f
}

// ---- Draw ----

func (a *App) Draw(screen *ebiten.Image) {
	screen.Fill(cBG)

	// Header
	vector.DrawFilledRect(screen, 0, 0, winW, 40, cPanel, false)
	ebitenutil.DebugPrintAt(screen, "SNAKE FORGE  ::  spritesheet maker", 16, 12)
	ebitenutil.DebugPrintAt(screen, "arrows: nudge offset   space: play/pause   m: mirror copy   esc: quit", 470, 12)

	// ---- Left: editor ----
	ex, ey, es := float64(24), float64(56), float64(360)
	label(screen, "FRAME EDITOR", ex, ey-14)
	a.drawChecker(screen, ex, ey, es, es)
	if f := a.curFrame(); f != nil {
		a.renderCell(f)
		op := &ebiten.DrawImageOptions{}
		op.Filter = ebiten.FilterNearest
		op.GeoM.Scale(es/float64(a.cw), es/float64(a.ch))
		op.GeoM.Translate(ex, ey)
		screen.DrawImage(a.cell, op)
	}
	strokeRect(screen, ex, ey, es, es, cLine)
	// frame nav
	ny := ey + es + 8
	if a.button(screen, ex, ny, 40, 24, "< prev", 0) {
		a.selectDelta(-1)
	}
	if a.button(screen, ex+es-40, ny, 40, 24, "next >", 0) {
		a.selectDelta(1)
	}
	label(screen, fmt.Sprintf("frame %d / %d", a.cur+1, len(a.frames)), ex+150, ny+6)

	// ---- Left lower: filmstrip ----
	a.drawFilmstrip(screen, 24, ny+44, 360+356+20)

	// ---- Middle: controls ----
	a.drawControls(screen, 430, 56)

	// ---- Right: preview + sheet ----
	a.drawPreviewColumn(screen, 820, 56)

	// status bar
	vector.DrawFilledRect(screen, 0, winH-26, winW, 26, cPanel, false)
	ebitenutil.DebugPrintAt(screen, a.status, 16, winH-20)
}

func (a *App) selectDelta(d int) {
	if len(a.frames) == 0 {
		return
	}
	a.cur = (a.cur + d + len(a.frames)) % len(a.frames)
}

// ---- Controls panel (immediate mode) ----

func (a *App) drawControls(screen *ebiten.Image, x, y float64) {
	w := 356.0
	py := y

	section := func(t string) { label(screen, t, x, py); py += 20 }
	// A labelled -/+ stepper row. Returns -1, +1 or 0.
	stepper := func(lbl, val string) int {
		ebitenutil.DebugPrintAt(screen, lbl, int(x), int(py)+4)
		ebitenutil.DebugPrintAt(screen, val, int(x)+130, int(py)+4)
		out := 0
		if a.button(screen, x+w-56, py, 26, 22, "-", 0) {
			out = -1
		}
		if a.button(screen, x+w-27, py, 26, 22, "+", 0) {
			out = 1
		}
		py += 28
		return out
	}
	toggle := func(bx float64, lbl string, on bool) bool {
		kind := 0
		if on {
			kind = 3
		}
		return a.button(screen, bx, py, 110, 24, lbl, kind)
	}

	section("SHEET")
	if d := stepper("cell width", fmt.Sprint(a.cw)); d != 0 {
		a.cw = clampi(a.cw+d*8, 8, 512)
	}
	if d := stepper("cell height", fmt.Sprint(a.ch)); d != 0 {
		a.ch = clampi(a.ch+d*8, 8, 512)
	}
	if d := stepper("columns", fmt.Sprint(a.cols)); d != 0 {
		a.cols = clampi(a.cols+d, 1, 20)
	}
	if toggle(x, tlabel("trim", a.trim), a.trim) {
		a.trim = !a.trim
	}
	if toggle(x+120, tlabel("smooth", a.smooth), a.smooth) {
		a.smooth = !a.smooth
	}
	py += 30

	section("FRAME TRANSFORM")
	f := a.curFrame()
	if f == nil {
		return
	}
	if toggle(x, tlabel("flip H", f.flipH), f.flipH) {
		f.flipH = !f.flipH
	}
	if toggle(x+120, tlabel("flip V", f.flipV), f.flipV) {
		f.flipV = !f.flipV
	}
	py += 30
	if d := stepper("rotate (deg)", fmt.Sprint(f.rot)); d != 0 {
		f.rot = (f.rot + d*90) % 360
	}
	if d := stepper("scale X", fmt.Sprintf("%.2f", f.sx)); d != 0 {
		f.sx = clampf(f.sx+float64(d)*0.05, 0.3, 2.0)
	}
	if d := stepper("scale Y", fmt.Sprintf("%.2f", f.sy)); d != 0 {
		f.sy = clampf(f.sy+float64(d)*0.05, 0.3, 2.0)
	}
	if d := stepper("offset X", fmt.Sprintf("%.0f", f.ox)); d != 0 {
		f.ox += float64(d)
	}
	if d := stepper("offset Y", fmt.Sprintf("%.0f", f.oy)); d != 0 {
		f.oy += float64(d)
	}
	// source selector
	ebitenutil.DebugPrintAt(screen, "source", int(x), int(py)+4)
	ebitenutil.DebugPrintAt(screen, trunc(a.sources[f.src].name, 16), int(x)+70, int(py)+4)
	if a.button(screen, x+w-56, py, 26, 22, "<", 0) {
		f.src = (f.src - 1 + len(a.sources)) % len(a.sources)
	}
	if a.button(screen, x+w-27, py, 26, 22, ">", 0) {
		f.src = (f.src + 1) % len(a.sources)
	}
	py += 30

	// frame ops
	if a.button(screen, x, py, 110, 26, "reset", 0) {
		*f = defaultFrame(f.src)
	}
	if a.button(screen, x+120, py, 110, 26, "mirror copy", 1) {
		a.mirrorCopy()
	}
	py += 32
	if a.button(screen, x, py, 110, 26, "duplicate", 0) {
		a.insertFrame(a.cur+1, *f)
		a.cur++
	}
	if a.button(screen, x+120, py, 110, 26, "add frame", 0) {
		a.insertFrame(a.cur+1, defaultFrame(f.src))
		a.cur++
	}
	py += 32
	if a.button(screen, x, py, 70, 26, "< move", 0) {
		a.moveFrame(-1)
	}
	if a.button(screen, x+76, py, 70, 26, "move >", 0) {
		a.moveFrame(1)
	}
	if a.button(screen, x+160, py, 90, 26, "delete", 2) {
		a.deleteFrame()
	}
}

func (a *App) drawPreviewColumn(screen *ebiten.Image, x, y float64) {
	label(screen, "LIVE PREVIEW", x, y-14)
	ps := 160.0
	a.drawChecker(screen, x, y, ps, ps)
	if len(a.frames) > 0 {
		fr := &a.frames[a.animFrame%len(a.frames)]
		a.renderCell(fr)
		op := &ebiten.DrawImageOptions{}
		op.Filter = ebiten.FilterNearest
		op.GeoM.Scale(ps/float64(a.cw), ps/float64(a.ch))
		op.GeoM.Translate(x, y)
		screen.DrawImage(a.cell, op)
	}
	strokeRect(screen, x, y, ps, ps, cLine)

	py := y + ps + 10
	ebitenutil.DebugPrintAt(screen, "fps", int(x), int(py)+4)
	ebitenutil.DebugPrintAt(screen, fmt.Sprint(a.fps), int(x)+60, int(py)+4)
	if a.button(screen, x+ps-56, py, 26, 22, "-", 0) {
		a.fps = clampi(a.fps-1, 1, 24)
	}
	if a.button(screen, x+ps-27, py, 26, 22, "+", 0) {
		a.fps = clampi(a.fps+1, 1, 24)
	}
	py += 28
	pl := "pause"
	if !a.playing {
		pl = "play"
	}
	if a.button(screen, x, py, ps, 24, pl, 0) {
		a.playing = !a.playing
	}
	py += 34

	// sheet preview
	label(screen, "SHEET PREVIEW", x, py)
	py += 18
	sheet, cols, rows := a.buildSheet()
	sw, sh := float64(sheet.Bounds().Dx()), float64(sheet.Bounds().Dy())
	maxW, maxH := 336.0, 150.0
	sc := math.Min(maxW/sw, maxH/sh)
	if sc > 6 {
		sc = 6
	}
	dw, dh := sw*sc, sh*sc
	a.drawChecker(screen, x, py, dw, dh)
	op := &ebiten.DrawImageOptions{}
	op.Filter = ebiten.FilterNearest
	op.GeoM.Scale(sc, sc)
	op.GeoM.Translate(x, py)
	screen.DrawImage(sheet, op)
	strokeRect(screen, x, py, dw, dh, cLine)
	py += dh + 12

	ebitenutil.DebugPrintAt(screen, fmt.Sprintf("grid %dx%d   cell %dx%d   frames %d", cols, rows, a.cw, a.ch, len(a.frames)), int(x), int(py))
	py += 20
	if a.button(screen, x, py, 336, 30, "EXPORT PNG -> "+trunc(a.outPath, 22), 1) {
		a.exportPNG()
	}
}

func (a *App) moveFrame(d int) {
	j := a.cur + d
	if j < 0 || j >= len(a.frames) {
		return
	}
	a.frames[a.cur], a.frames[j] = a.frames[j], a.frames[a.cur]
	a.cur = j
}

func (a *App) deleteFrame() {
	if len(a.frames) <= 1 {
		return
	}
	a.frames = append(a.frames[:a.cur], a.frames[a.cur+1:]...)
	if a.cur >= len(a.frames) {
		a.cur = len(a.frames) - 1
	}
}

func (a *App) drawFilmstrip(screen *ebiten.Image, x, y, w float64) {
	label(screen, "FRAMES", x, y-14)
	vector.DrawFilledRect(screen, float32(x), float32(y), float32(w), 84, cPanel, false)
	tx := x + 8
	for i := range a.frames {
		size := 68.0
		a.drawChecker(screen, tx, y+8, size, size)
		a.renderCell(&a.frames[i])
		op := &ebiten.DrawImageOptions{}
		op.Filter = ebiten.FilterNearest
		op.GeoM.Scale(size/float64(a.cw), size/float64(a.ch))
		op.GeoM.Translate(tx, y+8)
		screen.DrawImage(a.cell, op)
		col := cLine
		if i == a.cur {
			col = cAccent
		}
		strokeRect(screen, tx, y+8, size, size, col)
		ebitenutil.DebugPrintAt(screen, fmt.Sprint(i+1), int(tx)+3, int(y)+10)
		if a.mx >= tx && a.mx < tx+size && a.my >= y+8 && a.my < y+8+size && a.clicked {
			a.cur = i
		}
		tx += size + 8
		if tx > x+w-size {
			break
		}
	}
	// add button
	if a.button(screen, tx, y+8, 68, 68, "  +", 0) {
		f := defaultFrame(0)
		if cf := a.curFrame(); cf != nil {
			f.src = cf.src
		}
		a.frames = append(a.frames, f)
		a.cur = len(a.frames) - 1
	}
}

// ---- Widgets ----

// button draws an immediate-mode button. kind: 0 normal, 1 primary, 2 danger,
// 3 toggle-on. Returns true if clicked this frame.
func (a *App) button(dst *ebiten.Image, x, y, w, h float64, lbl string, kind int) bool {
	hov := a.mx >= x && a.mx < x+w && a.my >= y && a.my < y+h
	var fill, border color.RGBA
	switch kind {
	case 1:
		fill, border = cAccentD, cAccent
	case 2:
		fill, border = cDangerD, cDanger
	case 3:
		fill, border = cAccentD, cAccent
	default:
		fill, border = cPanel2, cLine
	}
	if hov {
		fill = cHover
		border = cAccent
	}
	vector.DrawFilledRect(dst, float32(x), float32(y), float32(w), float32(h), fill, false)
	strokeRect(dst, x, y, w, h, border)
	ebitenutil.DebugPrintAt(dst, lbl, int(x)+7, int(y)+int(h/2)-8)
	return hov && a.clicked
}

func (a *App) drawChecker(dst *ebiten.Image, x, y, w, h float64) {
	const s = 8.0
	for yy := 0.0; yy < h; yy += s {
		for xx := 0.0; xx < w; xx += s {
			c := cCheckA
			if int(xx/s+yy/s)%2 == 0 {
				c = cCheckB
			}
			cw := math.Min(s, w-xx)
			chh := math.Min(s, h-yy)
			vector.DrawFilledRect(dst, float32(x+xx), float32(y+yy), float32(cw), float32(chh), c, false)
		}
	}
}

func label(dst *ebiten.Image, t string, x, y float64) {
	ebitenutil.DebugPrintAt(dst, t, int(x), int(y))
}

func strokeRect(dst *ebiten.Image, x, y, w, h float64, c color.RGBA) {
	vector.DrawFilledRect(dst, float32(x), float32(y), float32(w), 1, c, false)
	vector.DrawFilledRect(dst, float32(x), float32(y+h-1), float32(w), 1, c, false)
	vector.DrawFilledRect(dst, float32(x), float32(y), 1, float32(h), c, false)
	vector.DrawFilledRect(dst, float32(x+w-1), float32(y), 1, float32(h), c, false)
}

func tlabel(name string, on bool) string {
	if on {
		return "[x] " + name
	}
	return "[ ] " + name
}

func trunc(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return "..." + s[len(s)-n+3:]
}

func (a *App) Layout(int, int) (int, int) { return winW, winH }

// ---- Loading ----

func loadSources(dir string) ([]*Source, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	names := []string{}
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		ext := strings.ToLower(filepath.Ext(e.Name()))
		if ext == ".png" || ext == ".jpg" || ext == ".jpeg" {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	var sources []*Source
	for _, name := range names {
		s, err := loadSource(filepath.Join(dir, name))
		if err != nil {
			log.Printf("skip %s: %v", name, err)
			continue
		}
		sources = append(sources, s)
	}
	return sources, nil
}

func loadSource(path string) (*Source, error) {
	fp, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer fp.Close()
	src, _, err := image.Decode(fp)
	if err != nil {
		return nil, err
	}
	b := src.Bounds()
	return &Source{
		name: filepath.Base(path),
		img:  ebiten.NewImageFromImage(src),
		bbox: opaqueBounds(src),
		w:    b.Dx(),
		h:    b.Dy(),
	}, nil
}

// opaqueBounds returns the tight bounding box of non-transparent pixels.
func opaqueBounds(img image.Image) image.Rectangle {
	b := img.Bounds()
	minX, minY, maxX, maxY := b.Max.X, b.Max.Y, b.Min.X-1, b.Min.Y-1
	for y := b.Min.Y; y < b.Max.Y; y++ {
		for x := b.Min.X; x < b.Max.X; x++ {
			if _, _, _, alpha := img.At(x, y).RGBA(); alpha > 2000 {
				if x < minX {
					minX = x
				}
				if x > maxX {
					maxX = x
				}
				if y < minY {
					minY = y
				}
				if y > maxY {
					maxY = y
				}
			}
		}
	}
	if maxX < minX {
		return b // fully transparent; use full image
	}
	return image.Rect(minX, minY, maxX+1, maxY+1)
}

// ---- helpers ----

func clampi(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}
func clampf(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}
func maxi(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func main() {
	dir := flag.String("dir", "assets", "folder to load sprite PNGs from")
	out := flag.String("out", "", "output sheet path (default <dir>/enemy_spritesheet.png)")
	flag.Parse()
	if *out == "" {
		*out = filepath.Join(*dir, "enemy_spritesheet.png")
	}

	sources, err := loadSources(*dir)
	if err != nil {
		log.Printf("warning: could not read %s: %v", *dir, err)
	}
	app := newApp(sources, *out)

	ebiten.SetWindowSize(winW, winH)
	ebiten.SetWindowTitle("Snake Forge — Spritesheet Maker")
	if err := ebiten.RunGame(app); err != nil {
		log.Fatal(err)
	}
}
