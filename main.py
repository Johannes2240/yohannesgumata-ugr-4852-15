from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass

try:
    import pygame
    from pygame.locals import DOUBLEBUF, OPENGL
    from OpenGL.GL import (
        GL_COLOR_BUFFER_BIT,
        GL_LINE_LOOP,
        GL_LINE_STRIP,
        GL_LINES,
        GL_POLYGON,
        GL_PROJECTION,
        GL_MODELVIEW,
        glBegin,
        glClear,
        glClearColor,
        glColor3f,
        glEnd,
        glLineWidth,
        glLoadIdentity,
        glMatrixMode,
        glOrtho,
        glVertex2f,
        glViewport,
    )

    GRAPHICS_READY = True
except ImportError:
    pygame = None
    GRAPHICS_READY = False

try:
    import tkinter as tk

    TK_READY = True
except ImportError:
    tk = None
    TK_READY = False


Direction = tuple[int, int]
Cell = tuple[int, int]


@dataclass
class MazeStats:
    carved_passages: int = 0
    extra_openings: int = 0
    generation_steps: int = 0
    solve_steps: int = 0


class Maze:
    """Maze model using north/east wall arrays plus DFS generation/solving."""

    def __init__(
        self,
        rows: int,
        cols: int,
        extra_wall_chance: float = 0.0,
        seed: int | None = None,
        bonus_mode: bool = False,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.extra_wall_chance = max(0.0, min(1.0, extra_wall_chance))
        self.bonus_mode = bonus_mode
        self.rng = random.Random(seed)
        self.reset()

    def reset(self) -> None:
        # Assignment-style northWall array:
        # north_wall[k][c] is 1 when the horizontal wall segment is intact.
        # Index 0 is the phantom row whose north walls form the maze's bottom edge.
        # Index self.rows is the top boundary of the maze.
        self.north_wall = [[1 for _ in range(self.cols)] for _ in range(self.rows + 1)]

        # Assignment-style eastWall array:
        # east_wall[r][k] is 1 when the vertical wall segment is intact.
        # east_wall[r][0] is the left boundary where the entrance can be opened.
        # east_wall[r][self.cols] is the right boundary where the exit can be opened.
        self.east_wall = [[1 for _ in range(self.cols + 1)] for _ in range(self.rows)]

        self.generation_visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.solver_visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]

        start = (self.rng.randrange(self.rows), self.rng.randrange(self.cols))
        self.generation_stack: list[Cell] = [start]
        self.generation_visited[start[0]][start[1]] = True

        self.generation_complete = False
        self.cycles_added = False
        self.solver_ready = False
        self.solver_complete = False

        self.start_cell: Cell | None = None
        self.end_cell: Cell | None = None
        self.solve_stack: list[Cell] = []
        self.solution_path: list[Cell] = []
        self.dead_ends: set[Cell] = set()
        self.stats = MazeStats()

    def cell_has_all_walls(self, row: int, col: int) -> bool:
        north_index = self.rows - row
        south_index = self.rows - row - 1
        return (
            self.north_wall[north_index][col] == 1
            and self.north_wall[south_index][col] == 1
            and self.east_wall[row][col] == 1
            and self.east_wall[row][col + 1] == 1
        )

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def generation_neighbors(self, row: int, col: int) -> list[Cell]:
        candidates: list[Cell] = []
        for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_row = row + d_row
            next_col = col + d_col
            if not self.in_bounds(next_row, next_col):
                continue
            if self.generation_visited[next_row][next_col]:
                continue
            if self.cell_has_all_walls(next_row, next_col):
                candidates.append((next_row, next_col))
        return candidates

    def carve_between(self, current: Cell, neighbor: Cell, is_extra: bool = False) -> None:
        row, col = current
        next_row, next_col = neighbor

        if next_row == row - 1:
            self.north_wall[self.rows - row][col] = 0
        elif next_row == row + 1:
            self.north_wall[self.rows - row - 1][col] = 0
        elif next_col == col - 1:
            self.east_wall[row][col] = 0
        elif next_col == col + 1:
            self.east_wall[row][col + 1] = 0
        else:
            raise ValueError("Cells are not adjacent.")

        if is_extra:
            self.stats.extra_openings += 1
        else:
            self.stats.carved_passages += 1

    def finish_generation(self) -> None:
        if self.extra_wall_chance > 0.0 and not self.cycles_added:
            self.add_extra_openings()
        self.select_entrances()
        self.prepare_solver()
        self.generation_complete = True

    def generate_step(self) -> bool:
        if self.generation_complete:
            return True

        if not self.generation_stack:
            self.finish_generation()
            return True

        current = self.generation_stack[-1]
        options = self.generation_neighbors(*current)

        if options:
            chosen = self.rng.choice(options)
            self.carve_between(current, chosen)
            self.generation_visited[chosen[0]][chosen[1]] = True
            self.generation_stack.append(chosen)
        else:
            self.generation_stack.pop()

        self.stats.generation_steps += 1

        if not self.generation_stack:
            self.finish_generation()
            return True

        return False

    def add_extra_openings(self) -> None:
        for row in range(self.rows):
            for col in range(self.cols):
                if row + 1 < self.rows and self.rng.random() < self.extra_wall_chance:
                    south_neighbor = (row + 1, col)
                    south_wall_index = self.rows - row - 1
                    if self.north_wall[south_wall_index][col] == 1:
                        self.carve_between((row, col), south_neighbor, is_extra=True)
                if col + 1 < self.cols and self.rng.random() < self.extra_wall_chance:
                    east_neighbor = (row, col + 1)
                    if self.east_wall[row][col + 1] == 1:
                        self.carve_between((row, col), east_neighbor, is_extra=True)

        self.cycles_added = True

    def select_entrances(self) -> None:
        if self.bonus_mode and self.rows > 2 and self.cols > 2:
            interior_cells = [(row, col) for row in range(1, self.rows - 1) for col in range(1, self.cols - 1)]
            self.start_cell = self.rng.choice(interior_cells)
            self.end_cell = self.rng.choice(interior_cells)
            while self.end_cell == self.start_cell:
                self.end_cell = self.rng.choice(interior_cells)
            return

        start_row = self.rng.randrange(self.rows)
        end_row = self.rng.randrange(self.rows)

        self.start_cell = (start_row, 0)
        self.end_cell = (end_row, self.cols - 1)

        self.east_wall[start_row][0] = 0
        self.east_wall[end_row][self.cols] = 0

    def can_move(self, current: Cell, neighbor: Cell) -> bool:
        row, col = current
        next_row, next_col = neighbor

        if not self.in_bounds(next_row, next_col):
            return False

        if next_row == row - 1 and next_col == col:
            return self.north_wall[self.rows - row][col] == 0
        if next_row == row + 1 and next_col == col:
            return self.north_wall[self.rows - row - 1][col] == 0
        if next_row == row and next_col == col - 1:
            return self.east_wall[row][col] == 0
        if next_row == row and next_col == col + 1:
            return self.east_wall[row][col + 1] == 0
        return False

    def solver_neighbors(self, row: int, col: int) -> list[Cell]:
        choices: list[Cell] = []
        for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_row = row + d_row
            next_col = col + d_col
            if not self.in_bounds(next_row, next_col):
                continue
            if self.solver_visited[next_row][next_col]:
                continue
            if self.can_move((row, col), (next_row, next_col)):
                choices.append((next_row, next_col))
        return choices

    def prepare_solver(self) -> None:
        if self.start_cell is None:
            raise RuntimeError("Start cell was not selected.")

        self.solver_visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.solve_stack = [self.start_cell]
        self.solver_visited[self.start_cell[0]][self.start_cell[1]] = True
        self.dead_ends.clear()
        self.solution_path = []
        self.solver_ready = True
        self.solver_complete = False

    def solve_step(self) -> bool:
        if self.solver_complete:
            return True

        if not self.solve_stack:
            self.solver_complete = True
            self.solution_path = []
            return True

        current = self.solve_stack[-1]
        if current == self.end_cell:
            self.solution_path = list(self.solve_stack)
            self.solver_complete = True
            return True

        options = self.solver_neighbors(*current)

        if options:
            chosen = self.rng.choice(options)
            self.solver_visited[chosen[0]][chosen[1]] = True
            self.solve_stack.append(chosen)
        else:
            self.dead_ends.add(current)
            self.solve_stack.pop()

        self.stats.solve_steps += 1

        if self.solve_stack and self.solve_stack[-1] == self.end_cell:
            self.solution_path = list(self.solve_stack)
            self.solver_complete = True
            return True

        return False

    def generation_cursor(self) -> Cell | None:
        return self.generation_stack[-1] if self.generation_stack else None

    def solver_cursor(self) -> Cell | None:
        return self.solve_stack[-1] if self.solve_stack else None


