import loadConfig from '$lib/loadConfig.js';

export async function load({ params }) {
	const domain = params.domain || '';
	const adstxtEndpoint = loadConfig();
	const downloadUrl = adstxtEndpoint && domain ? `${adstxtEndpoint}${domain}/latest.csv` : null;
	return { downloadUrl };
}
