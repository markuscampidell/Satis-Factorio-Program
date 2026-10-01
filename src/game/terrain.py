# game.terrain
import math
from functools import lru_cache

from game.chunk import CHUNK_SIZE

EMPTY_TILE = 0

# Ore patches are placed via a "local priority maximum" scatter, not on a
# jittered grid - a lattice-with-jitter (the previous approach) always
# looks like a grid from far enough away, no matter how much jitter you
# add, because the underlying candidate positions are still tied to a
# regular lattice. Instead: cover the world with a dense field of
# candidate points (one per CANDIDATE_CELL_TILES cell, positioned anywhere
# within it - not just wobbled slightly off center), give each one a
# random priority, and a candidate only actually becomes a patch if no
# *other* candidate within MIN_PATCH_SEPARATION_CHUNKS of it has a higher
# priority. This is what actually guarantees the minimum spacing (if two
# accepted patches were closer than that, each would be within the other's
# checked radius, and the lower-priority one would have lost) while
# producing an organic, non-gridded scatter - accepted points end up
# wherever the priorities happen to "win" locally, not on a fixed lattice.

CANDIDATE_CELL_TILES = CHUNK_SIZE  # how fine the candidate field is - smaller = more organic variety but slower generation

MIN_PATCH_SEPARATION_CHUNKS = 2    # the hard "never touch" rule - lower this to allow patches closer together

# A patch's max possible reach from its center (radius + edge wobble) has
# to stay well under half MIN_PATCH_SEPARATION_CHUNKS (in tiles) so that
# even two accepted patches right at that minimum distance never actually
# touch - "far away from each other" isn't just center-to-center distance,
# their actual edges need a real gap too.
PATCH_BASE_RADIUS_TILES = 8       # average patch radius, in tiles - patch is roughly 2x this across
PATCH_RADIUS_JITTER_TILES = 5      # how much radius varies patch-to-patch
PATCH_EDGE_NOISE_SCALE = 8         # tiles per noise lattice cell for the wobbly edge
PATCH_EDGE_NOISE_STRENGTH = 4      # tiles, how far the edge noise can push the boundary

# Every accepted candidate produces exactly one ore patch (there's no
# "empty" candidate) - the weights below are the relative odds of each
# type, so across many patches roughly 40% of them are iron, 30% copper,
# 10% coal, 20% limestone.
_ORE_WEIGHTS = [
    ("iron_ore", 0.40),
    ("copper_ore", 0.30),
    ("coal", 0.10),
    ("limestone", 0.20),
]
_ITEM_TO_TILE_TYPE = {"iron_ore": 1, "copper_ore": 2, "coal": 3, "limestone": 4}
ORE_TILE_TYPES = {tile_type: item_id for item_id, tile_type in _ITEM_TO_TILE_TYPE.items()}

_SALT_JITTER_X = 101
_SALT_JITTER_Y = 103
_SALT_TYPE = 107
_SALT_RADIUS = 109
_SALT_EDGE = 113
_SALT_PRIORITY = 127


def _hash01(seed, ix, iy, salt):
    """Deterministic pseudo-random float in [0,1) from integer inputs only -
    not `hash()`/`random`, since neither is guaranteed stable across
    processes/Python versions for this. Cheap integer mixing hash."""
    n = (ix * 374761393 + iy * 668265263 + seed * 2147483647 + salt * 1000003) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n ^= n >> 16
    return n / 0xFFFFFFFF


def _smoothstep(t):
    return t * t * (3 - 2 * t)


