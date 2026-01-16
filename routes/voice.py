from flask import Blueprint, jsonify

from services.voice_service import VoiceService

voice_bp = Blueprint('voice', __name__)
voice_service = VoiceService()


@voice_bp.route('/dinle', methods=['POST'])
def dinle():
    """Voice command endpoint."""
    # Listen for voice command
    success, command, error_message = voice_service.listen()

    if not success:
        return jsonify({'status': 'error', 'message': error_message})

    # Process command
    response = voice_service.process_command(command)

    return jsonify(response)
