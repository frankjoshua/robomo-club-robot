#!/usr/bin/env python3
"""Tiny static file server for the robot meshes.

The bridge is rosbridge, which cannot resolve package:// mesh URIs, so the URDF points at
http://<host>:8100/robomo.dae and this serves model/meshes/ over HTTP. CORS is open so both
the Foxglove web app and desktop app can fetch the mesh.
"""
import http.server
import os
import socketserver

DIR = os.environ.get("MESH_DIR", "/meshes")
PORT = int(os.environ.get("PORT", "8100"))
os.chdir(DIR)


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class Server(socketserver.TCPServer):
    allow_reuse_address = True


print(f"serving {DIR} on :{PORT}", flush=True)
Server(("", PORT), Handler).serve_forever()
