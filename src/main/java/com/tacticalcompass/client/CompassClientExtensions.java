package com.tacticalcompass.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

public final class CompassClientExtensions implements IClientItemExtensions {
    public static final CompassClientExtensions INSTANCE = new CompassClientExtensions();

    /** Third-person pose while reading the compass: arm raised in front of the face. */
    public static final HumanoidModel.ArmPose SCOPE_POSE = HumanoidModel.ArmPose.create("TACTICALCOMPASS_SCOPE", false,
            (model, entity, arm) -> {
                ModelPart part = arm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
                part.xRot = model.head.xRot - 1.3F - (entity.isCrouching() ? 0.26F : 0.0F);
                part.yRot = model.head.yRot + (arm == HumanoidArm.RIGHT ? -0.35F : 0.35F);
                part.zRot = 0.0F;
            });

    /** Vanilla's equip / swing progress for each arm this frame, captured for the renderer. */
    static final float[] EQUIP = new float[2];
    static final float[] SWING = new float[2];

    private CompassItemRenderer renderer;

    private CompassClientExtensions() {
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        if (renderer == null) {
            renderer = new CompassItemRenderer();
        }
        return renderer;
    }

    @Override
    public boolean applyForgeHandTransform(PoseStack poseStack, LocalPlayer player, HumanoidArm arm, ItemStack itemInHand,
                                           float partialTick, float equipProcess, float swingProcess) {
        // the renderer builds the whole first-person pose itself (needs lid/scope state)
        EQUIP[arm.ordinal()] = equipProcess;
        SWING[arm.ordinal()] = swingProcess;
        return true;
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return entity.isUsingItem() && entity.getUsedItemHand() == hand ? SCOPE_POSE : null;
    }
}
