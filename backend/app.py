from flask import Flask, jsonify, send_file, make_response, request
from pytubefix import Search, YouTube
from flask_cors import CORS
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

FRONTEND_URL = os.environ.get('FRONTEND_URL', '')
flask_dir_path = os.path.abspath("")
TMP_DIR = os.path.join(flask_dir_path, "tmp")

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": ["*"]}})

@app.route('/search', methods=['POST'])
def search_youtube():
    search_query = request.form.get('searchQuery')
    MAX_DURATION_SECONDS = 600  # 10 minutes
    
    results = Search(search_query)
    video_dto = []
    filtered_count = 0
    
    for video in results.videos:
        try:
            # Create YouTube object to get duration
            yt = YouTube(video.watch_url)
            duration_seconds = yt.length
            
            # Only include videos under the duration limit
            if duration_seconds and duration_seconds <= MAX_DURATION_SECONDS:
                video_dto.append({
                    'title': video.title,
                    'youtubeUrl': video.watch_url,
                    'thumbnailUrl': video.thumbnail_url,
                    'duration': duration_seconds
                })
            else:
                filtered_count += 1
        except Exception as e:
            print(f"Error getting duration for {video.title}: {e}")
            filtered_count += 1
            continue
    
    print(f"Filtered out {filtered_count} videos over {MAX_DURATION_SECONDS/60} minutes")
    return jsonify({
        'results': video_dto,
        'filteredCount': filtered_count,
        'maxDurationMinutes': MAX_DURATION_SECONDS / 60
    })



@app.route('/download-video', methods=['POST'])
def download_video():
    url = request.form.get('youtubeUrl')
    if not url:
        print('Missing youtubeUrl field!')
        return jsonify({"error": "No URL provided"}), 400

    print(f"Download requested for: {url}")

    try:
        yt = YouTube(url)
        stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()
        print("Stream object: ", stream)
        if not stream:
            print("[ERROR] No valid mp4 stream found for this URL!")
            return jsonify({"error": "No valid mp4 stream found"}), 404

        if getattr(stream, 'filesize_mb', 0) > 200:
            print("[ERROR] Requested video too large: ", getattr(stream, 'filesize_mb', 0), "MB")
            return jsonify("File too large"), 413

        ext = stream.subtype
        file_name = f"tempvideo.{ext}"
        file_path = os.path.join(TMP_DIR, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        print("Downloading video to: ", file_path)
        stream.download(output_path=os.path.dirname(file_path), filename=os.path.basename(file_path))

        # === File existence and size check ===
        if not os.path.exists(file_path):
            print("[ERROR] File does not exist after download:", file_path)
            return jsonify({"error": "Download failed: file not found"}), 500
        file_size = os.path.getsize(file_path)
        print(f"[INFO] Downloaded file size: {file_size} bytes")
        if file_size == 0:
            print("[ERROR] Downloaded file is 0 bytes!")
            return jsonify({"error": "Download failed: empty file"}), 500

        response = make_response(send_file(
            file_path,
            as_attachment=True,
            download_name=f"temp_video.{ext}",
            mimetype='video/mp4'
        ))
        print("[SUCCESS] Sending file to client.")
        return response

    except Exception as e:
        print(f"[ERROR] Exception during /download-video: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
