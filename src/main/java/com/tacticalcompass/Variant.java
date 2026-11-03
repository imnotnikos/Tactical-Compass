package com.tacticalcompass;

import net.minecraft.world.level.material.MapColor;

/** Colour schemes shared by the compass and the relay. */
public enum Variant {
    BLACK("black", 0x2E96FF, MapColor.COLOR_BLACK),
    OLIVE("olive", 0xFF2E22, MapColor.COLOR_GREEN),
    CAMO("camo", 0x3CFF60, MapColor.PLANT);

    public final String id;
    /** LED colour, 0xRRGGBB. */
    public final int led;
    public final MapColor mapColor;

    Variant(String id, int led, MapColor mapColor) {
        this.id = id;
        this.led = led;
        this.mapColor = mapColor;
    }
}
