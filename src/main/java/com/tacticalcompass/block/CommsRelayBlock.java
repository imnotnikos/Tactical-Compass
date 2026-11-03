package com.tacticalcompass.block;

import com.tacticalcompass.TacticalCompass;
import com.tacticalcompass.Variant;
import com.tacticalcompass.item.TacticalCompassItem;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.SimpleWaterloggedBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

/** A rugged-case communications relay. Faces the placer; right-click opens/closes the case. */
public class CommsRelayBlock extends HorizontalDirectionalBlock implements EntityBlock, SimpleWaterloggedBlock {
    public static final BooleanProperty OPEN = BlockStateProperties.OPEN;
    public static final BooleanProperty WATERLOGGED = BlockStateProperties.WATERLOGGED;

    // the closed case box (model pixels, north-facing); used whether the lid is open or not
    private static final VoxelShape[] SHAPES = new VoxelShape[4];

    static {
        for (Direction d : Direction.Plane.HORIZONTAL) {
            SHAPES[d.get2DDataValue()] = shape(new double[]{1, 0, 2.5, 15, 6.4, 14}, d);
        }
    }

    private final Variant variant;

    public CommsRelayBlock(Variant variant, Properties props) {
        super(props);
        this.variant = variant;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(OPEN, false).setValue(WATERLOGGED, false));
    }

    public Variant variant() {
        return variant;
    }

    private static VoxelShape shape(double[] b, Direction facing) {
        double x0 = b[0], z0 = b[2], x1 = b[3], z1 = b[5];
        // rotate clockwise (seen from above) to match the blockstate y rotation
        for (int i = 0; i < (facing.get2DDataValue() + 2) % 4; i++) {
            double nx0 = 16 - z1, nx1 = 16 - z0, nz0 = x0, nz1 = x1;
            x0 = nx0; x1 = nx1; z0 = nz0; z1 = nz1;
        }
        return Block.box(x0, b[1], z0, x1, b[4], z1);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, OPEN, WATERLOGGED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState()
                .setValue(FACING, ctx.getHorizontalDirection().getOpposite())
                .setValue(WATERLOGGED, ctx.getLevel().getFluidState(ctx.getClickedPos()).getType() == Fluids.WATER);
    }

    @Override
    public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPES[state.getValue(FACING).get2DDataValue()];
    }

    @Override
    @SuppressWarnings("deprecation")
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
        // sneaking never touches the case (lets you place blocks against it), and the compass links instead
        if (player.isSecondaryUseActive() || player.getItemInHand(hand).getItem() instanceof TacticalCompassItem) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide) {
            boolean open = !state.getValue(OPEN);
            level.setBlock(pos, state.setValue(OPEN, open), Block.UPDATE_ALL);
            level.playSound(null, pos, open ? SoundEvents.IRON_TRAPDOOR_OPEN : SoundEvents.IRON_TRAPDOOR_CLOSE,
                    SoundSource.BLOCKS, 0.7F, open ? 1.15F : 1.0F);
            level.gameEvent(player, open ? GameEvent.CONTAINER_OPEN : GameEvent.CONTAINER_CLOSE, pos);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    @SuppressWarnings("deprecation")
    public FluidState getFluidState(BlockState state) {
        return state.getValue(WATERLOGGED) ? Fluids.WATER.getSource(false) : super.getFluidState(state);
    }

    @Override
    @SuppressWarnings("deprecation")
    public BlockState updateShape(BlockState state, Direction dir, BlockState neighbor, LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (state.getValue(WATERLOGGED)) {
            level.scheduleTick(pos, Fluids.WATER, Fluids.WATER.getTickDelay(level));
        }
        return super.updateShape(state, dir, neighbor, level, pos, neighborPos);
    }

    @Override
    @SuppressWarnings("deprecation")
    public BlockState rotate(BlockState state, Rotation rot) {
        return state.setValue(FACING, rot.rotate(state.getValue(FACING)));
    }

    @Override
    @SuppressWarnings("deprecation")
    public BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CommsRelayBlockEntity(pos, state);
    }

    @Nullable
    @Override
    @SuppressWarnings("unchecked")
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide && type == TacticalCompass.RELAY_BE.get()
                ? (BlockEntityTicker<T>) (BlockEntityTicker<CommsRelayBlockEntity>) CommsRelayBlockEntity::clientTick
                : null;
    }
}
