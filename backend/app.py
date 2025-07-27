from flask import Flask
from flask import jsonify, send_file, make_response, request

from pytubefix import Search, YouTube
from flask_cors import CORS
import base64
import os

FRONTEND_URL = os.environ.get('FRONTEND_URL', '')

flask_dir_path = os.path.abspath("")

app = Flask(__name__)

CORS(app, resources={r"/search": {"origins": FRONTEND_URL},
                     r"/download-video": {"origins": FRONTEND_URL, "expose_headers": ["X-Video-Title"]}})

@app.route('/search', methods=['POST'])
def search_youtube():
    search_query = request.form.get('searchQuery')
    results = Search(search_query)
    video_dto = [
        {
            'title': video.title,
            'youtubeUrl': video.watch_url,
            'thumbnailUrl': video.thumbnail_url
        }
        for video in results.videos
    ]
    return jsonify(video_dto)

@app.route('/download-video', methods=['POST'])
def download_video():
    url = request.form.get('youtubeUrl')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        yt = YouTube(url)
        stream = yt.streams.get_audio_only()
        if stream.filesize_mb > 200:
            return jsonify("File too large"), 413

        ext = stream.subtype
        file_name = f"tempvideo.{ext}"
        file_path = os.path.join(flask_dir_path, "tmp", file_name)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        stream.download(output_path=os.path.dirname(file_path), filename=os.path.basename(file_path))

        response = make_response(send_file(
            file_path,
            as_attachment=True,
            download_name=f"temp_video.{ext}"
        ))
        encoded_title = base64.b64encode(yt.title.encode('utf-8')).decode('utf-8')
        response.headers['X-Video-Title'] = encoded_title
        return response

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run()
