"""
The 3D animation of the progress window: a rotating voxel volume that fills with the model from the bottom up.

The model is simply its atoms binned into a cube of GRID x GRID x GRID voxels; they are scaled to fit and not
transformed in any other way, so this is not what the mode will build. It is drawn by numpy into an image rather
than with OpenGL: PDB2MC needs no extra library for it, and it works on any computer, including over remote
desktop. All voxels of a frame have the same orientation, so one cube is worked out per frame and then stamped
at every voxel, furthest first.
"""
import math

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from PDB2MC import pdb_manipulation as pdbm
from PDB2MC.build import chain_numbers, valid_chain_blocks
from PDB2MC.variables import hex_dict

# Voxels along each edge of the volume
GRID = 32
FRAME_MS = 33
# Degrees per second around the vertical axis
SPIN_SPEED = 45
# Degrees the view looks down at the volume
TILT = 28
# Share of the gap to the real progress closed each frame, so the model fills smoothly between reports
FILL_EASING = 0.12

BACKGROUND = "#f4f6f8"
FRAME_COLOR = QtGui.QColor(120, 132, 148)
LEVEL_COLOR = QtGui.QColor(50, 120, 220, 170)
DEFAULT_BLOCK_COLOR = "#8a8f98"
# Darkest value of a colour channel: black blocks would otherwise lose every face and edge in the shadows
COLOR_FLOOR = 62

# Brightness of the three visible faces of a cube, top first; edges are drawn darker so voxels stay distinct
FACE_LIGHT = {1: 1.0, 0: 0.78, 2: 0.6}
EDGE_LIGHT = 0.82
EDGE_WIDTH = 0.1

_FACE_NEIGHBOURS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def block_rgb(block):
    """(r, g, b) of a Minecraft block, lifted a little so even black voxels show their shading."""
    color = hex_dict.get(block, DEFAULT_BLOCK_COLOR).lstrip("#")
    return tuple(int(COLOR_FLOOR + int(color[i:i + 2], 16) * (255 - COLOR_FLOOR) / 255) for i in (0, 2, 4))


def atom_blocks(df, config):
    """The block each atom would most nearly get with the window's settings, for colouring the voxels."""
    atoms = config.get('atoms', {})
    other = atoms.get('other_atom', 'pink_concrete')
    if config.get('amino_acids'):
        return df['residue'].map(config['amino_acids']).fillna(other).to_numpy(dtype=object)
    if config.get('by_chain'):
        blocks = valid_chain_blocks(config.get('chain_blocks'))
        numbers = chain_numbers(df['chain'], len(blocks))
        return df['chain'].map(lambda chain: blocks[numbers[chain] - 1]).to_numpy(dtype=object)
    elements = df['element'].fillna('').astype(str).str.strip().str.upper()
    return elements.map(lambda element: atoms.get(element, other)).to_numpy(dtype=object)


def model_voxels(structure, config=None, grid=GRID):
    """
    The atoms of a structure as voxels: (positions (n, 3) with values 0..grid-1 and the second column pointing
    up, colours (n, 3) as uint8). Waters are left out, and so are other molecules when the model hides them.
    """
    config = config or {}
    df = pdbm.structure_to_df(structure)
    if df.empty:
        return np.zeros((0, 3), dtype=int), np.zeros((0, 3), dtype=np.uint8)
    df = df[~df['residue'].isin(("HOH", "WAT", "DOD"))]
    if not config.get('show_hetatm', True):
        df = df[df['row'] == 'ATOM']
    if df.empty:
        return np.zeros((0, 3), dtype=int), np.zeros((0, 3), dtype=np.uint8)
    xyz = df[['X', 'Y', 'Z']].to_numpy(dtype=float)
    low, high = xyz.min(axis=0), xyz.max(axis=0)
    fit = (grid - 1) / max(float((high - low).max()), 1e-6)
    # Centred in the volume, except for height: the model stands on its floor
    offset = (grid - 1 - (high - low) * fit) / 2
    offset[1] = 0
    positions = np.rint((xyz - low) * fit + offset).astype(int)
    keys = positions[:, 0] * grid * grid + positions[:, 1] * grid + positions[:, 2]
    _, first = np.unique(keys, return_index=True)
    blocks = atom_blocks(df, config)[first]
    colours = {block: block_rgb(block) for block in set(blocks)}
    return positions[first], np.array([colours[block] for block in blocks], dtype=np.uint8).reshape(-1, 3)


