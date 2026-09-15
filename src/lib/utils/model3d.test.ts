import { describe, expect, it } from 'vitest';
import { isModel3dFile, parseObj, parseStl, trianglesToAsciiStl } from './model3d';

describe('model3d utilities', () => {
	it('detects supported model files', () => {
		expect(isModel3dFile('part.STL')).toBe(true);
		expect(isModel3dFile('mesh.obj')).toBe(true);
		expect(isModel3dFile('photo.png')).toBe(false);
	});

	it('triangulates OBJ polygon faces', () => {
		const triangles = parseObj(`
			v 0 0 0
			v 1 0 0
			v 1 1 0
			v 0 1 0
			f 1 2 3 4
		`);
		expect(triangles).toHaveLength(2);
		expect(triangles[0][0]).toEqual([0, 0, 0]);
	});

	it('parses ASCII STL', () => {
		const triangles = parseStl(`solid sample
			facet normal 0 0 1
				outer loop
					vertex 0 0 0
					vertex 1 0 0
					vertex 0 1 0
				endloop
			endfacet
		endsolid sample`);
		expect(triangles).toHaveLength(1);
	});

	it('exports valid ASCII STL text', () => {
		const triangles = parseObj('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3');
		const stl = trianglesToAsciiStl('triangle', triangles);
		expect(stl).toContain('solid triangle');
		expect(stl).toContain('facet normal');
		expect(stl).toContain('endsolid triangle');
	});
});
