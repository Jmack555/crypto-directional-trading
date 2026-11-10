// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BaseSpotExecutor, ISwapRouter02} from "../src/BaseSpotExecutor.sol";

interface Vm {
    function chainId(uint256) external;
    function etch(address, bytes calldata) external;
    function prank(address) external;
    function expectRevert() external;
}

contract MockERC20 {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external { balanceOf[to] += amount; }
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }
    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "balance");
        require(allowance[from][msg.sender] >= amount, "allowance");
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract MockRouter is ISwapRouter02 {
    address public immutable outputToken;
    constructor(address token) { outputToken = token; }
    function exactInputSingle(ExactInputSingleParams calldata p) external returns (uint256) {
        uint256 output = p.amountIn * 2;
        require(output >= p.amountOutMinimum, "min out");
        require(MockERC20(outputToken).transfer(p.recipient, output), "transfer");
        return output;
    }
}

contract BaseSpotExecutorTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address private constant USER = address(0xBEEF);
    address private constant TEST_ROUTER = 0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4;
    MockERC20 private tokenIn;
    MockERC20 private tokenOut;
    BaseSpotExecutor private executor;

    function setUp() public {
        vm.chainId(84532);
        tokenIn = new MockERC20();
        tokenOut = new MockERC20();
        MockRouter implementation = new MockRouter(address(tokenOut));
        vm.etch(TEST_ROUTER, address(implementation).code);
        tokenOut.mint(TEST_ROUTER, 1_000_000);
        executor = new BaseSpotExecutor(TEST_ROUTER);
        tokenIn.mint(USER, 1000);
        vm.prank(USER);
        tokenIn.approve(address(executor), 1000);
    }

    function testSwapReturnsOutputToCallerAndResetsAllowance() public {
        vm.prank(USER);
        uint256 output = executor.swapExactInputSingle(
            address(tokenIn), address(tokenOut), 100, 190, 500, block.timestamp + 60
        );
        require(output == 200, "wrong output");
        require(tokenIn.balanceOf(USER) == 900, "input not pulled");
        require(tokenOut.balanceOf(USER) == 200, "output not delivered");
        require(tokenIn.allowance(address(executor), TEST_ROUTER) == 0, "router allowance remains");
        require(tokenIn.balanceOf(address(executor)) == 0, "executor retained input");
    }

    function testRejectsZeroMinimumOutput() public {
        vm.expectRevert();
        vm.prank(USER);
        executor.swapExactInputSingle(
            address(tokenIn), address(tokenOut), 100, 0, 500, block.timestamp + 60
        );
    }

    function testRejectsExpiredDeadline() public {
        vm.expectRevert();
        vm.prank(USER);
        executor.swapExactInputSingle(
            address(tokenIn), address(tokenOut), 100, 1, 500, block.timestamp - 1
        );
    }
}
