package com.tacticalcompass.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.tacticalcompass.block.CommsRelayBlock;
import com.tacticalcompass.block.CommsRelayBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.client.model.data.ModelData;

/** Draws the relay's hinged lid and folding antenna; the rest of the case is a static block model. */
public class CommsRelayRenderer implements BlockEntityRenderer<CommsRelayBlockEntity> {
    private static final float LID_HINGE_Y = 4.5F / 16, LID_HINGE_Z = 14.0F / 16;
    private static final float ANT_PIVOT_Y = 6.1F / 16, ANT_PIVOT_Z = 11.3F / 16;

    public CommsRelayRenderer(BlockEntityRendererProvider.Context ctx) {
    }

    @Override
    public void render(CommsRelayBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        BlockState state = be.getBlockState();
        if (!(state.getBlock() instanceof CommsRelayBlock relay)) {
            return;
        }
        float open = be.getOpenness(partialTick);
        open = 1.0F - (1.0F - open) * (1.0F - open) * (1.0F - open); // chest-style ease, continuous so it reverses cleanly
        float closedAngle = -90.0F * (1.0F - open);

        pose.pushPose();
        pose.translate(0.5F, 0.0F, 0.5F);
        pose.mulPose(Axis.YP.rotationDegrees(180.0F - state.getValue(CommsRelayBlock.FACING).toYRot()));
        pose.translate(-0.5F, 0.0F, -0.5F);

        hinged(pose, buffers, light, overlay, ClientEvents.relayModel("antenna", relay.variant()), ANT_PIVOT_Y, ANT_PIVOT_Z, closedAngle);
        hinged(pose, buffers, light, overlay, ClientEvents.relayModel("lid", relay.variant()), LID_HINGE_Y, LID_HINGE_Z, closedAngle);
        pose.popPose();
    }

    private static void hinged(PoseStack pose, MultiBufferSource buffers, int light, int overlay,
                               net.minecraft.resources.ResourceLocation model, float py, float pz, float angle) {
        Minecraft mc = Minecraft.getInstance();
        BakedModel baked = mc.getModelManager().getModel(model);
        pose.pushPose();
        pose.translate(0.0F, py, pz);
        pose.mulPose(Axis.XP.rotationDegrees(angle));
        pose.translate(0.0F, -py, -pz);
        mc.getBlockRenderer().getModelRenderer().renderModel(pose.last(), buffers.getBuffer(Sheets.cutoutBlockSheet()), null,
                baked, 1.0F, 1.0F, 1.0F, light, overlay, ModelData.EMPTY, Sheets.cutoutBlockSheet());
        pose.popPose();
    }
}
