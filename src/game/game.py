import pygame as py
from sys import exit

from core.camera import Camera
from grid.grid import Grid
from game.Objects.player import Player
from game.Objects.machines.smelter import Smelter
from game.Objects.machines.foundry import Foundry
from game.Objects.producing_machine_ui import ProducingMachineUI
from entities.player_inventory_ui import PlayerInventoryUI
from game.Objects.conveyor_belt import ConveyorBelt, BeltSegment
from core.vector2 import Vector2
from constants.itemdata import ITEMS
from game.Objects.machines.splitter import Splitter
from game.Objects.machines.producing_machine import ProducingMachine

class Game:
    def __init__(self):
        py.init()

        self.dev_mode = True

        self.screen_width, self.screen_height = 1920, 1080
        self.screen = py.display.set_mode((self.screen_width, self.screen_height))
        self.clock = py.time.Clock()
        self.font = py.font.SysFont("Arial", 32)
        self.title_font_surface = self.font.render("Satis Factorio Program", True, "#000000")

        self.just_placed_machine = False ; self.selected_machine_class = None
        self.hovered_delete_target = None ; self.build_mode = None
        self.preview_machine = None

        self.placing_belt = False
        self.belt_placement_direction = Vector2(1, 0)
        self.belt_first_axis_horizontal = True
        self.beltX1 = 0 ; self.beltY1 = 0

        self.overlay_none = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)

        self.overlay_build_select = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        self.overlay_build_select.fill((80, 160, 100, 20))

        self.overlay_build_place = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        self.overlay_build_place.fill((255, 170, 80, 28))

        self.overlay_delete = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        self.overlay_delete.fill((255, 80, 80, 35))

        self.splitter_rotation_steps = 0

        self.paused_mode = None

        self.create_starting_objects()

    def run(self):
        while True:
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    exit()
                
                if event.type == py.MOUSEBUTTONUP and event.button == 1: self.just_placed_machine = False
                
                self.event_keys(event)
                self.event_mouse(event)
                self.handle_placement(event)
                self.machine_ui.handle_event(event, self.machines, self.camera, self.screen, self.just_placed_machine, self.build_mode == "building", self.player, self.player_inventory_ui, self.screen_width, self.screen_height, self.dev_mode)

            self.update()
            self.screen.fill("#987171")

            if self.build_mode is not None:
                self.grid.draw(self.screen, self.camera)

            if self.build_mode == "building" and self.selected_machine_class:
                self.ghost_machine()
                self.ghost_conveyor_belt()

            self.draw_objects()
            self.draw_texts()
            self.draw_cursor()
            py.display.flip()


    def update(self):
        delta_time = self.clock.tick(60) / 1000
        self.player.update(self.machines)
        self.camera.update(self.player, self.screen_width, self.screen_height)

        cell = self.grid.CELL_SIZE
        all_segments = [seg for belt in self.belts for seg in belt.segments]
        for belt in self.belts:
            for segment in belt.segments:
                segment.update(all_segments=all_segments, machines=self.machines, cell_size=cell, dt=delta_time)

        for machine in self.machines:
            if isinstance(machine, ProducingMachine):
                machine.update(delta_time)
            elif isinstance(machine, Splitter):
                belt_map = {(seg.rect.x, seg.rect.y): seg for belt in self.belts for seg in belt.segments}
                machine.update(delta_time, self.grid.CELL_SIZE, belt_map)

        self.update_hovered_delete_target()

    def draw_objects(self):
        self.draw_belts()
        self.draw_items_on_belts()
        self.player.draw(self.screen, self.camera)
        for machine in self.machines:
            machine.draw(self.screen, self.camera)
        self.machine_ui.draw(self.screen)
        self.player_inventory_ui.draw(self.screen)
        self.highlight_hovered_delete_target()

        if self.build_mode == "building":
            if self.selected_machine_class is None:
                self.screen.blit(self.overlay_build_select, (0, 0))
            else:
                self.screen.blit(self.overlay_build_place, (0, 0))
        elif self.build_mode == "deleting":
            self.screen.blit(self.overlay_delete, (0, 0))

    def draw_cursor(self):
        mx, my = py.mouse.get_pos()
        
        cursor_radius = 12
        cursor_surface = py.Surface((cursor_radius * 2, cursor_radius * 2), py.SRCALPHA)

        if self.build_mode == "building":
            if self.selected_machine_class is None:
                color = (120, 255, 120, 120)
            else: color = (255, 200, 50, 150)
        elif self.build_mode == "deleting":
            color = (255, 100, 150, 120)
        else: color = (255, 255, 255, 100)

        py.draw.circle(cursor_surface, color, (cursor_radius, cursor_radius), cursor_radius)
        py.draw.circle(cursor_surface, (0, 0, 0, 200), (cursor_radius, cursor_radius), cursor_radius, width=2)
        self.screen.blit(cursor_surface, (mx - cursor_radius, my - cursor_radius))
    def draw_belts(self):
        for belt in self.belts:
            cell = Grid.CELL_SIZE
            for seg in belt.segments:
                image = py.transform.scale(belt.get_image(seg.direction), (cell, cell))
                self.screen.blit(image, (seg.rect.x - self.camera.x, seg.rect.y - self.camera.y))
    def draw_items_on_belts(self):
        cell = Grid.CELL_SIZE

        # Build lookup ONCE per frame
        next_segment_map = {
            (s.rect.x + s.direction.x * cell,
            s.rect.y + s.direction.y * cell): s
            for belt in self.belts for s in belt.segments
        }

        for belt in self.belts:
            for seg in belt.segments:
                prev_seg = next_segment_map.get((seg.rect.x, seg.rect.y))
                prev_dir = prev_seg.direction if prev_seg else seg.direction

                seg.draw_item(
                    self.screen,
                    self.camera,
                    cell_size=cell,
                    prev_direction=prev_dir
                )
                
    def get_scaled_image(self, direction, cell_size):
        key = (direction.x, direction.y)
        if key not in self.image_cache:
            original = self.get_image(direction)
            self.image_cache[key] = py.transform.scale(original, (cell_size, cell_size))
        return self.image_cache[key]


    def highlight_hovered_delete_target(self):
        if self.build_mode == "deleting" and self.hovered_delete_target is not None:
            alpha = 100 ; color = (255, 0, 0)

            if isinstance(self.hovered_delete_target, ConveyorBelt):
                for seg in self.hovered_delete_target.segments:
                    overlay = py.Surface((seg.rect.width, seg.rect.height), py.SRCALPHA)
                    overlay.fill((*color, alpha))
                    self.screen.blit(overlay, (seg.rect.x - self.camera.x, seg.rect.y - self.camera.y))
            elif hasattr(self.hovered_delete_target, 'rect'):
                rect = self.hovered_delete_target.rect
                overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
                overlay.fill((*color, alpha))
                self.screen.blit(overlay, (rect.x - self.camera.x, rect.y - self.camera.y))
            else:
                rect = self.hovered_delete_target.rect
                overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
                overlay.fill((*color, alpha))
                self.screen.blit(overlay, (rect.x - self.camera.x, rect.y - self.camera.y))
    def draw_texts(self):
        self.screen.blit(self.title_font_surface, (10, 10))
        self.screen.blit(self.font.render(f"Player position: x:{self.player.rect.centerx} y:{self.player.rect.centery}", True, "#000000"), (10, 50))
        self.screen.blit(self.font.render(f"FPS: {int(self.clock.get_fps())}", True, "#000000"), (10, 90))
        if self.dev_mode:
            self.screen.blit(self.font.render(f"DEV_MODE is True, every building is free", True, "#000000"), (10, 130))
            self.screen.blit(self.font.render(f"You can disable DEV_MODE with 0", True, "#000000"), (10, 170))
        else:
            self.screen.blit(self.font.render(f"You can enable DEV_MODE with 0", True, "#000000"), (10, 130))

    def event_keys(self, event):
        if event.type != py.KEYDOWN: return

        # 0: toggle dev_mode
        if event.key == py.K_0:
            self.dev_mode = not self.dev_mode
        
        # ESC: cancel everything
        if event.key == py.K_ESCAPE:
            self.player_inventory_ui.close()
            self.machine_ui.close()
            self.build_mode = None
            self.reset_build_state()
            self.selected_machine_class = None
            self.paused_mode = None
            return

        # TAB: toggle inventory
        if event.key == py.K_TAB:
            if not self.player_inventory_ui.open:
                if self.build_mode is not None:
                    self.paused_mode = self.build_mode
                    self.build_mode = None
                self.player_inventory_ui.open = True
            else:
                if self.paused_mode is not None:
                    self.build_mode = self.paused_mode
                    self.machine_ui.close()
                    self.paused_mode = None
                self.player_inventory_ui.close()
            return

        # Q: toggle building mode
        if event.key == py.K_q:
            self.player_inventory_ui.close()
            self.machine_ui.close()
            if self.build_mode == "building":
                self.build_mode = None
                self.reset_build_state()
            else:
                self.build_mode = "building"
                self.placing_belt = False
            return

        # X: toggle deleting mode
        if event.key == py.K_x:
            if self.player_inventory_ui.open:
                self.player_inventory_ui.close()
                self.paused_mode = None
            if self.machine_ui.open:
                self.machine_ui.close()
            if self.build_mode == "deleting":
                self.build_mode = 'building'
            else:
                self.build_mode = "deleting"
                self.placing_belt = False
            return

        if event.key == py.K_i:
            if self.machine_ui.open and self.machine_ui.selected_machine:
                machine = self.machine_ui.selected_machine

                # Add items to each input inventory separately
                for item_id, amount in machine.recipe.inputs.items():
                    if item_id in machine.input_inventories:
                        inv = machine.input_inventories[item_id]
                        inv.add_items(item_id, amount)
            return

        if self.player_inventory_ui.open or self.machine_ui.open: return

        # Rotate machines and conveyorbelts
        if event.key == py.K_r:
            if self.build_mode != "building": return
            if self.selected_machine_class is Splitter:
                self.splitter_rotation_steps = (self.splitter_rotation_steps + 1) % 4
            elif self.selected_machine_class is ConveyorBelt:
                x, y = self.belt_placement_direction.x, self.belt_placement_direction.y
                self.belt_placement_direction = Vector2(-y, x)

        # T: toggle first axis of belt placement
        if event.key == py.K_t:
            if self.build_mode != "building" or self.selected_machine_class is not ConveyorBelt or not self.placing_belt: return
            self.belt_first_axis_horizontal = not self.belt_first_axis_horizontal

        # Number keys: select machine → switch to building mode automatically
        if self.build_mode in ("building", "deleting"):
            if event.key in (py.K_1, py.K_2, py.K_3, py.K_4):
                if event.key == py.K_1: self.selected_machine_class = Smelter
                elif event.key == py.K_2: self.selected_machine_class = Foundry
                elif event.key == py.K_3: self.selected_machine_class = ConveyorBelt
                elif event.key == py.K_4: self.selected_machine_class = Splitter

                if self.selected_machine_class is not ConveyorBelt:
                    self.placing_belt = False
                if self.build_mode == "deleting":
                    self.build_mode = "building"
    def event_mouse(self, event):
        if self.machine_ui.open or self.player_inventory_ui.open: return
        if event.type != py.MOUSEBUTTONDOWN or event.button != 3: return

        if self.build_mode == "deleting": 
            self.build_mode = "building"
        elif self.placing_belt: 
            self.placing_belt = False
        elif self.selected_machine_class is not None: 
            self.selected_machine_class = None
        else: 
            self.build_mode = None
            self.reset_build_state()
    
    def handle_placement(self, event):
        if self.player_inventory_ui.open or self.machine_ui.open: return
        if event.type != py.MOUSEBUTTONDOWN: return
        mx, my = event.pos

        if event.button == 1:
            if self.build_mode == "deleting":
                self.delete_machine(mx, my)
                self.delete_belt(mx, my, delete_whole=bool(py.key.get_mods() & py.KMOD_SHIFT))
                return
            
            if self.build_mode == "building" and self.selected_machine_class is ConveyorBelt:
                if not self.placing_belt:
                    if self.is_mouse_over_ui(mx, my): return
                    self.placing_belt = True
                    self.beltX1 = mx + self.camera.x
                    self.beltY1 = my + self.camera.y
                    return
                else:
                    self.place_belt(mx, my, mx + self.camera.x, my + self.camera.y, first_segment_direction=self.belt_placement_direction)
                    self.placing_belt = False
                    return

            if self.build_mode == "building":
                if self.selected_machine_class is None: return
                self.place_machine()
                if hasattr(self, 'preview_splitter'):
                    self.preview_splitter = None

    def create_starting_objects(self):
        self.camera = Camera(self.screen_width, self.screen_height)
        self.grid = Grid(self.screen_width, self.screen_height)
        self.player = Player(self.grid.CELL_SIZE)
        self.camera.x = self.player.rect.centerx - self.screen_width // 2
        self.camera.y = self.player.rect.centery - self.screen_height // 2
        self.machines = []
        self.belt_grid = {}
        self.machine_ui = ProducingMachineUI(self.screen_width, self.screen_height)
        self.player_inventory_ui = PlayerInventoryUI(self.player)

        self.belts = []

        #world_w = self.grid.width
        #world_h = self.grid.height

        #self.grid_surface = py.Surface((world_w, world_h), py.SRCALPHA)
        #self.grid.draw(self.grid_surface, camera=None, alpha=60)


    def place_machine(self):
        if self.selected_machine_class is None: return
        (snapped_x, snapped_y), blocked = self.get_machine_placement_preview()
        if blocked: return

        cost = self.selected_machine_class.BUILD_COST
        if not self.dev_mode:
            if not self.player.inventory.has_enough_build_cost_items(cost): return
            self.player.inventory.remove_build_cost_items(cost)

        if self.selected_machine_class is Splitter:
            splitter = Splitter((snapped_x, snapped_y))
            for _ in range(self.splitter_rotation_steps):
                splitter.rotate()
            splitter.rect.center = (snapped_x, snapped_y)
    
            cell_size = self.grid.CELL_SIZE
            belt_map = {(seg.rect.x, seg.rect.y): seg for belt in self.belts for seg in belt.segments}
            splitter.output_belts = []
            for direction in splitter._get_relative_dirs():
                next_rect = splitter.rect.move(int(direction.x * cell_size), int(direction.y * cell_size))
                seg = belt_map.get((next_rect.x, next_rect.y))
                if seg: splitter.output_belts.append(seg)

            if splitter.output_belts: splitter.current_output_index %= len(splitter.output_belts)
            else: splitter.current_output_index = 0

            self.machines.append(splitter)
            self.update_all_splitters_outputs()
            self.preview_machine = None

        else: self.machines.append(self.selected_machine_class(pos=(snapped_x, snapped_y)))

        self.just_placed_machine = True
        self.machine_ui.close()
    def delete_machine(self, mx, my):
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        for machine in self.machines:
            if machine.rect.collidepoint(world_x, world_y):
                if self.machine_ui.selected_machine == machine:
                    self.machine_ui.close()

                if not self.dev_mode:
                    if hasattr(machine, "transfer_processing_items_to_player"):
                        machine.transfer_processing_items_to_player(self.player.inventory)
                    if isinstance(machine, Splitter) and machine.current_item:
                        self.player.inventory.add_items(machine.current_item, 1)
                        machine.current_item = None
                    for item_id, amount in machine.BUILD_COST.items():
                        self.player.inventory.add_items(item_id, amount)

                self.machines.remove(machine)
                return
    def ghost_machine(self):
        if self.selected_machine_class is None: return
        if self.selected_machine_class is not ConveyorBelt:
            if self.build_mode != 'building': return

            mx, my = py.mouse.get_pos()
            world_x, world_y = mx + self.camera.x, my + self.camera.y
            cell = self.grid.CELL_SIZE
            snapped_x = (world_x // cell) * cell + cell // 2 ; snapped_y = (world_y // cell) * cell + cell // 2
            temp_rect = py.Rect(snapped_x - self.selected_machine_class.SIZE // 2, snapped_y - self.selected_machine_class.SIZE // 2, self.selected_machine_class.SIZE, self.selected_machine_class.SIZE)

            blocked = self.is_rect_blocked(temp_rect)
            can_afford = True
            if not self.dev_mode: can_afford = self.player.inventory.has_enough_build_cost_items(self.selected_machine_class.BUILD_COST)

            if self.selected_machine_class is Splitter:
                preview = Splitter((snapped_x, snapped_y))
                for _ in range(self.splitter_rotation_steps): preview.rotate()
                ghost = preview.image.copy()

            else:
                ghost = py.Surface((self.selected_machine_class.SIZE, self.selected_machine_class.SIZE), py.SRCALPHA)
                if self.selected_machine_class.SPRITE_PATH:
                    original = py.image.load(self.selected_machine_class.SPRITE_PATH).convert_alpha()
                    img = py.transform.scale(original, (self.selected_machine_class.SIZE, self.selected_machine_class.SIZE))
                    ghost.blit(img, (0, 0))

            ghost.set_alpha(120)
            if blocked or not can_afford:
                overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
                overlay.fill((255, 0, 0, 120))
                ghost.blit(overlay, (0, 0))

            self.screen.blit(ghost, (snapped_x - self.camera.x - ghost.get_width() // 2, snapped_y - self.camera.y - ghost.get_height() // 2))

    def place_belt(self, mx, my, world_x2, world_y2, first_segment_direction=None):
        if self.is_mouse_over_ui(mx, my): return
        rects, blocked = self.get_dragging_belt_placement_preview(world_x2, world_y2)
        if blocked: return
        
        belt = ConveyorBelt(rects)
        if len(belt.segments) == 1:
            if first_segment_direction is not None:  belt.segments[0].direction = first_segment_direction
            else: belt.segments[0].direction = Vector2(1, 0)

        total_cost = {}
        for seg in belt.segments:
            for item_id, amount in seg.BUILD_COST.items():
                total_cost[item_id] = total_cost.get(item_id, 0) + amount

        if not self.dev_mode:
            if not self.player.inventory.has_enough_build_cost_items(total_cost): return
            self.player.inventory.remove_build_cost_items(total_cost)

        self.belts.append(belt)
        self.update_all_splitters_outputs()
    def delete_belt(self, mx, my, delete_whole=False):
        world_x = mx + self.camera.x ; world_y = my + self.camera.y

        for belt in self.belts[:]:
            for seg in belt.segments[:]:
                if seg.rect.collidepoint(world_x, world_y):
                    if delete_whole:
                        if not self.dev_mode:
                            belt.refund_all_items(self.player.inventory)
                            for s in belt.segments:
                                for item_id, amount in s.BUILD_COST.items():
                                    self.player.inventory.add_items(item_id, amount)
                        self.belts.remove(belt)
                    else:
                        if not self.dev_mode:
                            seg.refund_item(self.player.inventory)
                            for item_id, amount in seg.BUILD_COST.items():
                                self.player.inventory.add_items(item_id, amount)
                        belt.segments.remove(seg)
                        if len(belt.segments) == 0:
                            self.belts.remove(belt)
                    self.update_all_splitters_outputs()
                    return
    def ghost_conveyor_belt(self):
        if self.selected_machine_class is not ConveyorBelt: return
        mx, my = py.mouse.get_pos()
        world_x, world_y = mx + self.camera.x, my + self.camera.y
        cell = self.grid.CELL_SIZE

        if not self.placing_belt:
            if self.build_mode == "deleting": return
            snapped_x = (world_x // cell) * cell ; snapped_y = (world_y // cell) * cell
            temp_rect = py.Rect(snapped_x, snapped_y, cell, cell)
            blocked = self.is_rect_blocked(temp_rect)
            if self.dev_mode:
                color = "red" if blocked else "normal"
                ConveyorBelt.draw_ghost_belt(self.screen, self.camera, snapped_x, snapped_y, self.belt_placement_direction or Vector2(1, 0), color_flag=color)
                return

            segment_cost = BeltSegment(py.Rect(0, 0, cell, cell), Vector2(1, 0)).BUILD_COST
            if blocked: color = "red"
            elif self.player.inventory.has_enough_build_cost_items(segment_cost): color = "normal"
            else: color = "yellow"
            ConveyorBelt.draw_ghost_belt(self.screen, self.camera, snapped_x, snapped_y, self.belt_placement_direction or Vector2(1, 0), color_flag=color)
            return

        rects, any_blocked = self.get_dragging_belt_placement_preview(world_x, world_y)
        if self.dev_mode:
            color_flags = ["red" if any_blocked else "normal"] * len(rects)
            ConveyorBelt.draw_ghost_belt_while_dragging(self.screen, self.camera, rects, start_direction=self.belt_placement_direction or Vector2(1, 0), color_flags=color_flags)
            return

        segment_cost = BeltSegment(py.Rect(0, 0, cell, cell), Vector2(1, 0)).BUILD_COST
        color_flags = []
        if any_blocked: color_flags = ["red"] * len(rects)
        else:
            total_cost = {item_id: amount * len(rects) for item_id, amount in segment_cost.items()}
            if all(self.player.inventory.get_amount(i) >= a for i, a in total_cost.items()):
                color_flags = ["normal"] * len(rects)
            else:
                remaining = {i: self.player.inventory.get_amount(i) for i in segment_cost}
                for _ in rects:
                    if all(remaining[i] >= amount for i, amount in segment_cost.items()):
                        color_flags.append("orange")
                        for i, amount in segment_cost.items(): remaining[i] -= amount
                    else: color_flags.append("yellow")

        ConveyorBelt.draw_ghost_belt_while_dragging(self.screen, self.camera, rects, start_direction=self.belt_placement_direction or Vector2(1, 0), color_flags=color_flags)
    def can_afford_belt(self, belt_segments):
        total_cost = {}
        for seg in belt_segments:
            for item_id, amount in seg.BUILD_COST.items(): total_cost[item_id] = total_cost.get(item_id, 0) + amount
        return self.player.inventory.has_enough_build_cost_items(total_cost)
    def get_preview_belt_segments(self, rects):
        segments = []
        for rect in rects:
            temp_seg = BeltSegment(rect, Vector2(1, 0)) ; segments.append(temp_seg)
        return segments

    def update_all_splitters_outputs(self):
        cell = self.grid.CELL_SIZE
        belt_map = {(seg.rect.x, seg.rect.y): seg for belt in self.belts for seg in belt.segments}

        for machine in self.machines:
            if isinstance(machine, Splitter):
                output_belts = []
                for direction in machine._get_relative_dirs():
                    next_rect = machine.rect.move(int(direction.x * cell), int(direction.y * cell))
                    seg = belt_map.get((next_rect.x, next_rect.y))
                    output_belts.append(seg)

                machine.output_belts = [b for b in output_belts if b]

                if machine.output_belts: machine.current_output_index %= len(machine.output_belts)
                else: machine.current_output_index = 0
    def is_mouse_over_ui(self, mx, my):
        return (self.machine_ui.open and self.machine_ui.rect.collidepoint(mx, my)) or (self.player_inventory_ui.open and self.player_inventory_ui.rect.collidepoint(mx, my))
    def update_hovered_delete_target(self):
        if self.build_mode != "deleting": self.hovered_delete_target = None ; return
        mx, my = py.mouse.get_pos()
        world_x = mx + self.camera.x
        world_y = my + self.camera.y
        shift_held = py.key.get_mods() & py.KMOD_SHIFT
        for machine in self.machines:
            if machine.rect.collidepoint(world_x, world_y):
                self.hovered_delete_target = machine ; return
        for belt in self.belts:
            for seg in belt.segments:
                if seg.rect.collidepoint(world_x, world_y):
                    if shift_held: self.hovered_delete_target = belt
                    else: self.hovered_delete_target = seg
                    return

        self.hovered_delete_target = None
    def get_machine_placement_preview(self):
        mx, my = py.mouse.get_pos() ; world_x = mx + self.camera.x ; world_y = my + self.camera.y ; cell = self.grid.CELL_SIZE
        snapped_x = (world_x // cell) * cell + cell // 2 ; snapped_y = (world_y // cell) * cell + cell // 2
        temp_machine_rect = py.Rect(0, 0, self.selected_machine_class.SIZE, self.selected_machine_class.SIZE) ; temp_machine_rect.center = (snapped_x, snapped_y)
        blocked = False

        if self.player.rect.colliderect(temp_machine_rect): blocked = True
        for machine in self.machines:
            if machine.rect.colliderect(temp_machine_rect): blocked = True ; break
        if not blocked:
            for belt in self.belts:
                for seg in belt.segments:
                    if seg.rect.colliderect(temp_machine_rect): blocked = True ; break
                if blocked: break
        return (snapped_x, snapped_y), blocked
    def get_dragging_belt_placement_preview(self, world_x2, world_y2):
        cell = self.grid.CELL_SIZE
        x1 = int((self.beltX1 // cell) * cell) ; y1 = int((self.beltY1 // cell) * cell)
        x2 = int((world_x2 // cell) * cell) ; y2 = int((world_y2 // cell) * cell)
        rects = []
        blocked = False

        if self.belt_first_axis_horizontal:
            dx = 1 if x2 > x1 else -1
            for x in range(x1, x2 + dx * cell, dx * cell):
                r = py.Rect(x, y1, cell, cell)
                if self.is_rect_blocked(r): blocked = True
                rects.append(r)
            dy = 1 if y2 > y1 else -1
            for y in range(y1 + dy * cell, y2 + dy * cell, dy * cell):
                r = py.Rect(x2, y, cell, cell)
                if self.is_rect_blocked(r): blocked = True
                rects.append(r)
        else:
            dy = 1 if y2 > y1 else -1
            for y in range(y1, y2 + dy * cell, dy * cell):
                r = py.Rect(x1, y, cell, cell)
                if self.is_rect_blocked(r): blocked = True
                rects.append(r)
            dx = 1 if x2 > x1 else -1
            for x in range(x1 + dx * cell, x2 + dx * cell, dx * cell):
                r = py.Rect(x, y2, cell, cell)
                if self.is_rect_blocked(r): blocked = True
                rects.append(r)

        return rects, blocked
    def is_rect_blocked(self, rect):
        if self.player.rect.colliderect(rect): return True
        for machine in self.machines:
            if machine.rect.colliderect(rect): return True
        for belt in self.belts:
            for seg in belt.segments: 
                if seg.rect.colliderect(rect): return True
        return False
    def reset_build_state(self):
        self.placing_belt = False
        self.belt_placement_direction = Vector2(1, 0)
        self.splitter_rotation_steps = 0
        self.belt_first_axis_horizontal = True

game = Game()
for item in ITEMS: item.load_sprite()
game.run()