def rotation(angle, tilt=TILT):
    """View matrix for a turn of `angle` degrees around the vertical axis, seen from `tilt` degrees above."""
    spin, down = math.radians(angle), math.radians(tilt)
    around = np.array([[math.cos(spin), 0, math.sin(spin)], [0, 1, 0], [-math.sin(spin), 0, math.cos(spin)]])
    look = np.array([[1, 0, 0], [0, math.cos(down), -math.sin(down)], [0, math.sin(down), math.cos(down)]])
    return look @ around


def cube_stamp(view, size):
    """
    Pixels of one voxel of edge `size` seen through `view`: arrays (dy, dx, shade), shade being an index into
    the brightness table made by stamp_light(). Faces further from the viewer never overlap the near ones.
    """
    half = int(math.ceil(size * 1.8)) + 1
    ys, xs = np.mgrid[-half:half + 1, -half:half + 1]
    # Sample at pixel centres; screen y points down, view y up
    points = np.stack([xs.ravel() + 0.0, -(ys.ravel() + 0.0)], axis=1) / size
    faces = np.full(len(points), -1)
    edges = np.zeros(len(points), dtype=bool)
    for axis in (1, 0, 2):
        # The visible face on this axis is the one whose outward normal points at the viewer
        toward = 1.0 if view[2, axis] >= 0 else -1.0
        centre = view[:2, axis] * toward * 0.5
        u_axis, v_axis = [a for a in (0, 1, 2) if a != axis]
        basis = np.array([view[:2, u_axis], view[:2, v_axis]]).T
        if abs(np.linalg.det(basis)) < 1e-3:
            continue
        uv = np.linalg.solve(basis, (points - centre).T).T
        inside = (np.abs(uv) <= 0.5).all(axis=1) & (faces < 0)
        faces[inside] = axis
        edges[inside] = (np.abs(uv[inside]) >= 0.5 - EDGE_WIDTH).any(axis=1)
    keep = faces >= 0
    shade = faces[keep] * 2 + edges[keep]
    return ys.ravel()[keep], xs.ravel()[keep], shade


def stamp_light():
    """Brightness for each shade index of cube_stamp."""
    light = np.zeros(6)
    for axis, value in FACE_LIGHT.items():
        light[axis * 2] = value
        light[axis * 2 + 1] = value * EDGE_LIGHT
    return light


def visible_voxels(positions, level, grid=GRID):
    """Mask of the voxels at or below `level` (a height in voxels) that have an uncovered face."""
    filled = positions[:, 1] <= level
    occupied = np.zeros((grid + 2, grid + 2, grid + 2), dtype=bool)
    shown = positions[filled] + 1
    occupied[shown[:, 0], shown[:, 1], shown[:, 2]] = True
    local = positions + 1
    covered = np.ones(len(positions), dtype=bool)
    for dx, dy, dz in _FACE_NEIGHBOURS:
        covered &= occupied[local[:, 0] + dx, local[:, 1] + dy, local[:, 2] + dz]
    return filled & ~covered


def render(positions, colours, angle, level, width, height, grid=GRID):
    """
    One frame as an ARGB uint32 array (height, width), transparent around the model. `level` is the height
    filled so far, in voxels.
    """
    frame = np.zeros((height, width), dtype=np.uint32)
    if not len(positions):
        return frame
    mask = visible_voxels(positions, level, grid)
    if not mask.any():
        return frame
    view = rotation(angle)
    size = voxel_size(width, height, grid)
    centred = positions[mask] - (grid - 1) / 2
    rotated = centred @ view.T
    order = np.argsort(rotated[:, 2])
    rotated = rotated[order]
    xs = np.rint(width / 2 + rotated[:, 0] * size).astype(int)
    ys = np.rint(height / 2 - rotated[:, 1] * size).astype(int)

    # Per voxel, the colour of each shade as one packed number
    light = stamp_light()
    rgb = colours[mask][order].astype(float)
    shades = rgb[:, None, :] * light[None, :, None]
    packed = (0xFF000000 + (shades[..., 0].astype(np.uint32) << 16) + (shades[..., 1].astype(np.uint32) << 8)
              + shades[..., 2].astype(np.uint32)).astype(np.uint32)

    dy, dx, shade = cube_stamp(view, size)
    pixel_y = (ys[:, None] + dy[None, :]).ravel()
    pixel_x = (xs[:, None] + dx[None, :]).ravel()
    values = packed[:, shade].ravel()
    inside = (pixel_y >= 0) & (pixel_y < height) & (pixel_x >= 0) & (pixel_x < width)
    # Later voxels are nearer and overwrite earlier ones
    frame[pixel_y[inside], pixel_x[inside]] = values[inside]
    return frame


