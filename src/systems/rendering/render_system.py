# systems.rendering.render_system
class RenderSystem:
    def __init__(self, world_renderer, build_renderer, ui_renderer, cursor_renderer, game_menu_bar_renderer, build_hotbar):
        self.world_renderer = world_renderer
        self.build_renderer = build_renderer
        self.ui_renderer = ui_renderer
        self.cursor_renderer = cursor_renderer
        self.game_menu_bar_renderer = game_menu_bar_renderer
        self.build_hotbar = build_hotbar

    def draw(self, screen):
        screen.fill("#987171") # background color

        self.world_renderer.draw(screen)
        self.build_renderer.draw(screen)
        self.ui_renderer.draw(screen)
        self.build_hotbar.draw(screen)
        self.cursor_renderer.draw(screen)
        self.game_menu_bar_renderer.draw(screen)