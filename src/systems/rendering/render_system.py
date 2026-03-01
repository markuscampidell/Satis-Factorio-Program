# systems.rendering.render_system
class RenderSystem:
    def __init__(self, world_renderer, build_renderer, ui_renderer, cursor_renderer):
        self.world_renderer = world_renderer
        self.build_renderer = build_renderer
        self.ui_renderer = ui_renderer
        self.cursor_renderer = cursor_renderer

    def draw(self, screen):
        screen.fill("#987171") # background color

        self.world_renderer.draw(screen) # machines/beltsegments/splitters...
        self.build_renderer.draw(screen) # overlays/ghost machines/ghost beltsegments...
        self.ui_renderer.draw(screen) # player inventory/handcrafting...
        self.cursor_renderer.draw(screen) # cursor circle