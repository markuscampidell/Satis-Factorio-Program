import pygame as py
from sys import exit

from core.camera import Camera
from grid.grid import Grid
from game.Objects.player import Player
from game.Objects.machines.smelter import Smelter
from game.Objects.machines.foundry import Foundry
from game.Objects.machine_ui import MachineUI
from entities.player_inventory_ui import PlayerInventoryUI

class Game:
    def __init__(self):
        py.init()
        self.screen_width, self.screen_height = 1920, 1080
        self.screen = py.display.set_mode((self.screen_width, self.screen_height))
        self.clock = py.time.Clock()

        self.font = py.font.SysFont("Arial", 32)
        self.title_font_surface = self.font.render("Satis Factorio Program", True, "#000000")

        self.just_placed_machine = False
        self.selected_machine_class = Smelter

        self.building = False

        self.create_all_starting_objects()

    def create_all_starting_objects(self):
        self.camera = Camera(self.screen_width, self.screen_height)
        self.grid = Grid(32, self.screen_width, self.screen_height)
        self.player = Player(32)
        self.machines = []
        self.machine_ui = MachineUI()
        self.player_inventory_ui = PlayerInventoryUI(self.player)
    
    def handle_placement(self, event):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1: return
        if self.building == False: return

        self.place_machine()

    def place_machine(self):
        # Dont go farther if the mouse is in a UI
        mx, my = py.mouse.get_pos()
        if self.machine_ui.open:
            if self.machine_ui.rect.collidepoint(mx, my): return
        if self.player_inventory_ui.open:
            if self.player_inventory_ui.rect.collidepoint(mx, my): return

        # Position Detection Shenanigans
        mx, my = py.mouse.get_pos()
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        cell = self.grid.cell_size
        snapped_x = (world_x // cell) * cell + cell // 2
        snapped_y = (world_y // cell) * cell + cell // 2

        # Dont place if player or other machines are in the way
        temp_rect = py.Rect(0, 0, 96, 96)
        temp_rect.center = (snapped_x, snapped_y)

        if temp_rect.colliderect(self.player.rect): return
        for machine in self.machines:
            if machine.rect.colliderect(temp_rect): return

        # Then actually place a machine
        self.machines.append(self.selected_machine_class((snapped_x, snapped_y)))
        self.just_placed_machine = True
        self.machine_ui.close()


    def delete_machine(self, event):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 3: return

        mx, my = py.mouse.get_pos()
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        # Try deleting a machine
        for machine in self.machines:
            if machine.rect.collidepoint(world_x, world_y):
                if self.machine_ui.selected_machine == machine:
                    self.machine_ui.close()
                self.machines.remove(machine)
                return
            
    def update(self):
        dt = self.clock.tick(60) / 1000
        self.player.update(self.machines)
        self.camera.update(self.player, self.screen_width, self.screen_height)
        for machine in self.machines:
            machine.update(dt)

    def draw_objects(self):
        self.screen.fill("#918D8D")
        self.grid.draw(self.screen, self.camera)
        for machine in self.machines:
            machine.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.machine_ui.draw(self.screen)
        self.player_inventory_ui.draw(self.screen)
    
    def draw_texts(self):
        self.screen.blit(self.title_font_surface, (10, 10))
        self.screen.blit(self.font.render(f"X: {self.player.rect.x} Y: {self.player.rect.y}", True, "#000000"), (10, 50))
        self.screen.blit(self.font.render(f"FPS: {int(self.clock.get_fps())}", True, "#000000"), (10, 90))

    def run(self):
        while True:
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    exit()
                
                if event.type == py.MOUSEBUTTONUP and event.button == 1:
                    self.just_placed_machine = False
                
                if event.type == py.KEYDOWN:
                    if event.key == py.K_q:
                        self.building = not self.building
                        print(self.building)
                    
                    if event.key == py.K_TAB:
                        self.player_inventory_ui.open = not self.player_inventory_ui.open
                        
                    if self.building == True:
                        if event.key == py.K_1:
                            self.selected_machine_class = Smelter

                        elif event.key == py.K_2:
                            self.selected_machine_class = Foundry

                    



                self.handle_placement(event)
                self.delete_machine(event)
                self.machine_ui.handle_event(event, self.machines, self.camera, self.screen, self.just_placed_machine, self.building, self.player, self.player_inventory_ui)
                self.player_inventory_ui.handle_event(event)

            self.update()
            self.draw_objects()
            self.draw_texts()

            py.display.flip()

game = Game()
game.run()