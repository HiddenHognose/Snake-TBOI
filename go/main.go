// Command snake-roguelite is a top-down, Binding of Isaac-inspired roguelite
// starring snakes. This file is the minimal playable starter: a window with an
// animated snake you can move around a room. Build it up from here.
package main

import (
	"bytes"
	_ "embed"
	"image"
	"log"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
)

const (
	screenWidth  = 640
	screenHeight = 480

	// The snake sprite sheet is a 320x160 grid: 10 columns x 5 rows of 32x32
	// frames. Each row is one animation state (see the row* constants below).
	frameW    = 32
	frameH    = 32
	sheetCols = 10
	sheetRows = 5

	playerScale = 2.0 // 32px frames drawn at 64px
	playerSpeed = 3.0 // pixels per tick

	// Ticks (60/sec) each animation frame is held. Matches the original game's
	// 8-ticks-per-frame pacing for idle/move.
	animTicksPerFrame = 8
)

// Animation rows within the sprite sheet, as defined by the original game's
// SnakeAnimation.split_sprite_sheet.
const (
	rowIdle      = 0
	rowGoingDown = 1
	rowMove      = 2
	rowAttack    = 3
	rowDefeated  = 4
)

//go:embed assets/snake_sheet.png
var snakeSheetPNG []byte

// Game holds all mutable state. Ebitengine drives it via Update (logic, ~60/s)
// and Draw (rendering).
type Game struct {
	// anims[row] is the list of non-empty frames for that animation state.
	anims [sheetRows][]*ebiten.Image

	// Player position is the center of the sprite, in screen coordinates.
	playerX, playerY float64
	facingRight      bool

	animState int // one of the row* constants
	animFrame int
	animTick  int
}

func newGame() *Game {
	img, _, err := image.Decode(bytes.NewReader(snakeSheetPNG))
	if err != nil {
		log.Fatalf("decoding snake sprite sheet: %v", err)
	}
	sheet := ebiten.NewImageFromImage(img)

	g := &Game{
		playerX:   screenWidth / 2,
		playerY:   screenHeight / 2,
		animState: rowIdle,
	}

	// Slice the sheet into per-row animation frames, skipping any fully
	// transparent cells (some rows don't use all 10 columns).
	for row := 0; row < sheetRows; row++ {
		for col := 0; col < sheetCols; col++ {
			rect := image.Rect(col*frameW, row*frameH, (col+1)*frameW, (row+1)*frameH)
			frame := sheet.SubImage(rect).(*ebiten.Image)
			if !frameHasContent(img, rect) {
				continue
			}
			g.anims[row] = append(g.anims[row], frame)
		}
		if len(g.anims[row]) == 0 {
			// Guard against an empty animation causing a divide-by-zero / blank draw.
			g.anims[row] = append(g.anims[row], sheet.SubImage(image.Rect(0, row*frameH, frameW, (row+1)*frameH)).(*ebiten.Image))
		}
	}
	return g
}

// frameHasContent reports whether any pixel in rect is non-transparent.
func frameHasContent(img image.Image, rect image.Rectangle) bool {
	for y := rect.Min.Y; y < rect.Max.Y; y++ {
		for x := rect.Min.X; x < rect.Max.X; x++ {
			if _, _, _, a := img.At(x, y).RGBA(); a > 0 {
				return true
			}
		}
	}
	return false
}

func (g *Game) Update() error {
	var dx, dy float64
	if ebiten.IsKeyPressed(ebiten.KeyLeft) || ebiten.IsKeyPressed(ebiten.KeyA) {
		dx -= playerSpeed
	}
	if ebiten.IsKeyPressed(ebiten.KeyRight) || ebiten.IsKeyPressed(ebiten.KeyD) {
		dx += playerSpeed
	}
	if ebiten.IsKeyPressed(ebiten.KeyUp) || ebiten.IsKeyPressed(ebiten.KeyW) {
		dy -= playerSpeed
	}
	if ebiten.IsKeyPressed(ebiten.KeyDown) || ebiten.IsKeyPressed(ebiten.KeyS) {
		dy += playerSpeed
	}

	moving := dx != 0 || dy != 0
	if dx < 0 {
		g.facingRight = false
	} else if dx > 0 {
		g.facingRight = true
	}

	g.playerX += dx
	g.playerY += dy

	// Keep the sprite fully inside the room.
	halfW := frameW * playerScale / 2
	halfH := frameH * playerScale / 2
	g.playerX = clamp(g.playerX, halfW, screenWidth-halfW)
	g.playerY = clamp(g.playerY, halfH, screenHeight-halfH)

	// Pick the animation state and advance its frames.
	state := rowIdle
	if moving {
		state = rowMove
	}
	if state != g.animState {
		g.animState = state
		g.animFrame = 0
		g.animTick = 0
	}
	g.animTick++
	if g.animTick >= animTicksPerFrame {
		g.animTick = 0
		g.animFrame = (g.animFrame + 1) % len(g.anims[g.animState])
	}

	if inpututil.IsKeyJustPressed(ebiten.KeyEscape) {
		return ebiten.Termination
	}
	return nil
}

func (g *Game) Draw(screen *ebiten.Image) {
	frame := g.anims[g.animState][g.animFrame]

	op := &ebiten.DrawImageOptions{}
	if g.facingRight {
		// Flip horizontally: scale x by -1 then shift back into place.
		op.GeoM.Scale(-playerScale, playerScale)
		op.GeoM.Translate(frameW*playerScale, 0)
	} else {
		op.GeoM.Scale(playerScale, playerScale)
	}
	// Center the (scaled) frame on the player position.
	op.GeoM.Translate(g.playerX-frameW*playerScale/2, g.playerY-frameH*playerScale/2)
	screen.DrawImage(frame, op)

	ebitenutil.DebugPrint(screen, "Snake Roguelite — move: WASD/arrows   quit: Esc")
}

// Layout maps the game's logical resolution to the window; Ebitengine handles
// scaling for us.
func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	return screenWidth, screenHeight
}

func clamp(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func main() {
	ebiten.SetWindowSize(screenWidth*2, screenHeight*2)
	ebiten.SetWindowTitle("Snake Roguelite")
	if err := ebiten.RunGame(newGame()); err != nil {
		log.Fatal(err)
	}
}
