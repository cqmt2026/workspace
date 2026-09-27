from manim import *

class MathScene(Scene):
    def construct(self):
        title = Text("鸡兔同笼", font_size=48, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)
        step0 = Text("35个头", font_size=36, color=WHITE)
        step0.next_to(title, DOWN, buff=1.0)
        self.play(Write(step0))
        self.wait(0.5)
        step1 = Text("94只脚", font_size=36, color=WHITE)
        step1.next_to(title, DOWN, buff=1.5)
        self.play(Write(step1))
        self.wait(0.5)
        step2 = Text("问鸡兔各几只", font_size=36, color=WHITE)
        step2.next_to(title, DOWN, buff=2.0)
        self.play(Write(step2))
        self.wait(0.5)
        self.wait(1)
        result = Text("[OK] 问鸡兔各几只", font_size=48, color=GREEN)
        result.next_to(step2, DOWN, buff=0.8)
        self.play(Write(result))
        self.wait(1.5)

if __name__ == "__main__":
    config.pixel_height = 1080
    config.pixel_width = 1920
    config.frame_rate = 30
    scene = MathScene()
    scene.render()
