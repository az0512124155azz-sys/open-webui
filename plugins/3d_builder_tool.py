"""
title: 3D Builder
author: custom-fork
version: 1.0.0
description: Generates OpenSCAD + Three.js HTML. Enable TOOL in chat.
"""

class Tools:
    def build_openscad_triangle_prism(self, side_mm: float = 30, height_mm: float = 10) -> str:
        return f"$fn=64;\nlinear_extrude(height={height_mm}) polygon(points=[[0,0],[{side_mm},0],[{side_mm}/2,{side_mm}*0.866]]);\n"

    def build_openscad_box(self, width_mm: float = 20, depth_mm: float = 20, height_mm: float = 20) -> str:
        return f"$fn=64;\ncube([{width_mm},{depth_mm},{height_mm}]);\n"

    def build_threejs_html(self, shape: str = "box") -> str:
        shape = (shape or "box").lower()
        geos = {
            "box": "new THREE.BoxGeometry(1,1,1)",
            "sphere": "new THREE.SphereGeometry(0.6,32,32)",
            "cone": "new THREE.ConeGeometry(0.5,1,32)",
            "cylinder": "new THREE.CylinderGeometry(0.4,0.4,1,32)",
        }
        geo = geos.get(shape, geos["box"])
        return (
            "<!DOCTYPE html><html><head><meta charset=utf-8><title>3D</title>"
            "<style>html,body{margin:0;height:100%;background:#111}</style></head><body>"
            "<script type=importmap>{\"imports\":{\"three\":\"https://unpkg.com/three@0.160.0/build/three.module.js\","
            "\"three/addons/\":\"https://unpkg.com/three@0.160.0/examples/jsm/\"}}</script>"
            "<script type=module>"
            "import * as THREE from 'three';"
            "import { OrbitControls } from 'three/addons/controls/OrbitControls.js';"
            "const scene=new THREE.Scene();scene.background=new THREE.Color(0x111111);"
            "const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,0.1,100);"
            "camera.position.set(2.2,1.8,2.8);"
            "const renderer=new THREE.WebGLRenderer({antialias:true});"
            "renderer.setSize(innerWidth,innerHeight);document.body.appendChild(renderer.domElement);"
            "scene.add(new THREE.AmbientLight(0xffffff,0.4));"
            "const d=new THREE.DirectionalLight(0xffffff,1);d.position.set(3,4,2);scene.add(d);"
            f"const mesh=new THREE.Mesh({geo},new THREE.MeshStandardMaterial({{color:0x10a37f}}));"
            "scene.add(mesh);scene.add(new THREE.GridHelper(8,8,0x333,0x222));"
            "const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;"
            "addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});"
            "(function loop(){requestAnimationFrame(loop);controls.update();renderer.render(scene,camera);})();"
            "</script></body></html>"
        )

    def build_3d_pack(self, shape: str = "triangle") -> str:
        shape = (shape or "triangle").lower()
        if "box" in shape:
            scad, view = self.build_openscad_box(), self.build_threejs_html("box")
        elif "cyl" in shape:
            scad, view = self.build_openscad_box(15, 15, 25), self.build_threejs_html("cylinder")
        else:
            scad, view = self.build_openscad_triangle_prism(), self.build_threejs_html("cone")
        return "OpenSCAD:\n```scad\n" + scad + "\n```\n\nSave as viewer.html:\n```html\n" + view + "\n```\n"
