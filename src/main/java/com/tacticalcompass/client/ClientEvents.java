package com.tacticalcompass.client;

import com.tacticalcompass.TacticalCompass;
import com.tacticalcompass.Variant;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.ModelEvent;
import net.minecraftforge.client.event.RenderLivingEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

public final class ClientEvents {
    /** Entity currently being rendered, so the item renderer knows whose compass it is drawing. */
    static LivingEntity renderingEntity;

    static final String[] COMPASS_PARTS = {"base", "lid", "popup", "needle", "card", "icon"};

    private ClientEvents() {
    }

    public static ResourceLocation compassModel(String part, Variant v) {
        return new ResourceLocation(TacticalCompass.MODID, "item/compass/" + part + "_" + v.id);
    }

    public static ResourceLocation relayModel(String part, Variant v) {
        return new ResourceLocation(TacticalCompass.MODID, "block/relay/" + part + "_" + v.id);
    }

    @Mod.EventBusSubscriber(modid = TacticalCompass.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class ModBus {
        @SubscribeEvent
        public static void registerModels(ModelEvent.RegisterAdditional event) {
            for (Variant v : Variant.values()) {
                for (String part : COMPASS_PARTS) {
                    event.register(compassModel(part, v));
                }
                event.register(relayModel("lid", v));
                event.register(relayModel("antenna", v));
            }
        }

        @SubscribeEvent
        public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
            event.registerBlockEntityRenderer(TacticalCompass.RELAY_BE.get(), CommsRelayRenderer::new);
        }
    }

    @Mod.EventBusSubscriber(modid = TacticalCompass.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
    public static final class ForgeBus {
        @SubscribeEvent
        public static void clientTick(TickEvent.ClientTickEvent event) {
            if (event.phase == TickEvent.Phase.END) {
                CompassAnimTracker.tick();
            }
        }

        @SubscribeEvent
        public static void preLiving(RenderLivingEvent.Pre<?, ?> event) {
            renderingEntity = event.getEntity();
        }

        @SubscribeEvent
        public static void postLiving(RenderLivingEvent.Post<?, ?> event) {
            renderingEntity = null;
        }
    }
}
