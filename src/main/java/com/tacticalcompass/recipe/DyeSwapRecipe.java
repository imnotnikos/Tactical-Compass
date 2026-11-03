package com.tacticalcompass.recipe;

import com.tacticalcompass.TacticalCompass;
import com.tacticalcompass.Variant;
import net.minecraft.core.RegistryAccess;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingBookCategory;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;
import net.minecraftforge.registries.RegistryObject;
import org.jetbrains.annotations.Nullable;

import java.util.Map;

/**
 * Re-dyes a compass or relay: one item plus one dye (black / green / brown) in any grid.
 * Keeps the item's data (e.g. a compass's relay link) and refuses to dye an item into the
 * colourway it already has.
 */
public class DyeSwapRecipe extends CustomRecipe {
    // keep in sync with RECIPE_DYES in tools/gen_assets.py
    private static final Map<Item, Variant> DYES = Map.of(
            Items.BLACK_DYE, Variant.BLACK,
            Items.GREEN_DYE, Variant.OLIVE,
            Items.BROWN_DYE, Variant.CAMO);

    public DyeSwapRecipe(ResourceLocation id, CraftingBookCategory category) {
        super(id, category);
    }

    private record Match(ItemStack item, Map<Variant, RegistryObject<Item>> family, Variant target) {
    }

    @Nullable
    private static Match find(CraftingContainer grid) {
        ItemStack target = null;
        Map<Variant, RegistryObject<Item>> family = null;
        Variant dye = null;
        for (int i = 0; i < grid.getContainerSize(); i++) {
            ItemStack s = grid.getItem(i);
            if (s.isEmpty()) {
                continue;
            }
            Map<Variant, RegistryObject<Item>> fam = familyOf(s.getItem());
            if (fam != null && target == null) {
                target = s;
                family = fam;
            } else if (DYES.containsKey(s.getItem()) && dye == null) {
                dye = DYES.get(s.getItem());
            } else {
                return null;
            }
        }
        if (target == null || dye == null || family.get(dye).get() == target.getItem()) {
            return null;
        }
        return new Match(target, family, dye);
    }

    @Nullable
    private static Map<Variant, RegistryObject<Item>> familyOf(Item item) {
        for (Map<Variant, RegistryObject<Item>> fam : java.util.List.of(TacticalCompass.COMPASSES, TacticalCompass.RELAY_ITEMS)) {
            for (RegistryObject<Item> ro : fam.values()) {
                if (ro.get() == item) {
                    return fam;
                }
            }
        }
        return null;
    }

    @Override
    public boolean matches(CraftingContainer grid, Level level) {
        return find(grid) != null;
    }

    @Override
    public ItemStack assemble(CraftingContainer grid, RegistryAccess access) {
        Match m = find(grid);
        if (m == null) {
            return ItemStack.EMPTY;
        }
        ItemStack out = new ItemStack(m.family().get(m.target()).get());
        if (m.item().getTag() != null) {
            out.setTag(m.item().getTag().copy());
        }
        return out;
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 2;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return TacticalCompass.DYE_SWAP.get();
    }
}
