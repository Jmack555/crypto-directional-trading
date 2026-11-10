# BaseSpotExecutor

A minimal, non-custodial, single-hop ERC-20 spot-swap executor for Base using
the official Uniswap v3 SwapRouter02 deployment. The contract is separate from
the off-chain directional strategy. It does not calculate signals, fetch
prices, hold keys, or decide whether a trade is profitable.

## Deployment targets

| Network | Chain ID | Router02 |
|---|---:|---|
| Base Sepolia | 84532 | `0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4` |
| Base mainnet | 8453 | `0x2626664c2603336E57B271c5C0b26F421741e481` |

Addresses are checked against the official
[Uniswap Base deployments page](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments).
Uniswap currently documents Universal Router as its preferred general-purpose
entrypoint; this project deliberately uses the narrower v3 SwapRouter02
interface and supports only v3 single-pool swaps.

## Safety properties

- Caller approves this executor for a specific input amount; only that amount is pulled.
- Output is sent directly to the caller; no owner, admin, or withdrawal function exists.
- Router allowance is exact and reset to zero after the swap.
- `amountOutMinimum` must be nonzero and must be computed off-chain from a fresh
  quote/reference price plus a strict slippage policy.
- Deadline must be current and no more than 10 minutes ahead.
- Supported fee tiers are 0.01%, 0.05%, 0.30%, and 1.00%.
- Reentrancy guard; rejects zero addresses, identical tokens, and zero input.
- No arbitrary router, arbitrary calldata, flash-loan, owner sweep, or upgrade mechanism.

## Limitations

This is an execution primitive, not a complete trading bot. The off-chain system
must independently validate pool existence/liquidity, quote freshness, price
impact, token decimals, token allowlists, token risk, and expected net
profitability. A strict minimum output reduces price manipulation risk but does
not guarantee protection from MEV or bad quotes. Unknown, fee-on-transfer,
rebasing, or otherwise non-standard tokens are not supported.

The contract has passed the repository's mocked Foundry unit tests. It has not
yet been exercised against a live Base Sepolia fork, deployed to testnet,
formally verified, or independently audited. **Do not deploy to mainnet or fund
it until testnet integration, static analysis, and independent security review
pass.**

## Build and test

From this directory:

```bash
forge build
forge test -vvv
```

## Testnet deployment (after a Base Sepolia integration test)

1. Install Foundry and configure `BASE_SEPOLIA_RPC_URL` in your local environment.
2. Create a dedicated deployment wallet holding only a small amount of test ETH.
3. Export its private key as `PRIVATE_KEY` in your local shell. Never paste it into
   ChatGPT, commit it, or put it in source code.
4. Run:

```bash
cd contracts
forge script script/DeployBaseSpotExecutor.s.sol:DeployBaseSpotExecutor \
  --rpc-url base_sepolia --broadcast
```

5. Record the deployment address and transaction hash; verify the source on the
   Base Sepolia explorer and perform a real test-token swap with a strict minimum
   output and small amount.

Only after all checks and independent review should the same script be run with
`--rpc-url base` using a dedicated wallet. Deployment is a separate, explicit
operator action; this repository does not deploy automatically.
