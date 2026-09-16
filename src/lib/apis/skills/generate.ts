import { WEBUI_API_BASE_URL } from '$lib/constants';

export const generateSkillDraft = async (
	token: string,
	payload: { prompt: string; model?: string; language?: string }
) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/skills/generate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(payload)
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: res.statusText }));
		throw error?.detail ?? error;
	}
	return res.json();
};

export const duplicateSkill = async (
	token: string,
	id: string,
	payload: { id: string; name?: string }
) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/skills/id/${id}/duplicate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(payload)
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: res.statusText }));
		throw error?.detail ?? error;
	}
	return res.json();
};
