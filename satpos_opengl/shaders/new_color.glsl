#version 330 core

layout (std140) uniform Common {
    mat4 camera;
    vec4 light_direction;
};
struct Material {
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
};
struct Light {
    vec3 position;
    vec3 direction;

    vec3 ambient;
    vec3 diffuse;
    vec3 specular;

    float constant;
    float linear;
    float quadratic;
};
uniform Light light;
uniform Material material;
uniform vec3 lightColor;

in vec3 v_vertex;
in vec3 v_normal;
in vec2 v_uv;

layout (location = 0) out vec4 FragColor;

void main() {
    // out_color = vec4(color, 1.0);
    // float lum = dot(normalize(v_normal), normalize(light_direction.xyz));
    // out_color.rgb *= max(lum, 0) * 0.5 + 0.5;

    // point light
    float l_distance = length(light.position - FragPos);
    float attenuation = 1.0 / (light.constant + light.linear * l_distance + light.quadratic * (l_distance * l_distance));

    // ambient
    vec3 viewPos = camera.xyz
    vec3 ambient = lightColor * material.ambient;

    // diffuse
    vec3 norm = normalize(v_normal);
    vec3 lightDir = normalize(lightPos - v_vertex);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = lightColor * (diff * material.diffuse);

    // specular
    vec3 viewDir = normalize(viewPos - v_vertex);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);
    vec3 specular = lightColor * (spec * material.specular);

    ambient  *= attenuation;
    diffuse  *= attenuation;
    specular *= attenuation;

    vec3 result = ambient + diffuse + specular;
    FragColor = vec4(result, 1.0);
}