// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BaseSpotExecutor} from "../src/BaseSpotExecutor.sol";

interface VmDeploy {
    function envUint(string calldata name) external returns (uint256);
    function startBroadcast(uint256 privateKey) external;
    function stopBroadcast() external;
}

/// @notice Deploys the fixed-router executor on Base Sepolia or Base mainnet.
/// @dev The key is read from the local Foundry environment; never commit it.
contract DeployBaseSpotExecutor {
    VmDeploy private constant vm =
        VmDeploy(address(uint160(uint256(keccak256("hevm cheat code")))));

    address private constant BASE_ROUTER =
        0x2626664c2603336E57B271c5C0b26F421741e481;
    address private constant BASE_SEPOLIA_ROUTER =
        0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4;

    error UnsupportedDeploymentChain();

    function run() external returns (BaseSpotExecutor deployed) {
        address router;
        if (block.chainid == 8453) {
            router = BASE_ROUTER;
        } else if (block.chainid == 84532) {
            router = BASE_SEPOLIA_ROUTER;
        } else {
            revert UnsupportedDeploymentChain();
        }

        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(privateKey);
        deployed = new BaseSpotExecutor(router);
        vm.stopBroadcast();
    }
}