def _value_noise(seed, x, y, salt, scale):
    """Bilinear-interpolated value noise: hash the 4 lattice corners around
    (x, y) at `scale` tiles apart, smoothstep-interpolate between them -
    used only for the wobbly, non-circular edge of a patch here."""
    lx, ly = x / scale, y / scale
    x0, y0 = int(lx // 1), int(ly // 1)
    tx, ty = _smoothstep(lx - x0), _smoothstep(ly - y0)
    v00 = _hash01(seed, x0, y0, salt)
    v10 = _hash01(seed, x0 + 1, y0, salt)
    v01 = _hash01(seed, x0, y0 + 1, salt)
    v11 = _hash01(seed, x0 + 1, y0 + 1, salt)
    top = v00 + (v10 - v00) * tx
    bottom = v01 + (v11 - v01) * tx
    return top + (bottom - top) * ty


def _candidate_position(seed, ccx, ccy):
    """Where candidate (ccx, ccy)'s point sits - anywhere within its own
    cell (not just wobbled slightly off center), which is what keeps the
    result from looking like a grid."""
    base_x = ccx * CANDIDATE_CELL_TILES
    base_y = ccy * CANDIDATE_CELL_TILES
    jx = _hash01(seed, ccx, ccy, _SALT_JITTER_X) * CANDIDATE_CELL_TILES
    jy = _hash01(seed, ccx, ccy, _SALT_JITTER_Y) * CANDIDATE_CELL_TILES
    return base_x + jx, base_y + jy


def _candidate_key(seed, ccx, ccy):
    """(priority, cell coords) - compared lexicographically so "higher
    priority wins" has no possibility of an exact tie (two different
    candidates can share a priority in principle, however unlikely, but
    never the same coordinates)."""
    return _hash01(seed, ccx, ccy, _SALT_PRIORITY), (ccx, ccy)


@lru_cache(maxsize=300_000)
def _is_patch_center(seed, ccx, ccy):
    """True if this candidate "wins" - no other candidate within
    MIN_PATCH_SEPARATION_CHUNKS of it has a higher priority. Any two
    accepted candidates are therefore guaranteed to be at least that far
    apart: if they were closer, each would be inside the other's search
    radius, and the lower-priority one would lose."""
    cx, cy = _candidate_position(seed, ccx, ccy)
    my_key = _candidate_key(seed, ccx, ccy)

    min_sep_tiles = MIN_PATCH_SEPARATION_CHUNKS * CHUNK_SIZE
    reach_cells = int(min_sep_tiles // CANDIDATE_CELL_TILES) + 2

    for dcy in range(-reach_cells, reach_cells + 1):
        for dcx in range(-reach_cells, reach_cells + 1):
            if dcx == 0 and dcy == 0:
                continue
            ocx, ocy = ccx + dcx, ccy + dcy
            ox, oy = _candidate_position(seed, ocx, ocy)
            if math.hypot(cx - ox, cy - oy) < min_sep_tiles and _candidate_key(seed, ocx, ocy) > my_key:
                return False

    return True


def _patch_radius(seed, ccx, ccy):
    return PATCH_BASE_RADIUS_TILES + (_hash01(seed, ccx, ccy, _SALT_RADIUS) - 0.5) * 2 * PATCH_RADIUS_JITTER_TILES


def _patch_tile_type(seed, ccx, ccy):
    """Which ore this patch is, chosen by the weighted odds in
    _ORE_WEIGHTS from one deterministic roll per candidate."""
    roll = _hash01(seed, ccx, ccy, _SALT_TYPE)
    cumulative = 0.0
    for item_id, weight in _ORE_WEIGHTS:
        cumulative += weight
        if roll < cumulative:
            return _ITEM_TO_TILE_TYPE[item_id]
    return _ITEM_TO_TILE_TYPE[_ORE_WEIGHTS[-1][0]]  # float-rounding fallback


def tile_type_at(seed, tile_x, tile_y):
    """The tile-type index at one absolute tile - a pure function of
    (seed, x, y), so it's callable from anywhere with no world state (the
    lru_cache above is purely a perf nicety, not required for correctness).
    Checks every candidate cell whose patch could possibly reach this tile,
    and returns whichever *accepted* one actually does, nearest-wins if
    more than one somehow would (shouldn't happen given the radius/spacing
    margins above, but stays well-defined either way)."""
    ccx0 = tile_x // CANDIDATE_CELL_TILES
    ccy0 = tile_y // CANDIDATE_CELL_TILES

    max_reach = PATCH_BASE_RADIUS_TILES + PATCH_RADIUS_JITTER_TILES + PATCH_EDGE_NOISE_STRENGTH
    reach_cells = int(max_reach // CANDIDATE_CELL_TILES) + 2

    # Position-only, not per-candidate, so it's computed once per tile
    # rather than once per candidate checked.
    wobble = (_value_noise(seed, tile_x, tile_y, _SALT_EDGE, PATCH_EDGE_NOISE_SCALE) - 0.5) * 2 * PATCH_EDGE_NOISE_STRENGTH

    best_type, best_dist = EMPTY_TILE, None
    for dcy in range(-reach_cells, reach_cells + 1):
        for dcx in range(-reach_cells, reach_cells + 1):
            ccx, ccy = ccx0 + dcx, ccy0 + dcy
            if not _is_patch_center(seed, ccx, ccy):
                continue

            cx, cy = _candidate_position(seed, ccx, ccy)
            dist = math.hypot(tile_x - cx, tile_y - cy)
            radius = _patch_radius(seed, ccx, ccy) + wobble
            if dist <= radius and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_type = _patch_tile_type(seed, ccx, ccy)

    return best_type


def generate_chunk_tiles(seed, cx, cy):
    """CHUNK_SIZE x CHUNK_SIZE grid of tile types for chunk (cx, cy)."""
    base_x, base_y = cx * CHUNK_SIZE, cy * CHUNK_SIZE
    return [
        [tile_type_at(seed, base_x + lx, base_y + ly) for lx in range(CHUNK_SIZE)]
        for ly in range(CHUNK_SIZE)
    ]
