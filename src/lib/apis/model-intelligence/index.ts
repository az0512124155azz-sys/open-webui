import { WEBUI_API_BASE_URL } from '$lib/constants';

const requestJson = async (url: string, token: string, method = 'GET', body?: object) => {
	const res = await fetch(url, {
		method,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		...(body ? { body: JSON.stringify(body) } : {})
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: res.statusText }));
		throw error?.detail ?? error;
	}
	return res.json();
};

export const getConnectionHealth = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/health`, token);

export const getDuplicateModels = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/duplicates`, token);

export const routeModels = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/route`, token, 'POST', payload);

export const getFallbackChain = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/fallback`, token, 'POST', payload);

export const warmupModels = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/warmup`, token, 'POST', payload);

export const checkModelUpdates = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/updates`, token);

export const benchmarkModel = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/model-intelligence/benchmark`, token, 'POST', payload);