class MazeWindow:
    def __init__(
        self,
        maze: Maze,
        width: int,
        height: int,
        generation_steps_per_frame: int,
        solve_steps_per_frame: int,
    ) -> None:
        if not GRAPHICS_READY:
            raise RuntimeError(
                "PyOpenGL/pygame are missing. Install dependencies with: pip install -r requirements.txt"
            )

        self.maze = maze
        self.width = width
        self.height = height
        self.generation_steps_per_frame = generation_steps_per_frame
        self.solve_steps_per_frame = solve_steps_per_frame
        self.paused = False
        self.running = True

        pygame.init()
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()

        glClearColor(0.95, 0.95, 0.95, 1.0)
        self.resize(self.width, self.height)
        self.update_caption()

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def update_caption(self) -> None:
        if not self.maze.generation_complete:
            phase = "Generating"
        elif not self.maze.solver_complete:
            phase = "Solving"
        else:
            phase = "Solved"

        if self.maze.bonus_mode:
            mode = f"bonus mode ({self.maze.extra_wall_chance:.2f} extra wall chance)"
        else:
            mode = "proper maze"
        pygame.display.set_caption(
            f"Maze Generator and Solver | {phase} | {mode} | "
            "Space pause, R reset, B toggle bonus, Esc quit"
        )

    def grid_geometry(self) -> tuple[float, float, float]:
        margin = 40.0
        cell_size = min((self.width - 2 * margin) / self.maze.cols, (self.height - 2 * margin) / self.maze.rows)
        return margin, margin, cell_size

    def cell_bounds(self, row: int, col: int) -> tuple[float, float, float, float]:
        x0, y0, cell_size = self.grid_geometry()
        left = x0 + col * cell_size
        bottom = y0 + (self.maze.rows - 1 - row) * cell_size
        return left, bottom, left + cell_size, bottom + cell_size

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        left, bottom, right, top = self.cell_bounds(row, col)
        return (left + right) / 2.0, (bottom + top) / 2.0

    def draw_polygon(self, points: list[tuple[float, float]], color: tuple[float, float, float]) -> None:
        glColor3f(*color)
        glBegin(GL_POLYGON)
        for x_value, y_value in points:
            glVertex2f(x_value, y_value)
        glEnd()

    def draw_line(self, start: tuple[float, float], end: tuple[float, float], color: tuple[float, float, float], width: float) -> None:
        glColor3f(*color)
        glLineWidth(width)
        glBegin(GL_LINES)
        glVertex2f(*start)
        glVertex2f(*end)
        glEnd()

    def draw_disc(self, center: tuple[float, float], radius: float, color: tuple[float, float, float]) -> None:
        glColor3f(*color)
        glBegin(GL_POLYGON)
        for step in range(24):
            angle = (math.tau * step) / 24.0
            glVertex2f(center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius)
        glEnd()

    def draw_path_line(self, path: list[Cell], color: tuple[float, float, float], width: float) -> None:
        if len(path) < 2:
            return

        glColor3f(*color)
        glLineWidth(width)
        glBegin(GL_LINE_STRIP)
        for row, col in path:
            glVertex2f(*self.cell_center(row, col))
        glEnd()

    def draw_cell_fill(self, row: int, col: int, color: tuple[float, float, float], inset_ratio: float = 0.18) -> None:
        left, bottom, right, top = self.cell_bounds(row, col)
        cell_size = right - left
        inset = cell_size * inset_ratio
        self.draw_polygon(
            [
                (left + inset, bottom + inset),
                (right - inset, bottom + inset),
                (right - inset, top - inset),
                (left + inset, top - inset),
            ],
            color,
        )

    def update_simulation(self) -> None:
        if self.paused:
            return

        if not self.maze.generation_complete:
            for _ in range(self.generation_steps_per_frame):
                if self.maze.generate_step():
                    break
            self.update_caption()
            return

        if not self.maze.solver_complete:
            for _ in range(self.solve_steps_per_frame):
                if self.maze.solve_step():
                    break
            self.update_caption()

    def draw(self) -> None:
        glClear(GL_COLOR_BUFFER_BIT)
        _, _, cell_size = self.grid_geometry()

        if self.maze.start_cell is not None:
            self.draw_cell_fill(*self.maze.start_cell, color=(0.78, 0.93, 0.78), inset_ratio=0.28)
        if self.maze.end_cell is not None:
            self.draw_cell_fill(*self.maze.end_cell, color=(0.95, 0.86, 0.60), inset_ratio=0.28)

        for row, col in self.maze.dead_ends:
            self.draw_disc(self.cell_center(row, col), cell_size * 0.12, (0.18, 0.37, 0.78))

        if self.maze.solution_path:
            self.draw_path_line(self.maze.solution_path, color=(0.12, 0.62, 0.20), width=max(2.0, cell_size * 0.11))

        generation_cursor = self.maze.generation_cursor()
        if generation_cursor is not None:
            self.draw_disc(self.cell_center(*generation_cursor), cell_size * 0.16, (0.12, 0.67, 0.28))

        solver_cursor = self.maze.solver_cursor()
        if solver_cursor is not None:
            self.draw_disc(self.cell_center(*solver_cursor), cell_size * 0.16, (0.86, 0.12, 0.12))

        x0, y0, cell_size = self.grid_geometry()
        wall_width = max(2.0, cell_size * 0.08)

        for wall_index, row in enumerate(self.maze.north_wall):
            y_value = y0 + wall_index * cell_size
            for col, has_wall in enumerate(row):
                if has_wall:
                    start = (x0 + col * cell_size, y_value)
                    end = (x0 + (col + 1) * cell_size, y_value)
                    self.draw_line(start, end, (0.16, 0.13, 0.13), wall_width)

        for row_index, row in enumerate(self.maze.east_wall):
            bottom = y0 + (self.maze.rows - 1 - row_index) * cell_size
            top = bottom + cell_size
            for wall_index, has_wall in enumerate(row):
                if has_wall:
                    x_value = x0 + wall_index * cell_size
                    self.draw_line((x_value, bottom), (x_value, top), (0.16, 0.13, 0.13), wall_width)

        pygame.display.flip()

    def handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self.maze.reset()
            self.update_caption()
        elif key == pygame.K_b:
            self.maze.bonus_mode = not self.maze.bonus_mode
            self.maze.extra_wall_chance = 0.05 if self.maze.bonus_mode else 0.0
            self.maze.reset()
            self.update_caption()

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            self.update_simulation()
            self.draw()
            self.clock.tick(60)

        pygame.quit()


