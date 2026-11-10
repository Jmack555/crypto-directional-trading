# BaseSpotExecutor

A minimal, non-custodial, single-hop ERC-20 spot-swap executor for Base using the official Uniswap v3 SwapRouter02 deployment. The contract is separate from the off-chain directional strategy. It does not calculate signals, fetch prices, hold keys, or decide whether a trade is profitable.

## Deployment targets

| Network | Chain ID | Router02 |
|---|---:|---|
| Base Sepolia | 84532 | `0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4` |
| Base mainnet | 8453 | `0x2626664c2603336E57B271c5C0b26F421741e481` |

The constructor rejects unsupported chains and any router address other than the corresponding official deployment. These addresses are taken from the [Uniswap Base deployments page](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments).

## Safety properties

- Caller approves this executor for a specific input amount; only that amount is pulled.
- Output is sent directly to the caller; no owner, admin, or withdrawal function exists.
- Router allowance is exact and reset to zero after the swap.
- `amountOutMinimum` must be nonzero and must be computed off-chain from a fresh quote/reference price plus a strict slippage policy.
- Deadline must be current and no more than 10 minutes ahead.
- Supported fee tiers are 0.01%, 0.05%, 0.30%, and 1.00%.
- Reentrancy guard; rejects zero addresses, identical tokens, and zero input.
- No arbitrary router, arbitrary calldata, flash-loan, owner sweep, or upgrade mechanism.

## Important limitations

This is an execution primitive, not a complete trading bot. The off-chain system must independently validate pool existence/liquidity, quote freshness, price impact, token decimals, token allowlists, token risk, and expected net profitability. A strict minimum output reduces price manipulation risk but does not guarantee protection from MEV or bad quotes. Do not route unknown or fee-on-transfer/rebasing tokens without explicit compatibility tests.

The contract has not yet been compiled, tested against a fork, formally verified, or audited in this environment. **Do not deploy to mainnet or fund it until the Foundry unit/integration suite, Base Sepolia fork/integration tests, static analysis, and an independent security review pass.**

## Build

Install Foundry, then from this directory:

```bash
forge build
forge test -vvv
```

## Deployment sequence

1. Run the full test suite on Base Sepolia and inspect the verified constructor bytecode/address.
2. Use a delicated wallet with no unrelated assets; never put a seed phrase or private key in this repository.
3. Deploy to Base Sepolia using the router address above and verify source on the explorer.
4. Test swaps with test tokens, strict nonzero minimum output, small amounts, and deliberately expired deadlines.
5. Only after independent review, deploy the identical source to Base mainnet with the Base router address.

A deployment script and tests are intentionally not represented as complete until they have been executed and verified.
