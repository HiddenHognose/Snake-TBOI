// Command snake-roguelite is a top-down, Binding of Isaac-inspired roguelite
// starring snakes. This file is the minimal playable starter: a window with a
// single sprite you can move around a room. Build it up from here.
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

	playerSize  = 48.0 // on-screen size of the player sprite, in pixels
	playerSpeed = 3.0  // pixels per tick
)

//go:embed assets/player.png
var playerPNG []byte

// Game holds all mutable state. Ebitengine drives it via Update (logic, ~60/s)
// and Draw (rendering).
type Game struct {
	playerImg *ebiten.Image

	// Player position is the center of the sprite, in screen coordinates.
	playerX, playerY float64
}

func newGame() *Game {
	img, _, err := image.Decode(bytes.NewReader(playerPNG))
	if err != nil {
		log.Fatalf("decoding player sprite: %v", err)
	}
	return &Game{
		playerImg: ebiten.NewImageFromImage(img),
		playerX:   screenWidth / 2,
		playerY:   screenHeight / 2,
	}
}

func (g *Game) Update() error {
	// Top-down movement: WASD or arrow keys.
	if ebiten.IsKeyPressed(ebiten.KeyLeft) || ebiten.IsKeyPressed(ebiten.KeyA) {
		g.playerX -= playerSpeed
	}
	if ebiten.IsKeyPressed(ebiten.KeyRight) || ebiten.IsKeyPressed(ebiten.KeyD) {
		g.playerX += playerSpeed
	}
	if ebiten.IsKeyPressed(ebiten.KeyUp) || ebiten.IsKeyPressed(ebiten.KeyW) {
		g.playerY -= playerSpeed
	}
	if ebiten.IsKeyPressed(ebiten.KeyDown) || ebiten.IsKeyPressed(ebiten.KeyS) {
		g.playerY += playerSpeed
	}

	// Keep the sprite fully inside the room.
	half := playerSize / 2
	g.playerX = clamp(g.playerX, half, screenWidth-half)
	g.playerY = clamp(g.playerY, half, screenHeight-half)

	if inpututil.IsKeyJustPressed(ebiten.KeyEscape) {
		return ebiten.Termination
	}
	return nil
}

func (g *Game) Draw(screen *ebiten.Image) {
	// Draw the player sprite scaled to playerSize and centered on its position.
	bounds := g.playerImg.Bounds()
	sx := playerSize / float64(bounds.Dx())
	sy := playerSize / float64(bounds.Dy())

	op := &ebiten.DrawImageOptions{}
	op.GeoM.Scale(sx, sy)
	op.GeoM.Translate(g.playerX-playerSize/2, g.playerY-playerSize/2)
	screen.DrawImage(g.playerImg, op)

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
