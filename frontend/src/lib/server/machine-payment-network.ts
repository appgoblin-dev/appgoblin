export function getMachinePaymentNetwork(value: string | undefined, stripeKey: string) {
	const network = value?.trim();
	if (network === 'eip155:8453') {
		return {
			network,
			usdcAddress: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
			recordInStripe: true
		} as const;
	}
	if (network === 'eip155:84532') {
		if (!/^(sk|rk)_test_/.test(stripeKey.trim())) {
			throw new Error('[MachinePayments] Base Sepolia requires a Stripe test key');
		}
		return {
			network,
			usdcAddress: '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
			recordInStripe: false
		} as const;
	}
	throw new Error('[MachinePayments] BLOCKCHAIN_NETWORK must be eip155:8453 or eip155:84532');
}
