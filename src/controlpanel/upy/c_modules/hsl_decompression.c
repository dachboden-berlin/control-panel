#include "py/dynruntime.h"

// --- Hue → RGB LUT (S=100%, L=50%) ---
static uint8_t hue_lut[256][3];

// Build hue LUT at module init
static void build_hue_lut(void) {
    for (int h = 0; h < 256; h++) {
        int hue = (h * 360) >> 8;
        int region = hue / 60;
        int remainder = (hue % 60) * 255 / 60;

        int r = 0, g = 0, b = 0;

        switch (region) {
            case 0: r = 255; g = remainder; b = 0; break;
            case 1: r = 255 - remainder; g = 255; b = 0; break;
            case 2: r = 0; g = 255; b = remainder; break;
            case 3: r = 0; g = 255 - remainder; b = 255; break;
            case 4: r = remainder; g = 0; b = 255; break;
            default: r = 255; g = 0; b = 255 - remainder; break;
        }

        hue_lut[h][0] = r;
        hue_lut[h][1] = g;
        hue_lut[h][2] = b;
    }
}

// --- Python-exposed function ---
static mp_obj_t uncompress_hsl_into(mp_obj_t buffer_obj, mp_obj_t compressed_obj) {
    mp_buffer_info_t buf_info;
    mp_buffer_info_t comp_info;

    mp_get_buffer_raise(buffer_obj, &buf_info, MP_BUFFER_WRITE);
    mp_get_buffer_raise(compressed_obj, &comp_info, MP_BUFFER_READ);

    uint8_t *out = (uint8_t *)buf_info.buf;
    const uint8_t *in = (const uint8_t *)comp_info.buf;
    size_t len = comp_info.len;

    if (len & 1) {
        mp_raise_ValueError(MP_ERROR_TEXT("input length must be even"));
    }

    size_t pixels = len >> 1;
    if (buf_info.len < pixels * 3) {
        mp_raise_ValueError(MP_ERROR_TEXT("buffer too small"));
    }

    for (size_t i = 0; i < pixels; i++) {
        uint8_t h = *in++;
        uint8_t l = *in++;

        const uint8_t *base = hue_lut[h];

        if (l < 128) {
            // Scale toward black
            uint16_t scale = l << 1;  // 0..255
            *out++ = (base[0] * scale) >> 8;
            *out++ = (base[1] * scale) >> 8;
            *out++ = (base[2] * scale) >> 8;
        } else {
            // Scale toward white
            uint16_t scale = (l - 128) << 1;  // 0..255
            *out++ = base[0] + (((255 - base[0]) * scale) >> 8);
            *out++ = base[1] + (((255 - base[1]) * scale) >> 8);
            *out++ = base[2] + (((255 - base[2]) * scale) >> 8);
        }
    }

    return mp_const_none;
}

// --- Segment lookup table ---
static const uint8_t segment_lut[32][2] = {
    {38, 10}, {31, 7}, {24, 7}, {14, 10},
    {7, 7}, {0, 7}, {65, 4}, {86, 4},
    {48, 5}, {53, 6}, {59, 6}, {69, 6},
    {75, 6}, {81, 5}, {94, 2}, {90, 2},
    {92, 2}, {110, 10}, {120, 7}, {127, 7},
    {134, 10}, {96, 7}, {103, 7}, {156, 4},
    {177, 4}, {160, 5}, {165, 6}, {171, 6},
    {150, 6}, {144, 6}, {181, 5}, {186, 2},
};

// --- get_pixel_buffer(buf, colorbuf) ---
static mp_obj_t get_pixel_buffer(mp_obj_t buf_obj, mp_obj_t colorbuf_obj) {
    mp_buffer_info_t buf_info;
    mp_buffer_info_t color_info;

    mp_get_buffer_raise(buf_obj, &buf_info, MP_BUFFER_WRITE);
    mp_get_buffer_raise(colorbuf_obj, &color_info, MP_BUFFER_READ);

    uint8_t *buf = (uint8_t *)buf_info.buf;
    const uint8_t *in = (const uint8_t *)color_info.buf;

    size_t pair_count = color_info.len >> 1;

    for (size_t segment = 0; segment < pair_count; segment++) {
        uint8_t h = *in++;
        uint8_t l = *in++;

        const uint8_t *base = hue_lut[h];
        uint8_t r, g, b;

        if (l < 128) {
            uint16_t scale = l << 1;
            r = (base[0] * scale) >> 8;
            g = (base[1] * scale) >> 8;
            b = (base[2] * scale) >> 8;
        } else {
            uint16_t scale = (l - 128) << 1;
            r = base[0] + (((255 - base[0]) * scale) >> 8);
            g = base[1] + (((255 - base[1]) * scale) >> 8);
            b = base[2] + (((255 - base[2]) * scale) >> 8);
        }

        size_t digit = segment >> 5;
        size_t offset = digit * (188 * 3);
        uint8_t seg_in_digit = segment & 31;

        uint8_t start = segment_lut[seg_in_digit][0];
        uint8_t count = segment_lut[seg_in_digit][1];

        uint8_t *out = buf + offset + (start * 3);

        for (uint8_t j = 0; j < count; j++) {
            *out++ = r;
            *out++ = g;
            *out++ = b;
        }
    }

    return buf_obj;
}


static MP_DEFINE_CONST_FUN_OBJ_2(get_pixel_buffer_obj, get_pixel_buffer);

static MP_DEFINE_CONST_FUN_OBJ_2(uncompress_hsl_into_obj, uncompress_hsl_into);

// --- Module init ---
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY

    build_hue_lut();

    mp_store_global(
        MP_QSTR_uncompress_hsl_into,
        MP_OBJ_FROM_PTR(&uncompress_hsl_into_obj)
    );

    mp_store_global(
    MP_QSTR_get_pixel_buffer,
    MP_OBJ_FROM_PTR(&get_pixel_buffer_obj)
    );

    MP_DYNRUNTIME_INIT_EXIT
}
