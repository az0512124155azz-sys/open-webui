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

export const getPlugins = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/`, token);

export const getPluginPermissions = async (token: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/permissions`, token);

export const getPluginById = async (token: string, id: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/id/${id}`, token);

export const validatePlugin = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/validate`, token, 'POST', payload);

export const installPlugin = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/install`, token, 'POST', payload);

export const enablePlugin = async (token: string, id: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/id/${id}/enable`, token, 'POST');

export const disablePlugin = async (token: string, id: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/id/${id}/disable`, token, 'POST');

export const uninstallPlugin = async (token: string, id: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/plugins/id/${id}`, token, 'DELETE');
