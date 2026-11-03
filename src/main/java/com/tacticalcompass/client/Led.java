package com.tacticalcompass.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import com.tacticalcompass.TacticalCompass;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import org.joml.Matrix4f;

/**
 * Emissive 7-segment LED digits drawn in a local 2D frame (x right, y up, z out of the face).
 * Segments are the classic pointed hexagons with small gaps between them; unlit segments show as
 * very faint ghosts like a real display.
 */
final class Led {
    private static final ResourceLocation TEX = new ResourceLocation(TacticalCompass.MODID, "textures/misc/led.png");
    // bit order: a b c d e f g
    private static final int[] DIGITS = {0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F};
    static final int DASH = 0x40;

    private final VertexConsumer vc;
    private final Matrix4f m;
    private final int on, ghost;

    Led(MultiBufferSource buffers, Matrix4f m, int rgb) {
        this.vc = buffers.getBuffer(RenderType.text(TEX));
        this.m = m;
        this.on = rgb;
        int r = (rgb >> 16) & 255, g = (rgb >> 8) & 255, b = rgb & 255;
        this.ghost = ((10 + r / 14) << 16) | ((10 + g / 14) << 8) | (10 + b / 14);
    }

    static int mask(int digit) {
        return DIGITS[digit];
    }

    /** One digit with its bottom-left corner at (x, y), segment width w by total height h. */
    void digit(float x, float y, float w, float h, int mask) {
        float t = w * 0.22F;          // segment thickness
        float g = t * 0.22F;          // gap between segments
        float mid = y + h / 2;
        float l = x + t / 2, r = x + w - t / 2;   // vertical segment centre lines
        float top = y + h - t / 2, bot = y + t / 2;
        horizontal(l + g, r - g, top, t, (mask & 0x01) != 0);   // a
        vertical(r, mid + g, top - g, t, (mask & 0x02) != 0);   // b
        vertical(r, bot + g, mid - g, t, (mask & 0x04) != 0);   // c
        horizontal(l + g, r - g, bot, t, (mask & 0x08) != 0);   // d
        vertical(l, bot + g, mid - g, t, (mask & 0x10) != 0);   // e
        vertical(l, mid + g, top - g, t, (mask & 0x20) != 0);   // f
        horizontal(l + g, r - g, mid, t, (mask & 0x40) != 0);   // g
    }

    /** Two square dots for the HH:MM separator, sized to match a digit of height h. */
    void colon(float x, float y, float h, boolean lit) {
        float t = h * 0.12F;
        square(x, y + h * 0.28F, t, lit);
        square(x, y + h * 0.62F, t, lit);
    }

    /** Small lit square (degree mark, indicator lamp). */
    void square(float x, float y, float size, boolean lit) {
        int c = lit ? on : ghost;
        quad(x, y, x + size, y, x + size, y + size, x, y + size, c);
    }

    void triangle(float x0, float y0, float x1, float y1, float x2, float y2) {
        quad(x0, y0, x1, y1, x2, y2, x2, y2, on);
    }

    private void horizontal(float x0, float x1, float y, float t, boolean lit) {
        float ht = t / 2;
        int c = lit ? on : ghost;
        // pointed hexagon split into two convex quads
        quad(x0, y, x0 + ht, y - ht, x1 - ht, y - ht, x1, y, c);
        quad(x0, y, x1, y, x1 - ht, y + ht, x0 + ht, y + ht, c);
    }

    private void vertical(float x, float y0, float y1, float t, boolean lit) {
        float ht = t / 2;
        int c = lit ? on : ghost;
        quad(x, y0, x + ht, y0 + ht, x + ht, y1 - ht, x, y1, c);
        quad(x, y0, x, y1, x - ht, y1 - ht, x - ht, y0 + ht, c);
    }

    private void quad(float x0, float y0, float x1, float y1, float x2, float y2, float x3, float y3, int rgb) {
        // both windings so it shows regardless of face culling
        v(x0, y0, rgb);
        v(x1, y1, rgb);
        v(x2, y2, rgb);
        v(x3, y3, rgb);
        v(x3, y3, rgb);
        v(x2, y2, rgb);
        v(x1, y1, rgb);
        v(x0, y0, rgb);
    }

    private void v(float x, float y, int rgb) {
        vc.vertex(m, x, y, 0.02F).color((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255, 255)
                .uv(0.5F, 0.5F).uv2(LightTexture.FULL_BRIGHT).endVertex();
    }
}
