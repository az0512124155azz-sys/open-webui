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

export const optimizeContext = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/context/optimize`, token, 'POST', payload);

export const mergeAnswers = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/answers/merge`, token, 'POST', payload);

export const savePromptVersion = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/prompts/versions`, token, 'POST', payload);

export const listPromptVersions = async (token: string, promptId: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/prompts/${promptId}/versions`, token);

export const createChatSnapshot = async (token: string, payload: object) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/snapshots`, token, 'POST', payload);

export const listChatSnapshots = async (token: string, chatId: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/snapshots/${chatId}`, token);

export const getChatSnapshot = async (token: string, chatId: string, snapshotId: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/chat-intelligence/snapshots/${chatId}/${snapshotId}`, token);
