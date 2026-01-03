#include "py/dynruntime.h"

// --- Precompute table at module init (256 × 3 bytes = 768 bytes) ---
static uint8_t rgb_lut[256][3];

// Function to initialize the lookup table
static void build_rgb_lut(void) {
    for (int byte = 0; byte < 256; byte++) {
        uint8_t r = (byte & 0xE0) >> 5;   // 3 bits
        uint8_t g = (byte & 0x1C) >> 2;   // 3 bits
        uint8_t b = (byte & 0x03);        // 2 bits

        // Expand bits into 8-bit color space
        r = (r << 5) | (r << 2) | (r >> 1);
        g = (g << 5) | (g << 2) | (g >> 1);
        b = (b << 6) | (b << 4) | (b << 2) | b;

        rgb_lut[byte][0] = r;
        rgb_lut[byte][1] = g;
        rgb_lut[byte][2] = b;
    }
}

// --- The main function exposed to Python ---
static mp_obj_t uncompress_rgb_into(mp_obj_t buffer_obj, mp_obj_t compressed_obj) {
    mp_buffer_info_t buf_info;
    mp_buffer_info_t comp_info;
    mp_get_buffer_raise(buffer_obj, &buf_info, MP_BUFFER_WRITE);
    mp_get_buffer_raise(compressed_obj, &comp_info, MP_BUFFER_READ);

    uint8_t *out = (uint8_t *)buf_info.buf;
    const uint8_t *in = (const uint8_t *)comp_info.buf;
    size_t n = comp_info.len;

    if (buf_info.len < 3 * n) {
        mp_raise_ValueError(MP_ERROR_TEXT("buffer too small"));
    }

    // Fast path using LUT
    for (size_t i = 0; i < n; i++) {
        const uint8_t *rgb = rgb_lut[in[i]];
        *out++ = rgb[0];
        *out++ = rgb[1];
        *out++ = rgb[2];
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(uncompress_rgb_into_obj, uncompress_rgb_into);

// --- Module init function ---
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY

    // Initialize the lookup table once when the module is imported
    build_rgb_lut();

    mp_store_global(MP_QSTR_uncompress_rgb_into, MP_OBJ_FROM_PTR(&uncompress_rgb_into_obj));

    MP_DYNRUNTIME_INIT_EXIT
}
