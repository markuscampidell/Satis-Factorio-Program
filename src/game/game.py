# game.game
import pygame as py
from sys import exit

from game.initializer import Initializer

class Game:
    def __init__(self):
        py.init()
        self.context = Initializer.init_game()

        self.context.player.inventory.try_add_items("iron_ingot", 500)
        self.context.player.inventory.try_add_items("copper_ingot", 200)
        
    def run(self):
        while True:
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    exit()

                if event.type == py.VIDEORESIZE:
                    self.context.screen = py.display.set_mode((event.w, event.h), py.RESIZABLE)
                    self._update_screen_size(event.w, event.h)
                    self.context.grid.update_screen_size(event.w, event.h)
                    self.context.build_mode_renderer.update_overlay_surfaces(event.w, event.h)

                if event.type == py.MOUSEBUTTONUP and event.button == 1: 
                    self.context.machine_system.just_placed_machine = False
                
                self._handle_event(event)

            self.update()

            self.context.render_system.draw(self.context.screen)
            
            self.context.screen.blit(self.context.title_font_surface, (10, 10))
            self.context.screen.blit(self.context.font.render(f"Player position: x:{self.context.player.rect.centerx} y:{self.context.player.rect.centery}", True, "#000000"), (10, 35))
            self.context.screen.blit(self.context.font.render(f"FPS: {int(self.context.clock.get_fps())}", True, "#000000"), (10, 60))

            py.display.flip()

    def _handle_event(self, event):
        self.context.input_system.handle_keys(event)
        self.context.input_system.handle_mouse(event)

        self.context.build_system.handle_placement(event)

        self.context.machine_ui.handle_event(event, self.context.machine_system.just_placed_machine, self.context.build_system.build_mode == "building",)

        self.context.machine_interaction_system.handle_click(event, self.context.machine_system.just_placed_machine)

    def update(self):
        delta_time = self.context.clock.tick(60) / 1000
        self.context.player.update(self.context.world.machines, delta_time)
        self.context.camera.update(self.context.player)

        if self.context.hand_crafting_ui.open:
            self.context.hand_crafting_ui.update(delta_time)
            
        for segment in self.context.world.belt_segments:
            segment.update(self.context.world.belt_map, self.context.world.machines, delta_time)

        for machine in self.context.world.machines:
            machine.update(delta_time, self.context.world.belt_map)

        self.context.build_system.update_hovered_delete_target()
    
    def _update_screen_size(self, width, height):
        self.context.camera.screen_width = width
        self.context.camera.screen_height = height