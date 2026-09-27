# -*- coding: utf-8 -*-
"""
地图绘制风格配置
定义不同绘制风格的样式参数
"""

STYLE_CONFIGS = {
    "default": {
        "figure_size": (1080, 1920),
        "dpi": 300,
        "font_size": 14,
        "title_fontsize": 24,
        "label_fontsize": 12,
        "color_map": "YlOrRd",
        "highlight_color": "#FF4444",
        "bg_color": "#1a1a2e",
        "text_color": "#ffffff",
    },
    "direct": {
        "figure_size": (1080, 1920),
        "dpi": 300,
        "font_size": 14,
        "title_fontsize": 24,
        "label_fontsize": 12,
        "color_map": "YlOrRd",
        "highlight_color": "#FF6B35",
        "bg_color": "#0f1923",
        "text_color": "#e0e0e0",
        "bar_color": "#3b82f6",
        "accent_color": "#10b981",
    },
    "minimal": {
        "figure_size": (1080, 1920),
        "dpi": 300,
        "font_size": 12,
        "title_fontsize": 20,
        "label_fontsize": 10,
        "color_map": "Greys",
        "highlight_color": "#000000",
        "bg_color": "#ffffff",
        "text_color": "#333333",
    },
    "dark": {
        "figure_size": (1080, 1920),
        "dpi": 300,
        "font_size": 14,
        "title_fontsize": 24,
        "label_fontsize": 12,
        "color_map": "viridis",
        "highlight_color": "#fbbf24",
        "bg_color": "#0f172a",
        "text_color": "#f8fafc",
    },
}
