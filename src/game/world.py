# game.world
from game.chunk import Chunk, chunk_coords

class World:
    """Keeps track of every machine and belt that's been built, and where
    each one sits on the grid."""

    def __init__(self, player, cell_size):
        self.player = player
        self.cell_size = cell_size

        self.machines = []
        self.belt_segments = []

        self.machine_map = {}
        self.belt_map = {}

        # Additive spatial index on top of the flat lists/maps above, for
        # camera-culled rendering (and later, per-chunk terrain/ore
        # generation) - never a substitute for machine_map/belt_map, which
        # stay global so belt/machine connectivity across a chunk boundary
        # needs no special-casing anywhere. Never gates simulation either -
        # update_all_belts()/machine.update() keep iterating the flat lists
        # regardless of which chunks exist or are "visible".
        self.chunks = {}

    def clear(self):
        """Empties the world of all machines/belts, for a fresh load/new game."""
        self.machines.clear()
        self.belt_segments.clear()
        self.machine_map.clear()
        self.belt_map.clear()
        self.chunks.clear()

    def _get_or_create_chunk(self, chunk_pos):
        chunk = self.chunks.get(chunk_pos)
        if chunk is None:
            chunk = Chunk(*chunk_pos)
            self.chunks[chunk_pos] = chunk
        return chunk

    def _chunks_for_cells(self, cells):
        """Distinct chunk coords touched by a set of tile cells - a
        multi-tile machine straddling a chunk boundary touches more than
        one."""
        return {chunk_coords(cell) for cell in cells}

    def add_machine(self, machine):
        """Add a machine and map all its occupied cells."""
        self.machines.append(machine)
        for cell in machine.occupied_cells:
            self.machine_map[cell] = machine
        for chunk_pos in self._chunks_for_cells(machine.occupied_cells):
            self._get_or_create_chunk(chunk_pos).machines.add(machine)

    def remove_machine(self, machine):
        """Remove machine from world and lookup map."""
        if machine in self.machines:
            self.machines.remove(machine)
        for cell in getattr(machine, "occupied_cells", []):
            self.machine_map.pop(cell, None)
        for chunk_pos in self._chunks_for_cells(getattr(machine, "occupied_cells", [])):
            chunk = self.chunks.get(chunk_pos)
            if chunk is not None:
                chunk.machines.discard(machine)

    def get_machine_at(self, grid_pos):
        """Return the machine at a given grid position, if any."""
        return self.machine_map.get(grid_pos)



    def add_belt_segment(self, seg):
        """Add a belt segment and put it in the lookup map."""
        self.belt_segments.append(seg)
        self.belt_map[seg.grid_pos] = seg
        self._get_or_create_chunk(chunk_coords(seg.grid_pos)).belt_segments.add(seg)

    def remove_belt_segment(self, seg):
        """Remove a belt segment from the world and the lookup map."""
        if seg in self.belt_segments:
            self.belt_segments.remove(seg)
        self.belt_map.pop(seg.grid_pos, None)
        chunk = self.chunks.get(chunk_coords(seg.grid_pos))
        if chunk is not None:
            chunk.belt_segments.discard(seg)

    def get_belt_segment_at(self, world_x, world_y):
        tile = self.snap_to_tile(world_x, world_y)
        return self.belt_map.get(tile)

    def gather_occupants(self, cells):
        """Return all belt segments and machines found in the given cells.
        Machines that cover multiple cells are only included once."""
        segments = [self.belt_map[cell] for cell in cells if cell in self.belt_map]
        machines = list({
            id(machine): machine
            for cell in cells
            for machine in [self.machine_map.get(cell)]
            if machine is not None
        }.values())
        return segments, machines

    def chunks_in_tile_rect(self, left, top, right, bottom):
        """Yields every existing Chunk overlapping the given tile-coordinate
        rect (right/bottom exclusive - same convention world_renderer.py
        already uses for its camera bounds). Doesn't create chunks for empty
        regions - only yields ones something's actually been placed in."""
        cx1, cy1 = chunk_coords((left, top))
        cx2, cy2 = chunk_coords((right - 1, bottom - 1))
        for cy in range(cy1, cy2 + 1):
            for cx in range(cx1, cx2 + 1):
                chunk = self.chunks.get((cx, cy))
                if chunk is not None:
                    yield chunk

    def machines_in_tile_rect(self, left, top, right, bottom):
        """Deduped machines whose chunk(s) overlap the rect. Chunk-grained,
        not tile-grained - can include machines whose actual footprint lies
        just outside the exact rect; callers that need pixel-precise culling
        should keep doing their own precise check on top of this."""
        seen = set()
        result = []
        for chunk in self.chunks_in_tile_rect(left, top, right, bottom):
            for machine in chunk.machines:
                if machine not in seen:
                    seen.add(machine)
                    result.append(machine)
        return result

    def belt_segments_in_tile_rect(self, left, top, right, bottom):
        """Belts whose chunk overlaps the rect - a belt is always 1x1, so it
        only ever lives in exactly one chunk and needs no dedupe."""
        for chunk in self.chunks_in_tile_rect(left, top, right, bottom):
            yield from chunk.belt_segments

    def machines_near(self, rect, padding_tiles=1):
        """Candidate machines for collision against `rect` (a pygame.Rect in
        pixel space) - a chunk-scoped stand-in for "every machine in the
        world" that comfortably covers the small distance a player's own
        collision check ever actually needs (the biggest machine is 3x3
        tiles), without scanning machines far away."""
        left = rect.left // self.cell_size - padding_tiles
        top = rect.top // self.cell_size - padding_tiles
        right = (rect.right - 1) // self.cell_size + 1 + padding_tiles
        bottom = (rect.bottom - 1) // self.cell_size + 1 + padding_tiles
        return self.machines_in_tile_rect(left, top, right, bottom)

    def snap_to_tile(self, x, y):
        """Convert pixel coordinates to tile indices (integers)."""
        return int(x // self.cell_size), int(y // self.cell_size)

    def is_cell_blocked(self, grid_pos):
        """Check if a cell is occupied by a machine or belt."""
        return grid_pos in self.machine_map or grid_pos in self.belt_map

    def is_blocked_by_player(self, grid_pos):
        """Check if the given grid cell is currently occupied by the player."""
        left = int(self.player.rect.left // self.cell_size)
        right = int((self.player.rect.right - 1) // self.cell_size)
        top = int(self.player.rect.top // self.cell_size)
        bottom = int((self.player.rect.bottom - 1) // self.cell_size)

        px, py = grid_pos

        # Return True if the grid_pos is inside the player's covered cells
        return left <= px <= right and top <= py <= bottom
