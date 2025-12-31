"""
This module defines all available shaders and their uniforms
"""

RENDER_SIZE = (960, 540)
RENDER_HEIGHT = RENDER_SIZE[1]


downscale_uniforms = {
    '_MainTex': 0,
}

threshold_shader_uniforms = {
    '_MainTex': 1,
    '_LuminanceThreshold': 0.07,
}

blur_shader_uniforms = {
    '_MainTex': 1,
    '_Sigma': (sigma := 10),
    'u_resolution': RENDER_SIZE,
    '_KernelSize': 4*sigma+1,
}

ghost_shader_uniforms = {
    '_MainTex': 1,
    '_SecondaryTex': 2,
    '_NewIntensity': 0.6,
    '_GhostInfluence': 0.9,
}

add_shader_uniforms = {
    '_MainTex': 0,
    '_SecondaryTex': 2,
    '_Influence': (.25, .25, .25, 0.0), # TODO: Does this do anything?
}

crt_shader_uniforms = {
    '_MainTex': 0,
    '_Curvature': 8.0,
    '_VignetteWidth': 40.0,
    '_ScreenParams': RENDER_SIZE,
    '_ScanlineHeight': 2.0 / RENDER_HEIGHT,
    '_ScanlineStrength': 1.2,
}

to_bgra_uniforms = {
    '_MainTex': 0,
}

shader_params: dict[str, tuple[str, str, dict]] = {
    "Downscale": ("quad.vert", "downscale.frag", downscale_uniforms),
    "Threshold": ("quad.vert", "threshold.frag", threshold_shader_uniforms),
    "Blur_H": ("quad.vert", "blur_h.frag", blur_shader_uniforms),
    "Blur_V": ("quad.vert", "blur_v.frag", blur_shader_uniforms),
    "Ghost": ("quad.vert", "ghost.frag", ghost_shader_uniforms),
    "Add": ("quad.vert", "add.frag", add_shader_uniforms),
    "CRT": ("quad.vert", "crt.frag", crt_shader_uniforms),
    "To_BGRA": ("quad.vert", "to_bgra.frag", to_bgra_uniforms),
}
