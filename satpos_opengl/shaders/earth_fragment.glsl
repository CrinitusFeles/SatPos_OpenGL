#version 330 core

layout (std140) uniform Common {
    mat4 camera;
    vec4 light_direction; // Предполагается, что это вектор направления ОТ солнца
    vec3 viewPos;
};

uniform sampler2D day_texture;
uniform sampler2D night_texture;
uniform sampler2D cloud_texture;
uniform sampler2D normal_map;
uniform sampler2D specular_map;

in vec3 v_vertex;  // Позиция в мировых координатах (или локальных, если сфера в 0,0,0)
in vec3 v_normal;  // Нормаль вершины
in vec2 v_uv;      // UV координаты

layout (location = 0) out vec4 out_color;

vec3 calculate_lighting(vec3 normal, vec3 light_dir, vec3 diffuse_color, float specular_strength) {
    float diff = max(dot(normal, normalize(light_dir)), 0.0);
    vec3 view_dir = normalize(viewPos - v_vertex);
    vec3 reflect_dir = reflect(-normalize(light_dir), normal);
    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32.0) * specular_strength;

    return vec3(diff) * diffuse_color + (spec * 0.5);
}

void main() {
    // 1. Подготовка данных освещения
    vec3 N = normalize(v_normal);
    // Используем нормаль из карты нормалей для детализации (опционально)
    vec3 normal_map_data = texture(normal_map, v_uv).rgb * 2.0 - 1.0;
    N = normalize(N + normal_map_data * 0.005); // Смешиваем базовую нормаль с картой

    vec3 L = normalize(v_vertex-light_direction.xyz); // Направление на солнце
    vec3 V = normalize(viewPos - v_vertex);   // Направление на камеру
    // Но для сферы обычно используют вектор от центра (0,0,0) до точки.
    vec3 view_dir = normalize(-v_vertex);

    // 2. Расчет освещенности (Dot product)
    float diffuse = max(dot(N, L), 0.0);
    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.0); // Эффект атмосферного свечения по краям

    // 3. Текстуры
    vec4 day_color = texture(day_texture, v_uv);
    vec4 night_color = texture(night_texture, v_uv);
    float cloud_mask = texture(cloud_texture, v_uv).r;
    float specular_strength = texture(specular_map, v_uv).r;

    float light_intensity = clamp(dot(N, L), 0.0, 1.0);
    float term = smoothstep(-0.1, 0.1, dot(N, L));
    vec3 base_color = mix(night_color.rgb, day_color.rgb, term);

    // 5. Отражения (Specular)
    vec3 R = reflect(-L, N);
    float spec = pow(max(dot(R, view_dir), 0.0), 32.0) * specular_strength;
    vec3 specular_color = vec3(0.5, 0.5, 0.5) * spec * light_intensity;

    // 6. Облака
    // Облака всегда видны (даже ночью они подсвечиваются изнутри или просто светлее)
    // Но в реальности они должны быть освещены солнцем.
    vec3 cloud_color = vec3(1.0, 1.0, 1.0) * cloud_mask;
    float cloud_alpha = cloud_mask * 0.8; // Делаем их полупрозрачными

    // Смешиваем: Сначала поверхность (день/ночь + блик), затем облака
    vec3 final_rgb = base_color * (0.7 + 0.3 * light_intensity) + specular_color;

    // Накладываем облака поверх, учитывая освещенность (облака подсвечиваются солнцем)
    float cloud_lighting = max(dot(N, L), 0.5); // Облака немного светятся в тени
    vec3 cloud_final = cloud_color * cloud_lighting;

    // Финальное смешивание (облака поверх земли)
    // Если облака очень густые, они перекрывают землю
    final_rgb = mix(final_rgb, cloud_final, cloud_mask * 0.5);

    // 7. Атмосферное свечение (Rim lighting / Fresnel)
    // Добавляем легкое голубое свечение по краям планеты
    vec3 atmosphere = vec3(0.3, 0.5, 1.0) * fresnel * light_intensity;
    final_rgb += atmosphere;

    out_color = vec4(final_rgb, 1.0);
}
