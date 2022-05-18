import http.server
import socketserver

handler = http.server.SimpleHTTPRequestHandler
handler.extensions_map.update({
    ".js": "application/javascript"
})

httpd = socketserver.TCPServer(("", 8002), handler)
httpd.serve_forever()
