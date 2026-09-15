export type Vec3 = [number, number, number];
export type Triangle3D = [Vec3, Vec3, Vec3];

export const model3dExtensions = new Set(['stl', 'obj']);

export const fileExtension = (name = '') => name.split('.').pop()?.toLowerCase() ?? '';
export const isModel3dFile = (name = '') => model3dExtensions.has(fileExtension(name));

const decodeText = (data: ArrayBuffer | Uint8Array | string) => {
	if (typeof data === 'string') return data;
	const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
	return new TextDecoder('utf-8', { fatal: false }).decode(bytes);
};

const parseBinaryStl = (buffer: ArrayBuffer): Triangle3D[] => {
	if (buffer.byteLength < 84) return [];
	const view = new DataView(buffer);
	const triangleCount = view.getUint32(80, true);
	if (84 + triangleCount * 50 > buffer.byteLength) return [];

	const triangles: Triangle3D[] = [];
	let offset = 84;
	for (let i = 0; i < triangleCount; i += 1) {
		offset += 12; // normal
		const vertices: Vec3[] = [];
		for (let vertex = 0; vertex < 3; vertex += 1) {
			vertices.push([
				view.getFloat32(offset, true),
				view.getFloat32(offset + 4, true),
				view.getFloat32(offset + 8, true)
			]);
			offset += 12;
		}
		offset += 2; // attribute byte count
		triangles.push(vertices as Triangle3D);
	}
	return triangles;
};

const parseAsciiStl = (text: string): Triangle3D[] => {
	const triangles: Triangle3D[] = [];
	const vertices: Vec3[] = [];
	const vertexPattern = /\bvertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)/gi;
	let match: RegExpExecArray | null;
	while ((match = vertexPattern.exec(text))) {
		const vertex: Vec3 = [Number(match[1]), Number(match[2]), Number(match[3])];
		if (vertex.every(Number.isFinite)) vertices.push(vertex);
	}
	for (let i = 0; i + 2 < vertices.length; i += 3) {
		triangles.push([vertices[i], vertices[i + 1], vertices[i + 2]]);
	}
	return triangles;
};

export const parseStl = (data: ArrayBuffer | Uint8Array | string): Triangle3D[] => {
	if (typeof data !== 'string') {
		const buffer = data instanceof Uint8Array
			? data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength)
			: data;
		if (buffer.byteLength >= 84) {
			const view = new DataView(buffer);
			const count = view.getUint32(80, true);
			if (84 + count * 50 === buffer.byteLength) {
				const binary = parseBinaryStl(buffer);
				if (binary.length) return binary;
			}
		}
	}
	return parseAsciiStl(decodeText(data));
};

const parseObjIndex = (token: string, vertexCount: number) => {
	const raw = Number(token.split('/')[0]);
	if (!Number.isInteger(raw) || raw === 0) return null;
	return raw > 0 ? raw - 1 : vertexCount + raw;
};

export const parseObj = (data: ArrayBuffer | Uint8Array | string): Triangle3D[] => {
	const vertices: Vec3[] = [];
	const triangles: Triangle3D[] = [];
	for (const rawLine of decodeText(data).split(/\r?\n/)) {
		const line = rawLine.trim();
		if (!line || line.startsWith('#')) continue;
		if (line.startsWith('v ')) {
			const parts = line.split(/\s+/).slice(1, 4).map(Number);
			if (parts.length === 3 && parts.every(Number.isFinite)) vertices.push(parts as Vec3);
			continue;
		}
		if (!line.startsWith('f ')) continue;
		const indexes = line
			.split(/\s+/)
			.slice(1)
			.map((token) => parseObjIndex(token, vertices.length))
			.filter((value): value is number => value !== null && value >= 0 && value < vertices.length);
		if (indexes.length < 3) continue;
		for (let i = 1; i < indexes.length - 1; i += 1) {
			triangles.push([vertices[indexes[0]], vertices[indexes[i]], vertices[indexes[i + 1]]]);
		}
	}
	return triangles;
};

export const parseModel3d = (name: string, data: ArrayBuffer | Uint8Array | string): Triangle3D[] => {
	const ext = fileExtension(name);
	if (ext === 'stl') return parseStl(data);
	if (ext === 'obj') return parseObj(data);
	return [];
};

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a: Vec3, b: Vec3): Vec3 => [
	a[1] * b[2] - a[2] * b[1],
	a[2] * b[0] - a[0] * b[2],
	a[0] * b[1] - a[1] * b[0]
];
const normalize = (v: Vec3): Vec3 => {
	const length = Math.hypot(v[0], v[1], v[2]) || 1;
	return [v[0] / length, v[1] / length, v[2] / length];
};

export const trianglesToAsciiStl = (name: string, triangles: Triangle3D[]) => {
	const safeName = (name || 'model').replace(/[^a-zA-Z0-9_.-]+/g, '_');
	const lines = [`solid ${safeName}`];
	for (const [a, b, c] of triangles) {
		const normal = normalize(cross(sub(b, a), sub(c, a)));
		lines.push(`  facet normal ${normal[0]} ${normal[1]} ${normal[2]}`);
		lines.push('    outer loop');
		for (const vertex of [a, b, c]) lines.push(`      vertex ${vertex[0]} ${vertex[1]} ${vertex[2]}`);
		lines.push('    endloop');
		lines.push('  endfacet');
	}
	lines.push(`endsolid ${safeName}`);
	return `${lines.join('\n')}\n`;
};

export const modelBounds = (triangles: Triangle3D[]) => {
	let min: Vec3 = [Infinity, Infinity, Infinity];
	let max: Vec3 = [-Infinity, -Infinity, -Infinity];
	for (const triangle of triangles) {
		for (const vertex of triangle) {
			min = [Math.min(min[0], vertex[0]), Math.min(min[1], vertex[1]), Math.min(min[2], vertex[2])];
			max = [Math.max(max[0], vertex[0]), Math.max(max[1], vertex[1]), Math.max(max[2], vertex[2])];
		}
	}
	if (!triangles.length) return { min: [0, 0, 0] as Vec3, max: [0, 0, 0] as Vec3, center: [0, 0, 0] as Vec3, radius: 1 };
	const center: Vec3 = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
	const radius = Math.max(1e-6, Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2);
	return { min, max, center, radius };
};
