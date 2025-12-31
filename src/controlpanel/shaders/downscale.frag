#version 300 es

precision mediump float; // Required in ES for specifying default precision for float types

uniform sampler2D _MainTex; // The original texture
in vec2 uvs;
out vec4 color;

void main()
{
    color = texture(_MainTex, uvs);
}