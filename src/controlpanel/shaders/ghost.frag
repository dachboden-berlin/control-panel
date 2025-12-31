#version 300 es

precision mediump float;

// Texture samplers for the two input textures
uniform sampler2D _MainTex;
uniform sampler2D _SecondaryTex;
uniform float _NewIntensity;
uniform float _GhostInfluence;

// The texture coordinate for this fragment, interpolated from the vertices
in vec2 uvs;

// Output color of the fragment
out vec4 color;

void main()
{
    // Sample the pixel color from each texture
    vec4 newColor = texture(_MainTex, uvs);
    vec4 ghostColor = texture(_SecondaryTex, uvs);

    // Add the colors together
    vec4 resultColor = _NewIntensity * newColor + _GhostInfluence * ghostColor;

    // Clamp and output
    color = clamp(resultColor, 0.0, 1.0);
}
