import { WEBUI_API_BASE_URL } from '$lib/constants';

const requestJson = async (url: string, token: string, method = 'GET') => {
	const res = await fetch(url, {
		method,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: res.statusText }));
		throw error?.detail ?? error;
	}
	return res.json();
};

export const getChatMemoryCount = async (token: string, id: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/chats/${id}/memories/count`, token);

export const deleteChatWithMemories = async (token: string, id: string) =>
	requestJson(`${WEBUI_API_BASE_URL}/chats/${id}/with-memories`, token, 'DELETE');
