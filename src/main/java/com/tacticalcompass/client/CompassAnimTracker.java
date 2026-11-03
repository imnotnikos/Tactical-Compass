package com.tacticalcompass.client;

import com.tacticalcompass.item.TacticalCompassItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Client-side animation state for every player holding a compass: when it was equipped (drives
 * the flick-open) and how far it is raised (drives the scope pose). Works for remote players too,
 * since held items and "using item" state are synced by vanilla.
 */
public final class CompassAnimTracker {
    /** Ticks the compass spends rising into view (vanilla re-equip) before the lid flips, and the flip length. */
    public static final float RAISE_TICKS = 6.0F;
    public static final float FLICK_TICKS = 6.0F;

    public static final class HandAnim {
        Object key;
        long equipTick = Long.MIN_VALUE / 2;
        float scope, scopePrev;
        boolean soundPlayed = true;

        public float equipAge(float partialTick) {
            return (float) Math.min(10_000L, ticks - equipTick) + partialTick;
        }

        public float scope(float partialTick) {
            return Mth.lerp(partialTick, scopePrev, scope);
        }
    }

    private static final Map<Integer, HandAnim[]> STATE = new HashMap<>();
    private static long ticks;

    private CompassAnimTracker() {
    }

    @Nullable
    public static HandAnim get(Player player, InteractionHand hand) {
        HandAnim[] arr = STATE.get(player.getId());
        return arr == null ? null : arr[hand.ordinal()];
    }

    static void tick() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            STATE.clear();
            return;
        }
        ticks++;
        Set<Integer> seen = new HashSet<>();
        for (AbstractClientPlayer p : mc.level.players()) {
            seen.add(p.getId());
            HandAnim[] arr = STATE.computeIfAbsent(p.getId(), id -> new HandAnim[]{new HandAnim(), new HandAnim()});
            boolean local = p == mc.player;
            update(arr[0], p, InteractionHand.MAIN_HAND, local ? p.getInventory().selected : -1, local);
            update(arr[1], p, InteractionHand.OFF_HAND, -2, local);
        }
        STATE.keySet().retainAll(seen);
    }

    private record Key(Item item, int slot) {
    }

    private static void update(HandAnim h, Player p, InteractionHand hand, int slot, boolean local) {
        ItemStack stack = p.getItemInHand(hand);
        Object key = stack.getItem() instanceof TacticalCompassItem ? new Key(stack.getItem(), slot) : null;
        if (key != null && !Objects.equals(key, h.key)) {
            h.equipTick = ticks;
            h.soundPlayed = false;
            h.scope = h.scopePrev = 0.0F;
        }
        h.key = key;
        if (local && !h.soundPlayed && ticks - h.equipTick >= (long) RAISE_TICKS) {
            h.soundPlayed = true;
            p.playSound(SoundEvents.IRON_TRAPDOOR_OPEN, 0.25F, 2.0F);
        }
        h.scopePrev = h.scope;
        boolean using = key != null && p.isUsingItem() && p.getUsedItemHand() == hand;
        h.scope = Mth.approach(h.scope, using ? 1.0F : 0.0F, 0.2F);
    }
}
