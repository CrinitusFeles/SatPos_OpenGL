#version 330 core

layout (std140) uniform Common {
    mat4 camera;
    vec4 light_direction;
};

uniform vec3 color;

in vec3 v_vertex;
in vec3 v_normal;
in vec2 v_uv;

layout (location = 0) out vec4 out_color;

void main() {
    out_color = vec4(color, 1.0);
    float lum = dot(normalize(v_normal), normalize(light_direction.xyz));
    out_color.rgb *= max(lum, 0) * 0.5 + 0.5;
}