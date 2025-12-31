#version 330

in vec2 fragmentTexCoord;
in vec3 fragmentColor;  // Unused, but required if vertex shader outputs it

uniform sampler2D imageTexture;
uniform float _Curvature;       // lower values -> higher curvature
uniform float _VignetteWidth;
uniform vec2 _ScreenParams;     // Viewport Size
uniform float _ScanlineY;       // Y position of Scanline on V axis [0,1]
uniform float _ScanlineHeight;  // height of Scanline on V axis [0,1]
uniform float _ScanlineStrength;

void main() {
    vec2 uv = fragmentTexCoord * 2.0 - 1.0;
    vec2 offset = uv.yx / _Curvature;
    uv = uv + uv * offset * offset;
    uv = uv * 0.5 + 0.5;

    vec4 col = texture(imageTexture, uv);
    if (uv.x <= 0.0 || 1.0 <= uv.x || uv.y <= 0.0 || 1.0 <= uv.y)
        col = vec4(0.0, 0.0, 0.0, 1.0);

    if (abs(uv.y - _ScanlineY) < _ScanlineHeight)
        col.rgb *= _ScanlineStrength;

    col.g *= (sin(uv.y * _ScreenParams.y * 2.0) + 1.0) * 0.15 + 1.0;
    col.rb *= (cos(uv.y * _ScreenParams.y * 2.0) + 1.0) * 0.135 + 1.0;

    uv = uv * 2.0 - 1.0;
    vec2 vignette = _VignetteWidth / _ScreenParams.xy;
    vignette = smoothstep(0.0, vignette.x, 1.0 - abs(uv));
    vignette = clamp(vignette, 0.0, 1.0);

    gl_FragColor = clamp(col, 0.0, 1.0) * vignette.x * vignette.y;
}
