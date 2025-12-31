#version 300 es

precision mediump float;

// Texture samplers for the two input textures
uniform sampler2D _MainTex;

// The texture coordinate for this fragment, interpolated from the vertices
in vec2 uvs;

// Output color of the fragment
out vec4 color;

void main()
{
    vec4 texColor = texture(_MainTex, uvs);
    //color = vec4(texColor.r, texColor.g, texColor.b, texColor.a);
    color = vec4(texColor.b, texColor.g, texColor.r, texColor.a);
}
