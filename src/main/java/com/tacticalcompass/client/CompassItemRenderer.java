package com.tacticalcompass.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.tacticalcompass.Variant;
import com.tacticalcompass.item.TacticalCompassItem;
import net.minecraft.Util;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.GlobalPos;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Renders the tactical compass as a rig of baked parts (base, rotating card, needle, hinged lid,
 * pop-up heading module) plus emissive LED readouts. Everything is drawn on the item itself.
 */
public class CompassItemRenderer extends BlockEntityWithoutLevelRenderer {
    // model geometry in pixels with the lid closed; mirrors tools/gen_assets.py
    private static final float DIAL_X = 8.0F / 16, DIAL_Z = 8.5F / 16;
    private static final float HINGE_Y = 2.0F / 16, HINGE_Z = 2.0F / 16;
    private static final float LID_OPEN = 100.0F;
    private static final float POP_TRAVEL = 1.6F;
    private static final Vector3f CENTER = new Vector3f(8.0F / 16, 1.0F / 16, 8.5F / 16);
    private static final Vector3f SIGHT = new Vector3f(8.0F / 16, 3.2F / 16, 10.25F / 16);

    // first-person poses (view space, blocks). Hold: squarely in front of the hand, turned slightly
    // toward screen centre and tipped up so dial, time and lid all face the eye.
    private static final float HOLD_X = 0.30F, HOLD_Y = -0.36F, HOLD_Z = -0.64F;
    private static final float HOLD_YAW = -8.0F, HOLD_TILT = 50.0F, HOLD_SCALE = 0.48F;
    // Raised: closer and ~1.5x bigger; the crosshair sits in the lid's sight window with the
    // heading module just above it, the time display and dial below.
    private static final float SCOPE_TILT = 52.0F, SCOPE_LID = 150.0F, SCOPE_SCALE = 0.48F;
    private static final float SCOPE_DIST = 0.56F;

    private static final class Rig {
        float heading, needle, lid = LID_OPEN, popup, popScale;
        boolean linked, lost;
    }

