# game.chunk
CHUNK_SIZE = 32  # tiles per chunk edge


def chunk_coords(tile_pos):
    """(tx, ty) absolute tile -> (cx, cy) chunk. Python's // floors toward
    -inf for negative operands already, so negative tiles need no special
    casing (tile -1 -> chunk -1, covering tiles -32..-1)."""
    tx, ty = tile_pos
    return tx // CHUNK_SIZE, ty // CHUNK_SIZE


class Chunk:
    """One 32x32-tile region - a spatial bucket of whatever machines/belts
    overlap it, for camera-culled rendering and (later) per-chunk terrain/ore
    generation. Never gates simulation - machines/belts inside keep updating
    via World's flat lists regardless of chunk visibility."""

    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.machines = set()
        self.belt_segments = set()

        # Terrain, both lazily populated the first time something actually
        # needs them - see World._ensure_chunk_terrain and
        # WorldRenderer._draw_terrain. `tiles` is plain per-tile data (a
        # CHUNK_SIZE x CHUNK_SIZE grid of tile-type ints); `terrain_surface`
        # is a cached pygame.Surface built from it purely for rendering, so
        # it doesn't get rebuilt every frame.
        self.tiles = None
        self.terrain_surface = None

    def is_empty(self):
        return not self.machines and not self.belt_segments
