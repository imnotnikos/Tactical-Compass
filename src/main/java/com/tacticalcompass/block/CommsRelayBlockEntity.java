package com.tacticalcompass.block;

import com.tacticalcompass.TacticalCompass;
import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Holds the client-side lid animation. Openness walks toward the blockstate's target each tick,
 * so toggling mid-swing simply reverses from wherever the lid currently is.
 */
public class CommsRelayBlockEntity extends BlockEntity {
    private static final float SPEED = 0.1F;
    private float openness;
    private float prevOpenness;
    private boolean initialized;

    public CommsRelayBlockEntity(BlockPos pos, BlockState state) {
        super(TacticalCompass.RELAY_BE.get(), pos, state);
    }

    public static void clientTick(Level level, BlockPos pos, BlockState state, CommsRelayBlockEntity be) {
        float target = state.getValue(CommsRelayBlock.OPEN) ? 1.0F : 0.0F;
        if (!be.initialized) {
            // chunk just loaded: show the current state without animating
            be.openness = be.prevOpenness = target;
            be.initialized = true;
            return;
        }
        be.prevOpenness = be.openness;
        if (be.openness < target) {
            be.openness = Math.min(target, be.openness + SPEED);
        } else if (be.openness > target) {
            be.openness = Math.max(target, be.openness - SPEED);
        }
    }

    public float getOpenness(float partialTick) {
        if (!initialized) {
            return getBlockState().getValue(CommsRelayBlock.OPEN) ? 1.0F : 0.0F;
        }
        return Mth.lerp(partialTick, prevOpenness, openness);
    }
}