    public CompassItemRenderer() {
        super(Minecraft.getInstance().getBlockEntityRenderDispatcher(), Minecraft.getInstance().getEntityModels());
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext ctx, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        if (!(stack.getItem() instanceof TacticalCompassItem compass)) {
            return;
        }
        Variant v = compass.variant();
        if (ctx == ItemDisplayContext.GUI || ctx == ItemDisplayContext.FIXED) {
            // inventory sprite in slots and item frames, like vanilla flat items
            renderPart("icon", v, stack, pose, buffers, light, overlay);
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        float pt = mc.getFrameTime();

        LivingEntity holder = null;
        HumanoidArm arm = null;
        if (ctx.firstPerson()) {
            holder = mc.player;
            arm = ctx == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND ? HumanoidArm.RIGHT : HumanoidArm.LEFT;
        } else if (ctx == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND || ctx == ItemDisplayContext.THIRD_PERSON_LEFT_HAND
                || ctx == ItemDisplayContext.HEAD) {
            holder = ClientEvents.renderingEntity;
            if (ctx != ItemDisplayContext.HEAD) {
                arm = ctx == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND ? HumanoidArm.RIGHT : HumanoidArm.LEFT;
            }
        }
        InteractionHand hand = holder != null && arm != null
                ? (arm == holder.getMainArm() ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND) : null;
        CompassAnimTracker.HandAnim anim = holder instanceof Player p && hand != null ? CompassAnimTracker.get(p, hand) : null;

        Rig rig = new Rig();
        float scope = anim != null ? smooth(anim.scope(pt)) : 0.0F;
        float age = anim != null ? anim.equipAge(pt) : 1000.0F;
        rig.lid = flickLid(age);
        rig.popup = scope;
        rig.popScale = scope <= 0.55F ? 0.0F : easeOutBack((scope - 0.55F) / 0.45F);

        // heading of the compass body (0 = north, clockwise) and where it sits in the world
        float yaw = 180.0F;
        Vec3 origin = null;
        if (holder != null) {
            if (ctx.firstPerson()) {
                yaw = holder.getViewYRot(pt);
            } else if (holder.isUsingItem() || ctx == ItemDisplayContext.HEAD) {
                yaw = Mth.rotLerp(pt, holder.yHeadRotO, holder.yHeadRot);
            } else {
                yaw = Mth.rotLerp(pt, holder.yBodyRotO, holder.yBodyRot);
            }
            origin = holder.getPosition(pt);
        }
        rig.heading = Mth.positiveModulo(yaw + 180.0F, 360.0F);

        float bearing = 0.0F;
        GlobalPos link = TacticalCompassItem.getLink(stack);
        Level level = mc.level;
        if (link != null && level != null && origin != null) {
            if (link.dimension().equals(level.dimension())) {
                double dx = link.pos().getX() + 0.5 - origin.x;
                double dz = link.pos().getZ() + 0.5 - origin.z;
                bearing = (float) Math.toDegrees(Math.atan2(dx, -dz));
                rig.linked = true;
            } else {
                // relay is in another dimension: needle hunts aimlessly, like a lodestone compass
                double t = Util.getMillis() / 1000.0;
                bearing = rig.heading + (float) (t * 140.0 + 40.0 * Math.sin(t * 2.3));
                rig.lost = true;
            }
        }
        rig.needle = rig.heading - bearing;

        pose.pushPose();
        if (ctx.firstPerson()) {
            pose.translate(0.5F, 0.5F, 0.5F); // undo ItemRenderer's centring; we work in view space
            firstPersonPose(pose, arm, anim, scope, age, rig);
        } else {
            if (ctx == ItemDisplayContext.GROUND) {
                rig.lid = 0.0F;
            }
            pose.translate(0.0F, 6.0F / 16, -0.5F / 16);
        }
        renderRig(stack, v, rig, pose, buffers, light, overlay, level);
        pose.popPose();
    }

    private static void firstPersonPose(PoseStack pose, HumanoidArm arm, CompassAnimTracker.HandAnim anim,
                                        float scope, float age, Rig rig) {
        float side = arm == HumanoidArm.RIGHT ? 1.0F : -1.0F;
        float equip = CompassClientExtensions.EQUIP[arm.ordinal()];
        float swing = CompassClientExtensions.SWING[arm.ordinal()];

        Vector3f holdPos = new Vector3f(side * HOLD_X, HOLD_Y - equip * 0.6F, HOLD_Z);
        if (swing > 0.0F) {
            float sq = Mth.sqrt(swing);
            float k = 1.0F - scope;
            holdPos.add(side * -0.25F * Mth.sin(sq * Mth.PI) * k, 0.12F * Mth.sin(sq * Mth.TWO_PI) * k, -0.12F * Mth.sin(swing * Mth.PI) * k);
        }
        Quaternionf holdRot = new Quaternionf().rotateY(rad(side * HOLD_YAW)).rotateX(rad(HOLD_TILT));

        // raised pose: put the sight window's crosshair exactly on the screen centre
        Quaternionf scopeRot = new Quaternionf().rotateX(rad(SCOPE_TILT));
        Vector3f sight = lidPoint(SIGHT, SCOPE_LID).sub(CENTER).mul(SCOPE_SCALE);
        scopeRot.transform(sight);
        Vector3f scopePos = new Vector3f(0.0F, 0.0F, -SCOPE_DIST).sub(sight);

        Vector3f pos = holdPos.lerp(scopePos, scope);
        Quaternionf rot = holdRot.slerp(scopeRot, scope);
        float scale = Mth.lerp(scope, HOLD_SCALE, SCOPE_SCALE);
        rig.lid = Mth.lerp(scope, rig.lid, SCOPE_LID);

        pose.translate(pos.x, pos.y, pos.z);
        pose.mulPose(rot);
        pose.scale(scale, scale, scale);
        pose.translate(-CENTER.x, -CENTER.y, -CENTER.z);
    }

    private void renderRig(ItemStack stack, Variant v, Rig rig, PoseStack pose, MultiBufferSource buffers,
                           int light, int overlay, Level level) {
        renderPart("base", v, stack, pose, buffers, light, overlay);

        pose.pushPose();
        aboutDial(pose, rig.heading);
        renderPart("card", v, stack, pose, buffers, light, overlay);
        pose.popPose();

        pose.pushPose();
        aboutDial(pose, rig.needle);
        renderPart("needle", v, stack, pose, buffers, light, overlay);
        pose.popPose();

        // base LEDs: lubber index and link indicator (local x = model x, local y = -model z)
        pose.pushPose();
        pose.scale(1.0F / 16, 1.0F / 16, 1.0F / 16);
        pose.translate(0.0F, 2.6F, 0.0F);
        pose.mulPose(Axis.XP.rotationDegrees(-90.0F));
        Led base = new Led(buffers, pose.last().pose(), v.led);
        base.triangle(7.7F, -4.12F, 8.3F, -4.12F, 8.0F, -4.62F);
        long ms = Util.getMillis();
        boolean linkLit = rig.linked ? (ms / 1600) % 8 != 0 : rig.lost && (ms / 150) % 2 == 0;
        base.square(11.15F, -13.15F, 0.55F, linkLit);
        pose.popPose();

        pose.pushPose();
        pose.translate(0.0F, HINGE_Y, HINGE_Z);
        pose.mulPose(Axis.XP.rotationDegrees(-rig.lid));
        pose.translate(0.0F, -HINGE_Y, -HINGE_Z);
        renderPart("lid", v, stack, pose, buffers, light, overlay);

        pose.pushPose();
        pose.translate(0.0F, 0.0F, rig.popup * POP_TRAVEL / 16);
        renderPart("popup", v, stack, pose, buffers, light, overlay);
        if (rig.popScale > 0.01F) {
            drawHeading(pose, buffers, v, rig);
        }
        pose.popPose();

        if (rig.lid > 20.0F && level != null) {
            drawTime(pose, buffers, v, level);
        }
        pose.popPose();
    }

    /** Lid-inner-face frame: local x = model x, local y = model z (up when open), out = -y. */
    private static void lidFace(PoseStack pose, float planeY) {
        pose.scale(1.0F / 16, 1.0F / 16, 1.0F / 16);
        pose.translate(0.0F, planeY, 0.0F);
        pose.mulPose(Axis.XP.rotationDegrees(90.0F));
    }

    private static void drawTime(PoseStack pose, MultiBufferSource buffers, Variant v, Level level) {
        // display window on the lid's inner face: x 4.45..11.55, z 4.4..6.6 (lid closed coords)
        pose.pushPose();
        lidFace(pose, 2.6F);
        Led led = new Led(buffers, pose.last().pose(), v.led);
        float h = 1.6F, w = 0.95F, pitch = 1.3F, colonGap = 0.6F;
        float total = 4 * pitch - (pitch - w) + colonGap;
        float x = 8.0F - total / 2, y = 5.5F - h / 2;
        boolean fixed = level.dimensionType().hasFixedTime();
        int ticks = (int) ((level.getDayTime() + 6000L) % 24000L);
        int hours = ticks / 1000, minutes = (ticks % 1000) * 60 / 1000;
        int[] d = {hours / 10, hours % 10, minutes / 10, minutes % 10};
        for (int i = 0; i < 4; i++) {
            float dx = x + i * pitch + (i >= 2 ? colonGap : 0.0F);
            led.digit(dx, y, w, h, fixed ? Led.DASH : Led.mask(d[i]));
        }
        float colonX = x + 2 * pitch - (pitch - w) / 2 + colonGap / 2 - h * 0.06F;
        led.colon(colonX, y, h, !fixed && (Util.getMillis() / 500) % 2 == 0);
        pose.popPose();
    }

    private static void drawHeading(PoseStack pose, MultiBufferSource buffers, Variant v, Rig rig) {
        // display window on the pop-up module: x 6.4..9.6, z 12.6..13.5 (before the pop-up slide)
        pose.pushPose();
        lidFace(pose, 2.75F);
        float cx = 8.0F, cy = 13.05F;
        pose.translate(cx, cy, 0.0F);
        pose.scale(rig.popScale, rig.popScale, 1.0F);
        pose.translate(-cx, -cy, 0.0F);
        Led led = new Led(buffers, pose.last().pose(), v.led);
        int hdg = Math.round(rig.heading) % 360;
        int[] d = {hdg / 100, hdg / 10 % 10, hdg % 10};
        float h = 0.72F, w = 0.44F, pitch = 0.6F, deg = 0.13F;
        float total = 3 * pitch - (pitch - w) + 0.08F + deg;
        float x = cx - total / 2, y = cy - h / 2;
        for (int i = 0; i < 3; i++) {
            led.digit(x + i * pitch, y, w, h, Led.mask(d[i]));
        }
        led.square(x + 3 * pitch - (pitch - w) + 0.08F, y + h - deg, deg, true); // degree mark
        pose.popPose();
    }

    private static void aboutDial(PoseStack pose, float degrees) {
        pose.translate(DIAL_X, 0.0F, DIAL_Z);
        pose.mulPose(Axis.YP.rotationDegrees(degrees));
        pose.translate(-DIAL_X, 0.0F, -DIAL_Z);
    }

    private static Vector3f lidPoint(Vector3f p, float lid) {
        Vector3f q = new Vector3f(p).sub(0.0F, HINGE_Y, HINGE_Z);
        new Quaternionf().rotateX(rad(-lid)).transform(q);
        return q.add(0.0F, HINGE_Y, HINGE_Z);
    }

    private static void renderPart(String part, Variant v, ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        Minecraft mc = Minecraft.getInstance();
        BakedModel model = mc.getModelManager().getModel(ClientEvents.compassModel(part, v));
        mc.getItemRenderer().renderModelLists(model, stack, light, overlay, pose, buffers.getBuffer(Sheets.cutoutBlockSheet()));
    }

    /** Lid angle after equipping: shut while the compass rises into view, then flips up with a small overshoot. */
    private static float flickLid(float age) {
        float t = (age - CompassAnimTracker.RAISE_TICKS) / CompassAnimTracker.FLICK_TICKS;
        if (t <= 0.0F) {
            return 0.0F;
        }
        return LID_OPEN * easeOutBack(t);
    }

    private static float smooth(float t) {
        return t * t * (3.0F - 2.0F * t);
    }

    private static float easeOutBack(float t) {
        t = Mth.clamp(t, 0.0F, 1.0F) - 1.0F;
        return 1.0F + 2.70158F * t * t * t + 1.70158F * t * t;
    }

    private static float rad(float deg) {
        return deg * Mth.DEG_TO_RAD;
    }
}
