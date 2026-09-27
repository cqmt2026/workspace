"""Manim 牛吃草问题 - 公式动画（不用LaTeX，纯Text）"""
from manim import *

class CowGrassFormulas(Scene):
    def construct(self):
        # 标题
        title = Text("牛吃草问题", font_size=48, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)
        
        # 题目条件
        cond1 = Text("27头牛 6天吃完", font_size=36, color=WHITE)
        cond2 = Text("23头牛 9天吃完", font_size=36, color=WHITE)
        cond3 = Text("问：21头牛 几天吃完？", font_size=36, color=GREEN)
        
        cond1.next_to(title, DOWN, buff=0.8)
        cond2.next_to(cond1, DOWN, buff=0.3)
        cond3.next_to(cond2, DOWN, buff=0.5)
        
        self.play(Write(cond1), Write(cond2))
        self.wait(0.5)
        self.play(Write(cond3))
        self.wait(1)
        
        # 清屏
        self.play(FadeOut(cond1), FadeOut(cond2), FadeOut(cond3), FadeOut(title))
        self.wait(0.3)
        
        # 解题步骤
        step1_title = Text("设每头牛每天吃 1 份草", font_size=36, color=YELLOW)
        step1_title.to_edge(UP)
        self.play(Write(step1_title))
        
        f1 = Text("27 x 6 = 162（份）", font_size=48, color=WHITE)
        f1.next_to(step1_title, DOWN, buff=0.8)
        self.play(Write(f1))
        
        f2 = Text("23 x 9 = 207（份）", font_size=48, color=WHITE)
        f2.next_to(f1, DOWN, buff=0.4)
        self.play(Write(f2))
        self.wait(0.5)
        
        diff = Text("207 - 162 = 45（份，3天新草）", font_size=48, color=YELLOW)
        diff.next_to(f2, DOWN, buff=0.6)
        self.play(Write(diff))
        self.wait(0.5)
        
        daily = Text("45 ÷ 3 = 12（份/天，每天新草）", font_size=48, color=GREEN)
        daily.next_to(diff, DOWN, buff=0.4)
        self.play(Write(daily))
        self.wait(0.5)
        
        original = Text("162 - 6 x 12 = 90（份，原有草）", font_size=48, color=GREEN)
        original.next_to(daily, DOWN, buff=0.6)
        self.play(Write(original))
        self.wait(1)
        
        # 清屏
        self.play(FadeOut(step1_title), FadeOut(f1), FadeOut(f2), 
                  FadeOut(diff), FadeOut(daily), FadeOut(original))
        self.wait(0.3)
        
        # 最终答案
        ans_title = Text("答案", font_size=52, color=YELLOW)
        ans_title.to_edge(UP)
        self.play(Write(ans_title))
        
        ans1 = Text("21 - 12 = 9（份/天，净减少）", font_size=48, color=RED)
        ans1.next_to(ans_title, DOWN, buff=0.8)
        self.play(Write(ans1))
        
        ans2 = Text("90 ÷ 9 = 10（天）", font_size=56, color=GREEN)
        ans2.next_to(ans1, DOWN, buff=0.6)
        self.play(Write(ans2))
        
        result = Text("✅ 21头牛 10天吃完", font_size=48, color=GREEN)
        result.next_to(ans2, DOWN, buff=0.8)
        self.play(Write(result))
        self.wait(1.5)


if __name__ == "__main__":
    config.pixel_height = 1080
    config.pixel_width = 1920
    config.frame_rate = 30
    config.output_file = "cow_grass_formulas"
    scene = CowGrassFormulas()
    scene.render()