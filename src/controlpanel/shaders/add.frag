#version 300 es

precision mediump float;

// Texture samplers for the two input textures
uniform sampler2D _MainTex;
uniform sampler2D _SecondaryTex;
uniform vec4 _Influence;

// The texture coordinate for this fragment, interpolated from the vertices
in vec2 uvs;

// Output color of the fragment
out vec4 color;

void main()
{
    // Sample the pixel color from each texture
    vec4 color1 = texture(_MainTex, uvs);
    vec4 color2 = texture(_SecondaryTex, uvs);

    // Add the colors together
    vec4 resultColor = color1 + _Influence * color2;

    // Optionally, clamp the result to the valid range [0, 1]
    resultColor = clamp(resultColor, 0.0, 1.0);

    // Set the output color of the fragment
    color = resultColor;
}
