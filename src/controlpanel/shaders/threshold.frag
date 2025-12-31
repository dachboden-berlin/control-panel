#version 300 es

precision mediump float; // Required in ES for specifying default precision for float types

in vec2 uvs;
out vec4 color;

uniform sampler2D _MainTex;
uniform float _LuminanceThreshold;

void main() {
    vec4 texColor = texture(_MainTex, uvs);
    float luminance = dot(texColor.rgb, vec3(0.2126, 0.7152, 0.0722));
    if (luminance < _LuminanceThreshold) {
        color = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        color = texColor;
    }
}
