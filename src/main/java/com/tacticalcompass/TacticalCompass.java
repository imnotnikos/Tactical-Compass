package com.tacticalcompass;

import com.tacticalcompass.block.CommsRelayBlock;
import com.tacticalcompass.block.CommsRelayBlockEntity;
import com.tacticalcompass.item.TacticalCompassItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.EnumMap;
import java.util.Map;

@Mod(TacticalCompass.MODID)
public class TacticalCompass {
    public static final String MODID = "tacticalcompass";

    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, MODID);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES = DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, MODID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    public static final Map<Variant, RegistryObject<Block>> RELAYS = new EnumMap<>(Variant.class);
    public static final Map<Variant, RegistryObject<Item>> RELAY_ITEMS = new EnumMap<>(Variant.class);
    public static final Map<Variant, RegistryObject<Item>> COMPASSES = new EnumMap<>(Variant.class);

    static {
        for (Variant v : Variant.values()) {
            RegistryObject<Block> relay = BLOCKS.register("comms_relay_" + v.id, () -> new CommsRelayBlock(v,
                    BlockBehaviour.Properties.of().mapColor(v.mapColor).strength(2.5F, 6.0F).sound(SoundType.METAL)
                            .noOcclusion().lightLevel(s -> s.getValue(CommsRelayBlock.OPEN) ? 6 : 1)));
            RELAYS.put(v, relay);
            RELAY_ITEMS.put(v, ITEMS.register("comms_relay_" + v.id, () -> new BlockItem(relay.get(), new Item.Properties())));
            COMPASSES.put(v, ITEMS.register("tactical_compass_" + v.id, () -> new TacticalCompassItem(v, new Item.Properties().stacksTo(1))));
        }
    }

    public static final RegistryObject<BlockEntityType<CommsRelayBlockEntity>> RELAY_BE = BLOCK_ENTITIES.register("comms_relay",
            () -> BlockEntityType.Builder.of(CommsRelayBlockEntity::new,
                    RELAYS.values().stream().map(RegistryObject::get).toArray(Block[]::new)).build(null));

    public static final RegistryObject<CreativeModeTab> TAB = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.tacticalcompass"))
            .icon(() -> new ItemStack(COMPASSES.get(Variant.OLIVE).get()))
            .displayItems((params, out) -> {
                COMPASSES.values().forEach(i -> out.accept(i.get()));
                RELAY_ITEMS.values().forEach(i -> out.accept(i.get()));
            })
            .build());

    public TacticalCompass() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        BLOCKS.register(bus);
        ITEMS.register(bus);
        BLOCK_ENTITIES.register(bus);
        TABS.register(bus);
    }
}
