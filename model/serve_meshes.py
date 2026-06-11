#!/usr/bin/env python3
"""Tiny static file server for the robot meshes and URDF.

The bridge is rosbridge, which cannot resolve package:// mesh URIs, so the URDF points at
http://<host>:8100/robomo.dae and this serves model/meshes/ over HTTP. CORS is open so both
the Foxglove web app and desktop app can fetch the mesh.

Also serves the URDF itself at /robomo.urdf for Foxglove's URDF-layer "URL" source. The file
is mounted at a top-level path of its own (URDF_FILE) because a file bind can't be created
inside the read-only meshes mount.
"""
import http.server
import os
import socketserver

DIR = os.environ.get("MESH_DIR", "/meshes")
URDF = os.environ.get("URDF_FILE", "/robomo.urdf")
PORT = int(os.environ.get("PORT", "8100"))
os.chdir(DIR)


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean == "/" + os.path.basename(URDF) and os.path.isfile(URDF):
            return URDF
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class Server(socketserver.TCPServer):
    allow_reuse_address = True


print(f"serving {DIR} on :{PORT}", flush=True)
Server(("", PORT), Handler).serve_forever()
