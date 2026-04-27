# PyOpenGL Maze Generator and Solver

This project builds and runs a rectangular maze using Python graphics. It uses `pygame` + `PyOpenGL` when available and falls back to the built-in `tkinter` canvas when those packages are not installed.

It does two things:

1. Generates a random maze dynamically.
2. Solves the maze from a left-edge opening to a right-edge opening.
3. Supports the addendum bonus mode with interior start/end cells and extra wall removals that create cycles.

## How It Works

The maze is represented with two wall arrays:

- `north_wall[rows + 1][cols]`
- `east_wall[rows][cols + 1]`

The representation follows the assignment idea closely:

- `north_wall` stores horizontal wall segments.
- `east_wall` stores vertical wall segments.
- `north_wall[0][c]` is the phantom row whose north walls form the bottom edge.
- `east_wall[r][0]` stores the left boundary where the entrance can be opened.

## Maze Generation

The generator uses a stack-based depth-first search "mouse" algorithm:

- Start with every wall intact.
- Put the mouse in a random cell.
- Look for neighboring cells that still have all four walls intact.
- Pick one candidate randomly and eat through the connecting wall.
- Push deeper into the maze with a stack.
- When trapped, backtrack by popping the stack.

Because each new cell is visited once through DFS, the default maze is a proper maze: every cell is connected, and there is a unique path between any two cells.

Using a stack makes the mouse dive deeply before backtracking, which creates the long winding corridors typical of DFS mazes. A queue would bias the algorithm toward breadth-first expansion and would create later passages in a much more level-by-level order.

## Maze Solving

The solver also uses backtracking:

- Start at the left opening.
- Move to a random reachable unvisited neighbor.
- Keep the current route on a stack.
- If the mouse reaches a dead end, mark that cell blue and pop back.
- The active mouse is shown as a red dot.
- When the exit is found, the final solution path is drawn in green.

## Bonus Challenge

Bonus mode follows the assignment addendum more closely:

- it places the start and end in the interior of the maze
- it removes extra walls randomly after the proper maze is built
- it creates cycles that make the maze more interesting than a strict tree

Use:

```bash
python main.py --bonus
```

This defaults to an extra wall chance of `0.05`, which approximates the "1 in 20" idea from the assignment addendum.

You can also tune it manually:

```bash
python main.py --bonus --extra-wall-chance 0.08
```

## Install

```bash
python -m pip install -r requirements.txt
```

If `pygame` is unavailable on your Python version, the program still runs with the built-in Tkinter visualizer.

## Run

```bash
python main.py
```

Useful options:

```bash
python main.py --rows 20 --cols 30
python main.py --rows 20 --cols 30 --bonus
python main.py --rows 20 --cols 30 --bonus --extra-wall-chance 0.05
python main.py --seed 7
```

## Headless Verification

If you want to verify the algorithm without opening the OpenGL window:

```bash
python main.py --headless
```

## Controls

- `Space`: pause/resume
- `R`: build a fresh maze
- `B`: toggle bonus mode and rebuild
- `Esc`: quit

## Loom Recording Tips

For the recording, show:

- the wall-eating generation animation
- the red solving mouse
- the blue dead ends during backtracking
- the bonus mode with cycles enabled using `B` or `--bonus`
