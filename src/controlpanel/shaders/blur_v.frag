#version 300 es

precision mediump float;

uniform sampler2D _MainTex;
uniform float _Sigma; // The size of the blur, which controls the spread of the Gaussian blur
uniform vec2 u_resolution; // The resolution of the texture being blurred
uniform int _KernelSize;

in vec2 uvs;
out vec4 color;

// Gaussian function
float gaussian(float x, float sigma) {
    return exp(-0.5 * x * x / (sigma * sigma)) / (2.0 * 3.14159265 * sigma * sigma);
}

void main() {
    vec4 sum = vec4(0.0);

    float norm = 0.0;
    for (int i = -_KernelSize; i <= _KernelSize; i++) {
        float weight = gaussian(float(i), _Sigma);
        norm += weight;
        sum += texture(_MainTex, uvs + vec2(0.0, float(i) / u_resolution.y)) * weight;
    }

    color = sum / norm;
}