def voxel_size(width, height, grid=GRID):
    """Pixels per voxel so that the volume fits at any angle (with the tilt it spans about 1.55 edges)."""
    return min(width, height) / (grid * 1.62)


class VoxelVolume(QtWidgets.QWidget):
    """Continuously rotating voxel volume, filled with the model up to set_progress()."""

    def __init__(self, parent=None, size=320):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.positions = np.zeros((0, 3), dtype=int)
        self.colours = np.zeros((0, 3), dtype=np.uint8)
        self.angle = 30.0
        self.target = 0.0
        self.shown = 0.0
        self._clock = QtCore.QElapsedTimer()
        self._clock.start()
        self._last = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.advance)
        self._timer.start(FRAME_MS)

    def set_model(self, positions, colours):
        self.positions, self.colours = positions, colours
        self.update()

    def set_progress(self, value):
        self.target = max(0.0, min(1.0, value / 100))

    def stop(self):
        self._timer.stop()

    def advance(self):
        elapsed = self._clock.elapsed()
        self.angle = (self.angle + SPIN_SPEED * (elapsed - self._last) / 1000) % 360
        self._last = elapsed
        self.shown += (self.target - self.shown) * FILL_EASING
        if self.target - self.shown < 0.002:
            self.shown = self.target
        self.update()

    def level(self):
        """Height of the fill in voxels. The model's own height sets it, so the top arrives at 100%."""
        if not len(self.positions):
            return -1
        top = int(self.positions[:, 1].max())
        return top if self.shown >= 1 else int(self.shown * (top + 1)) - 1

    def _corners(self, height):
        """Screen positions of the four corners of the volume at a height from 0 (floor) to 1 (top)."""
        size = voxel_size(self.width(), self.height())
        half = GRID / 2
        corners = np.array([(-half, height * GRID - half, -half), (half, height * GRID - half, -half),
                            (half, height * GRID - half, half), (-half, height * GRID - half, half)])
        rotated = corners @ rotation(self.angle).T
        return [QtCore.QPointF(self.width() / 2 + x * size, self.height() / 2 - y * size)
                for x, y, _ in rotated], rotated[:, 2]

    def _draw_edges(self, painter, front):
        """The edges of the volume behind the model (front=False) or in front of it (front=True)."""
        floor, floor_depth = self._corners(0)
        top, top_depth = self._corners(1)
        pen = QtGui.QPen(FRAME_COLOR, 1.4 if front else 1.0)
        painter.setPen(pen)
        for i in range(4):
            j = (i + 1) % 4
            for points, depth in ((floor, floor_depth), (top, top_depth)):
                if (depth[i] + depth[j] > 0) == front:
                    painter.drawLine(points[i], points[j])
            if ((floor_depth[i] + top_depth[i]) > 0) == front:
                painter.drawLine(floor[i], top[i])

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(BACKGROUND))
        self._draw_edges(painter, front=False)
        level = self.level()
        frame = render(self.positions, self.colours, self.angle, level, self.width(), self.height())
        image = QtGui.QImage(frame.data, self.width(), self.height(), self.width() * 4,
                             QtGui.QImage.Format.Format_ARGB32)
        painter.drawImage(0, 0, image)
        if 0 < self.shown < 1 and len(self.positions):
            top = int(self.positions[:, 1].max()) + 1
            corners, _ = self._corners(self.shown * top / GRID)
            painter.setPen(QtGui.QPen(LEVEL_COLOR, 1.6))
            painter.drawPolygon(QtGui.QPolygonF(corners))
        self._draw_edges(painter, front=True)
        painter.end()
