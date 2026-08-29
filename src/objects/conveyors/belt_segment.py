# objects.conveyors.belt_segment
import pygame as py
from game.grid import Grid
from core.vector2 import Vector2
from objects.item_filter import ItemFilter

class BeltSegment:
    def __init__(self, grid_pos, direction: Vector2, incoming_directions: list, belt_type="basic"):
        self.grid_pos = grid_pos  # tile coordinates (x, y)
        self.direction = direction or Vector2(1, 0)
        self.incoming_directions = incoming_directions
        self.belt_type = belt_type

        # For drawing only
        self.rect = py.Rect(grid_pos[0] * Grid.CELL_SIZE, grid_pos[1] * Grid.CELL_SIZE, Grid.CELL_SIZE, Grid.CELL_SIZE)

        # Items on this segment
        self.item = None
        self.current_incoming_direction = None
        self.item_progress = 0.0
        self.input_requests = []
        self.current_input_index = 0

        self.items_per_minute = self._get_items_per_minute_for_type()
        self.speed = (self.items_per_minute / 60)  # tiles per second

        # What's allowed to enter this tile - from another belt, a
        # machine/storage push, or a splitter. Doesn't affect what this
        # segment pushes onward once an item is already on it.
        self.filter = ItemFilter()

    def accepts_item(self, item_id):
        return self.filter.accepts(item_id)

    def advance(self, dt):
        """Progress-only tick - no transfer decisions. Split out from the
        old update() so a full frame can run advance() once, then attempt
        transfers in a cascading loop (see update_all()) instead of just
        once, which is what let a packed line's items only ever shuffle
        forward one tile per *frame* instead of draining at real speed."""
        if self.item:
            self.item_progress += self.speed * dt

    def attempt_transfer(self, belt_map, machine_map):
        """If this segment's item has finished crossing the tile, try to
        hand it off - request the next belt (arbitrated fairly, possibly
        across several belts feeding one merge point, by
        resolve_input_requests) or insert straight into a machine. Returns
        True only for a machine-insert, which completes immediately;
        a belt-to-belt hand-off isn't final until resolve_input_requests
        runs, so it's reported as a change there instead."""
        if not self.item or self.item_progress < 1.0:
            return False

        next_pos = (self.grid_pos[0] + self.direction.x,
                    self.grid_pos[1] + self.direction.y)

        next_segment = belt_map.get(next_pos)
        if next_segment:
            # Deliberately NOT clamped here - if this request is granted,
            # resolve_input_requests carries the overshoot (whatever's past
            # 1.0) onto the receiving segment instead of discarding it, so
            # a never-blocked item doesn't lose a sliver of progress on
            # every single hop. If it's rejected instead, update_all()'s
            # final pass clamps it back to 1.0 once the frame's cascade is
            # done, so it never renders past the tile it's actually on.
            next_segment.request_item(self, self.item, self.direction)
            return False

        machine = machine_map.get(next_pos)
        if machine and self._try_insert_into_machine(machine, self.grid_pos):
            return True

        # Stay at the end of the belt until something accepts the item.
        self.item_progress = 1.0
        return False

    def refund_item_on_segment(self, player_inventory):
        if self.item:
            player_inventory.try_add_items(self.item.item_id, 1)
            self._clear_item()


    def _clear_item(self):
        self.item = None
        self.item_progress = 0.0
        self.current_incoming_direction = None


    def request_item(self, source_belt, item, incoming_direction):
        # Don't accept an item from an opposing belt.
        if incoming_direction == -self.direction:
            return False

        if not self.accepts_item(item.item_id):
            return False

        if self.item is not None:
            return False

        for request in self.input_requests:
            if request[0] is source_belt:
                return False

        self.input_requests.append((source_belt, item, incoming_direction))

        return True


    def resolve_input_requests(self):
        if self.item is not None:
            self.input_requests.clear()
            return False

        if not self.input_requests:
            return False

        chosen = None

        if len(self.incoming_directions) > 1:
            priority = self.incoming_directions[self.current_input_index]

            for request in self.input_requests:
                if request[2] == priority:
                    chosen = request
                    break

        if chosen is None:
            chosen = self.input_requests[0]

        source, item, direction = chosen

        self.item = item
        # Carry over however far past 1.0 the source had already advanced
        # this frame, instead of hard-resetting to 0.0 - a freely-flowing
        # (never-blocked) item typically overshoots the 1.0 threshold by a
        # few percent of a tile before the frame that notices it, and
        # discarding that overshoot on every single tile crossing adds up
        # to a real, systematic throughput deficit (worse on faster belts,
        # since a fixed frame time is a bigger fraction of a shorter
        # tile-crossing). A blocked source is already clamped to exactly
        # 1.0 by attempt_transfer, so this is 0.0 in that case anyway -
        # this only ever adds precision, never changes blocked behavior.
        self.item_progress = max(0.0, source.item_progress - 1.0)

        self.current_incoming_direction = direction

        source._clear_item()

        if len(self.incoming_directions) > 1:
            index = self.incoming_directions.index(direction)
            self.current_input_index = (
                index + 1
            ) % len(self.incoming_directions)

        self.input_requests.clear()
        return True


    def _try_insert_into_machine(self, machine, source_grid_pos):
        added = machine.try_receive_item(self.item, source_grid_pos, direction=self.direction, source_speed=self.speed)

        if added:
            self._clear_item()

        return added


    def _get_items_per_minute_for_type(self):
        if self.belt_type == "basic":
            return 120
        elif self.belt_type == "fast":
            return 240
        elif self.belt_type == "express":
            return 480
        else:
            return 120


def update_all(belt_segments, belt_map, machine_map, dt):
    """Advances every belt segment's item by dt, then resolves hand-offs
    in a cascading loop - repeating attempt_transfer/resolve_input_requests
    until a full pass makes no more progress, instead of just once. A
    single pass only lets each item move at most one link (a freshly
    emptied tile isn't noticed by the segment behind it until the next
    pass), so without this a fully packed line only drains one tile per
    *frame* rather than at the belt's actual speed - this lets a whole
    backed-up line shift as far as it can within the same frame."""
    for segment in belt_segments:
        segment.advance(dt)

    for _ in range(len(belt_segments) + 1):
        changed = False

        for segment in belt_segments:
            if segment.attempt_transfer(belt_map, machine_map):
                changed = True

        for segment in belt_segments:
            if segment.resolve_input_requests():
                changed = True

        if not changed:
            break

    # Anything still holding an item past 1.0 at this point tried every
    # request this frame's cascade allowed and is genuinely blocked for
    # the rest of it - pin it to exactly 1.0 so it doesn't render past its
    # tile or keep accumulating overshoot next frame while it waits.
    for segment in belt_segments:
        if segment.item and segment.item_progress > 1.0:
            segment.item_progress = 1.0