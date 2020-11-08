from flask import Flask
from narupa.trajectory.frame_client import FrameClient
from narupa.protocol.command import GetCommandsRequest
import grpc


app = Flask(__name__)

@app.route('/api/status')
def get_status():
    channel = FrameClient.insecure_channel(address='127.0.0.1', port=38801)
    request = GetCommandsRequest()
    try:
        channel._command_stub.GetCommands(request, timeout=1)
    except (grpc._channel._Rendezvous, grpc._channel._InactiveRpcError):
        return { 'status': False }
    finally:
        channel.close()
    return { 'status': True }
