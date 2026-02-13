from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            print("\n" + "="*50)
            print(f"RECEPTION DE : {data.get('stagiaire', 'Inconnu')}")
            print("-" * 50)
            print("LOGS KUBECTL :")
            print(data.get('logs', 'Aucun log reçu'))
            print("="*50 + "\n")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Validation reçue"}).encode('utf-8'))
        except Exception as e:
            print(f"Erreur lors de la réception : {e}")
            self.send_response(400)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run(server_class=HTTPServer, handler_class=ReceiverHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serveur du formateur en écoute sur le port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
        httpd.server_close()

if __name__ == "__main__":
    run()
