#version 330 core

layout (std140) uniform Common {
    mat4 camera;
    vec4 light_direction;
    vec3 viewPos;
};

uniform sampler2D Texture;

in vec3 v_vertex;
in vec3 v_normal;
in vec2 v_uv;

layout (location = 0) out vec4 out_color;

vec3 toneMap(vec3 color) {
    return color / (color + vec3(1.0));
}

void main() {
    vec3 tex_color = texture(Texture, v_uv).rgb;
    float lum = dot(normalize(v_normal), normalize(light_direction.xyz));
    float diffuse = max(lum, 0.0) * 0.5 + 0.5;
    vec3 final_color = tex_color * diffuse;
    float gamma = 2.2;
    final_color = toneMap(final_color);
    final_color = pow(final_color, vec3(1.0 / gamma));
    out_color = vec4(final_color, texture(Texture, v_uv).a);
}
