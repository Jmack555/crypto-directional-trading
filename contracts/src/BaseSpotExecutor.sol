// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Non-custodial, single-hop Uniswap v3 spot swap executor for Base.
/// @dev Users approve this contract for one swap; it pulls only amountIn, grants
///      the router an exact temporary allowance, and sends output directly back
///      to the caller. It does not hold user balances or custody private keys.
interface IERC20Minimal {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
}

interface ISwapRouter02 {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    function exactInputSingle(ExactInputSingleParams calldata params)
        external returns (uint256 amountOut);
}

contract BaseSpotExecutor {
    address public immutable router;
    uint256 public immutable deploymentChainId;
    uint256 private unlocked = 1;

    address public constant BASE_SWAP_ROUTER_02 = 0x2626664c2603336E57B271c5C0b26F421741e481;
    address public constant BASE_SEPOLIA_SWAP_ROUTER_02 = 0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4;
    uint256 public constant MAX_DEADLINE_WINDOW = 10 minutes;

    error UnsupportedChain();
    error InvalidRouter();
    error InvalidSwapParameters();
    error ExpiredOrExcessiveDeadline();
    error TokenCallFailed();
    error ReentrantCall();
    error InsufficientOutput(uint256 actual, uint256 minimum);
    error UnexpectedInputBalance();

    event SwapExecuted(
        address indexed trader,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint24 poolFee
    );

    constructor(address routerAddress) {
        if (block.chainid == 8453) {
            if (routerAddress != BASE_SWAP_ROUTER_02) revert InvalidRouter();
        } else if (block.chainid == 84532) {
            if (routerAddress != BASE_SEPOLIA_SWAP_ROUTER_02) revert InvalidRouter();
        } else {
            revert UnsupportedChain();
        }
        if (routerAddress.code.length == 0) revert InvalidRouter();
        router = routerAddress;
        deploymentChainId = block.chainid;
    }

    modifier nonReentrant() {
        if (unlocked != 1) revert ReentrantCall();
        unlocked = 2;
        _;
        unlocked = 1;
    }

    /// @notice Swap caller-owned ERC-20 tokens through one Uniswap v3 pool.
    /// @param tokenIn Input ERC-20 token address.
    /// @param tokenOut Output ERC-20 token address.
    /// @param amountIn Exact input amount in tokenIn base units.
    //// @param amountOutMinimum Quoter/oracle-derived minimum output; never zero.

    function swapExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOutMinimum,
        uint24 poolFee,
        uint256 deadline
    ) external nonReentrant returns (uint256 amountOut) {
        if (block.chainid != deploymentChainId) revert UnsupportedChain();
        if (
            tokenIn == address(0) || tokenOut == address(0) || tokenIn == tokenOut ||
            amountIn == 0 || amountOutMinimum == 0 ||
            (poolFee != 100 && poolFee != 500 && poolFee != 3000 && poolFee != 10000)
        ) revert InvalidSwapParameters();
        if (deadline < block.timestamp || deadline > block.timestamp + MAX_DEADLINE_WINDOW) {
            revert ExpiredOrExcessiveDeadline();
        }

        uint256 inputBefore = IERC20Minimal(tokenIn).balanceOf(address(this));
        uint256 outputBefore = IERC20Minimal(tokenOut).balanceOf(msg.sender);
        _safeTransferFrom(tokenIn, msg.sender, address(this), amountIn);
        uint256 received = IERC20Minimal(tokenIn).balanceOf(address(this)) - inputBefore;
        if (received == 0) revert UnexpectedInputBalance();

        _safeApprove(tokenIn, router, 0);
        _safeApprove(tokenIn, router, received);

        amountOut = ISwapRouter02(router).exactInputSingle(
            ISwapRouter02.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: poolFee,
                recipient: msg.sender,
                amountIn: received,
                amountOutMinimum: amountOutMinimum,
                sqrtPriceLimitX96: 0
            })
        );

        _safeApprove(tokenIn, router, 0);
        uint256 remainingInput = IERC20Minimal(tokenIn).balanceOf(address(this)) - inputBefore;
        if (remainingInput != 0) {
            _safeTransfer(tokenIn, msg.sender, remainingInput);
        }
        uint256 delivered = IERC20Minimal(tokenOut).balanceOf(msg.sender) - outputBefore;
        if (delivered < amountOutMinimum || delivered != amountOut) {
            revert InsufficientOutput(delivered, amountOutMinimum);
        }

        emit SwapExecuted(msg.sender, tokenIn, tokenOut, received, delivered, poolFee);
    }

    function _safeTransfer(address token, address to, uint256 amount) private {
        (bool ok, bytes memory data) = token.call(abi.encodeWithSelector(IERC20Minimal.transfer.selector, to, amount));
        if (!ok || (data.length != 0 && !abi.decode(data, (bool)))) revert TokenCallFailed();
    }

    function _safeTransferFrom(address token, address from, address to, uint256 amount) private {
        (bool ok, bytes memory data) = token.call(abi.encodeWithSelector(IERC20Minimal.transferFrom.selector, from, to, amount));
        if (!ok || (data.length != 0 && !abi.decode(data, (bool)))) revert TokenCallFailed();
    }

    function _safeApprove(address token, address spender, uint256 amount) private {
        (bool ok, bytes memory data) = token.call(abi.encodeWithSelector(IERC20Minimal.approve.selector, spender, amount));
        if (!ok || (data.length != 0 && !abi.decode(data, (bool)))) revert TokenCallFailed();
    }
}
