from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/incoming-call", methods=["POST"])
def incoming_call():
    response = VoiceResponse()
    
    # Assuming your voice bot uses WebSocket for streaming audio
    response.connect().stream(url='wss://d2qcjspr6rc0rj.cloudfront.net/')
    
    return Response(str(response), mimetype="text/xml")

if __name__ == "__main__":
    app.run(port=5000)
