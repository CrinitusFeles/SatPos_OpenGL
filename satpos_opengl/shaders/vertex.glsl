#version 330 core
layout (std140) uniform Common {
    mat4 camera;
    vec4 light_direction;
    vec3 viewPos;
};

uniform mat4 transform;

layout (location = 0) in vec3 in_vertex;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec2 in_uv;

out vec3 v_vertex;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world_pos = transform * vec4(in_vertex, 1.0);
    v_vertex = world_pos.xyz;
    v_normal = mat3(transform) * in_normal;
    v_uv = in_uv;

    gl_Position = camera * world_pos;
}