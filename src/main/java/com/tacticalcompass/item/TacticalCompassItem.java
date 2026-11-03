package com.tacticalcompass.item;

import com.tacticalcompass.Variant;
import com.tacticalcompass.block.CommsRelayBlock;
import com.tacticalcompass.client.CompassClientExtensions;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import org.jetbrains.annotations.Nullable;

import java.util.function.Consumer;

/**
 * Flip-up military compass. Right-click a comms relay to link (or unlink) it; hold right-click
 * anywhere else to raise it for reading. All readouts are drawn on the item model client-side.
 */
public class TacticalCompassItem extends Item {
    private static final String TAG_POS = "RelayPos";
    private static final String TAG_DIM = "RelayDim";

    private final Variant variant;

    public TacticalCompassItem(Variant variant, Properties props) {
        super(props);
        this.variant = variant;
    }

    public Variant variant() {
        return variant;
    }

    @Nullable
    public static GlobalPos getLink(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_POS) || !tag.contains(TAG_DIM)) {
            return null;
        }
        ResourceLocation dim = ResourceLocation.tryParse(tag.getString(TAG_DIM));
        if (dim == null) {
            return null;
        }
        return GlobalPos.of(ResourceKey.create(Registries.DIMENSION, dim), NbtUtils.readBlockPos(tag.getCompound(TAG_POS)));
    }

    private static void setLink(ItemStack stack, @Nullable GlobalPos link) {
        CompoundTag tag = stack.getOrCreateTag();
        if (link == null) {
            tag.remove(TAG_POS);
            tag.remove(TAG_DIM);
            if (tag.isEmpty()) {
                stack.setTag(null);
            }
        } else {
            tag.put(TAG_POS, NbtUtils.writeBlockPos(link.pos()));
            tag.putString(TAG_DIM, link.dimension().location().toString());
        }
    }

    @Override
    public InteractionResult useOn(UseOnContext ctx) {
        Level level = ctx.getLevel();
        BlockPos pos = ctx.getClickedPos();
        Player player = ctx.getPlayer();
        if (!(level.getBlockState(pos).getBlock() instanceof CommsRelayBlock)
                || (player != null && player.isSecondaryUseActive())) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide) {
            ItemStack stack = ctx.getItemInHand();
            GlobalPos target = GlobalPos.of(level.dimension(), pos.immutable());
            boolean unlink = target.equals(getLink(stack));
            setLink(stack, unlink ? null : target);
            level.playSound(null, pos, SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 1.0F, unlink ? 0.6F : 1.25F);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        player.startUsingItem(hand);
        level.playSound(player, player.getX(), player.getY(), player.getZ(), SoundEvents.SPYGLASS_USE, SoundSource.PLAYERS, 0.7F, 1.35F);
        return InteractionResultHolder.consume(player.getItemInHand(hand));
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
        level.playSound(entity instanceof Player p ? p : null, entity.getX(), entity.getY(), entity.getZ(),
                SoundEvents.SPYGLASS_STOP_USING, SoundSource.PLAYERS, 0.7F, 1.35F);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.NONE;
    }

    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        if (level.isClientSide || level.getGameTime() % 20 != 0) {
            return;
        }
        GlobalPos link = getLink(stack);
        // forget relays that were broken (only checkable when their chunk is loaded)
        if (link != null && link.dimension().equals(level.dimension()) && level.isLoaded(link.pos())
                && !(level.getBlockState(link.pos()).getBlock() instanceof CommsRelayBlock)) {
            setLink(stack, null);
        }
    }

    @Override
    public boolean shouldCauseReequipAnimation(ItemStack oldStack, ItemStack newStack, boolean slotChanged) {
        return slotChanged || oldStack.getItem() != newStack.getItem();
    }

    @Override
    public void initializeClient(Consumer<IClientItemExtensions> consumer) {
        consumer.accept(CompassClientExtensions.INSTANCE);
    }
}
