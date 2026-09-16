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

export const getSafeModeStatus = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/privacy/safe-mode`, token);

export const getTemporaryChatPolicy = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/privacy/temporary/policy`, token);

export const convertTemporaryChat = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/privacy/temporary/convert`, token, 'POST', payload);

export const getAuditLog = async (token: string, limit = 50) =>
	requestJson(`${WEBUI_API_BASE_URL}/privacy/audit?limit=${limit}`, token);

export const postAuditEvent = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/privacy/audit`, token, 'POST', payload);

export const getRecoveryPlan = async (token: string, issue: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/privacy/recovery/plan`, token, 'POST', { issue });