class TkMazeWindow:
    def __init__(
        self,
        maze: Maze,
        width: int,
        height: int,
        generation_steps_per_frame: int,
        solve_steps_per_frame: int,
    ) -> None:
        if not TK_READY:
            raise RuntimeError("No graphical backend is available. Use --headless to run without a window.")

        self.maze = maze
        self.width = width
        self.height = height
        self.generation_steps_per_frame = generation_steps_per_frame
        self.solve_steps_per_frame = solve_steps_per_frame
        self.paused = False
        self.running = True

        self.root = tk.Tk()
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.minsize(480, 360)
        self.root.configure(bg="#f2f2f2")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<space>", lambda _event: self.handle_action("space"))
        self.root.bind("<Escape>", lambda _event: self.handle_action("escape"))
        self.root.bind("<KeyPress-r>", lambda _event: self.handle_action("reset"))
        self.root.bind("<KeyPress-R>", lambda _event: self.handle_action("reset"))
        self.root.bind("<KeyPress-b>", lambda _event: self.handle_action("bonus"))
        self.root.bind("<KeyPress-B>", lambda _event: self.handle_action("bonus"))

        self.canvas = tk.Canvas(self.root, bg="#f2f2f2", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.update_caption()

    def close(self) -> None:
        self.running = False
        self.root.destroy()

    def on_resize(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self.width = max(1, event.width)
            self.height = max(1, event.height)

    def update_caption(self) -> None:
        if not self.maze.generation_complete:
            phase = "Generating"
        elif not self.maze.solver_complete:
            phase = "Solving"
        else:
            phase = "Solved"

        if self.maze.bonus_mode:
            mode = f"bonus mode ({self.maze.extra_wall_chance:.2f} extra wall chance)"
        else:
            mode = "proper maze"

        self.root.title(
            f"Maze Generator and Solver | {phase} | {mode} | "
            "Space pause, R reset, B toggle bonus, Esc quit"
        )

    def grid_geometry(self) -> tuple[float, float, float]:
        margin = 40.0
        cell_size = min((self.width - 2 * margin) / self.maze.cols, (self.height - 2 * margin) / self.maze.rows)
        return margin, margin, cell_size

    def cell_bounds(self, row: int, col: int) -> tuple[float, float, float, float]:
        x0, y0, cell_size = self.grid_geometry()
        left = x0 + col * cell_size
        bottom = y0 + (self.maze.rows - 1 - row) * cell_size
        top = bottom + cell_size
        canvas_top = self.height - top
        canvas_bottom = self.height - bottom
        return left, canvas_top, left + cell_size, canvas_bottom

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        left, top, right, bottom = self.cell_bounds(row, col)
        return (left + right) / 2.0, (top + bottom) / 2.0

    def draw_path_line(self, path: list[Cell], color: str, width: float) -> None:
        if len(path) < 2:
            return
        points: list[float] = []
        for row, col in path:
            x_value, y_value = self.cell_center(row, col)
            points.extend([x_value, y_value])
        self.canvas.create_line(*points, fill=color, width=width, smooth=True)

    def draw_disc(self, center: tuple[float, float], radius: float, color: str) -> None:
        self.canvas.create_oval(
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
            fill=color,
            outline=color,
        )

    def draw_cell_fill(self, row: int, col: int, color: str, inset_ratio: float = 0.18) -> None:
        left, top, right, bottom = self.cell_bounds(row, col)
        cell_size = right - left
        inset = cell_size * inset_ratio
        self.canvas.create_rectangle(
            left + inset,
            top + inset,
            right - inset,
            bottom - inset,
            fill=color,
            outline=color,
        )

    def update_simulation(self) -> None:
        if self.paused:
            return

        if not self.maze.generation_complete:
            for _ in range(self.generation_steps_per_frame):
                if self.maze.generate_step():
                    break
            self.update_caption()
            return

        if not self.maze.solver_complete:
            for _ in range(self.solve_steps_per_frame):
                if self.maze.solve_step():
                    break
            self.update_caption()

    def draw(self) -> None:
        self.canvas.delete("all")
        _, _, cell_size = self.grid_geometry()

        if self.maze.start_cell is not None:
            self.draw_cell_fill(*self.maze.start_cell, color="#c8edc8", inset_ratio=0.28)
        if self.maze.end_cell is not None:
            self.draw_cell_fill(*self.maze.end_cell, color="#f2db99", inset_ratio=0.28)

        for row, col in self.maze.dead_ends:
            self.draw_disc(self.cell_center(row, col), cell_size * 0.12, "#2f62c7")

        if self.maze.solution_path:
            self.draw_path_line(self.maze.solution_path, color="#1f9933", width=max(2.0, cell_size * 0.11))

        generation_cursor = self.maze.generation_cursor()
        if generation_cursor is not None:
            self.draw_disc(self.cell_center(*generation_cursor), cell_size * 0.16, "#23a847")

        solver_cursor = self.maze.solver_cursor()
        if solver_cursor is not None:
            self.draw_disc(self.cell_center(*solver_cursor), cell_size * 0.16, "#db2323")

        x0, y0, cell_size = self.grid_geometry()
        wall_width = max(2.0, cell_size * 0.08)
        wall_color = "#2a2121"

        for wall_index, row in enumerate(self.maze.north_wall):
            y_value = y0 + wall_index * cell_size
            canvas_y = self.height - y_value
            for col, has_wall in enumerate(row):
                if has_wall:
                    self.canvas.create_line(
                        x0 + col * cell_size,
                        canvas_y,
                        x0 + (col + 1) * cell_size,
                        canvas_y,
                        fill=wall_color,
                        width=wall_width,
                    )

        for row_index, row in enumerate(self.maze.east_wall):
            bottom = y0 + (self.maze.rows - 1 - row_index) * cell_size
            top = bottom + cell_size
            canvas_bottom = self.height - bottom
            canvas_top = self.height - top
            for wall_index, has_wall in enumerate(row):
                if has_wall:
                    x_value = x0 + wall_index * cell_size
                    self.canvas.create_line(
                        x_value,
                        canvas_top,
                        x_value,
                        canvas_bottom,
                        fill=wall_color,
                        width=wall_width,
                    )

    def handle_action(self, action: str) -> None:
        if action == "escape":
            self.close()
        elif action == "space":
            self.paused = not self.paused
        elif action == "reset":
            self.maze.reset()
            self.update_caption()
        elif action == "bonus":
            self.maze.bonus_mode = not self.maze.bonus_mode
            self.maze.extra_wall_chance = 0.05 if self.maze.bonus_mode else 0.0
            self.maze.reset()
            self.update_caption()

    def tick(self) -> None:
        if not self.running:
            return
        self.update_simulation()
        self.draw()
        self.root.after(16, self.tick)

    def run(self) -> None:
        self.tick()
        self.root.mainloop()


def validate_args(args: argparse.Namespace) -> None:
    if args.rows < 2 or args.cols < 2:
        raise SystemExit("rows and cols must both be at least 2")
    if args.generation_steps_per_frame < 1 or args.solve_steps_per_frame < 1:
        raise SystemExit("steps per frame must both be at least 1")
    if args.bonus and (args.rows < 3 or args.cols < 3):
        raise SystemExit("bonus mode needs at least 3 rows and 3 cols for interior start/end cells")


def run_headless(args: argparse.Namespace) -> None:
    maze = Maze(args.rows, args.cols, args.extra_wall_chance, args.seed, bonus_mode=args.bonus)

    while not maze.generation_complete:
        maze.generate_step()

    while not maze.solver_complete:
        maze.solve_step()

    print(f"Generated a {maze.rows}x{maze.cols} maze.")
    print(f"Mode: {'bonus' if maze.bonus_mode else 'proper'}")
    print(f"Start cell: {maze.start_cell}")
    print(f"End cell: {maze.end_cell}")
    print(f"DFS passages carved: {maze.stats.carved_passages}")
    print(f"Extra cycle openings: {maze.stats.extra_openings}")
    print(f"Generation steps: {maze.stats.generation_steps}")
    print(f"Solve steps: {maze.stats.solve_steps}")
    print(f"Solution path length: {len(maze.solution_path)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and solve a maze with a PyOpenGL animation.")
    parser.add_argument("--rows", type=int, default=18, help="Number of maze rows.")
    parser.add_argument("--cols", type=int, default=28, help="Number of maze columns.")
    parser.add_argument("--width", type=int, default=1280, help="Window width in pixels.")
    parser.add_argument("--height", type=int, default=820, help="Window height in pixels.")
    parser.add_argument(
        "--generation-steps-per-frame",
        type=int,
        default=10,
        help="How many generation steps to animate on each frame.",
    )
    parser.add_argument(
        "--solve-steps-per-frame",
        type=int,
        default=4,
        help="How many solving steps to animate on each frame.",
    )
    parser.add_argument(
        "--extra-wall-chance",
        type=float,
        default=0.0,
        help="Chance of removing an extra wall after the proper maze is built; try 0.05 for the bonus challenge.",
    )
    parser.add_argument(
        "--bonus",
        action="store_true",
        help="Place the start and end in the interior and add cycle openings for the addendum challenge.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducible mazes.")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the generation and solver without opening a window; useful for quick verification.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.bonus and args.extra_wall_chance == 0.0:
        args.extra_wall_chance = 0.05
    validate_args(args)

    if args.headless:
        run_headless(args)
        return

    maze = Maze(args.rows, args.cols, args.extra_wall_chance, args.seed, bonus_mode=args.bonus)
    if GRAPHICS_READY:
        window = MazeWindow(
            maze=maze,
            width=args.width,
            height=args.height,
            generation_steps_per_frame=args.generation_steps_per_frame,
            solve_steps_per_frame=args.solve_steps_per_frame,
        )
    else:
        window = TkMazeWindow(
            maze=maze,
            width=args.width,
            height=args.height,
            generation_steps_per_frame=args.generation_steps_per_frame,
            solve_steps_per_frame=args.solve_steps_per_frame,
        )
    window.run()


if __name__ == "__main__":
    main()
