from flask import Flask, jsonify, send_file, make_response, request, Response, stream_template
from pytubefix import Search, YouTube
from flask_cors import CORS
import os
from dotenv import load_dotenv
import traceback
import json
import time
import threading

load_dotenv()

FRONTEND_URL = os.environ.get('FRONTEND_URL', '')
flask_dir_path = os.path.abspath("")
TMP_DIR = os.path.join(flask_dir_path, "tmp")

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": ["*"]}})

@app.route('/search-stream', methods=['GET'])
def search_stream():
    """Streaming search endpoint that returns results progressively"""
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    def generate():
        try:
            MAX_DURATION_SECONDS = 600  # 10 minutes
            MAX_RESULTS = 30  # Limit initial results
            BATCH_SIZE = 5   # Send results in batches of 5
            TIMEOUT_SECONDS = 15  # 15 second timeout
            
            start_time = time.time()
            
            print(f"Starting streaming search for: {query}")
            
            # Get search results
            search_results = Search(query)
            total_videos = len(search_results.videos[:MAX_RESULTS])  # Limit to first 30
            
            video_batch = []
            processed_count = 0
            found_count = 0
            filtered_count = 0
            
            for i, video in enumerate(search_results.videos[:MAX_RESULTS]):
                # Check for timeout
                if time.time() - start_time > TIMEOUT_SECONDS:
                    # Send any remaining batch
                    if video_batch:
                        yield f"data: {json.dumps({'type': 'batch', 'results': video_batch})}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'timeout', 'message': 'Search timeout - showing partial results'})}\n\n"
                    return
                
                try:
                    # Get video duration
                    yt = YouTube(video.watch_url)
                    duration_seconds = yt.length
                    
                    processed_count += 1
                    
                    # Filter by duration
                    if duration_seconds and duration_seconds <= MAX_DURATION_SECONDS:
                        video_data = {
                            'title': video.title,
                            'youtubeUrl': video.watch_url,
                            'thumbnailUrl': video.thumbnail_url,
                            'duration': duration_seconds
                        }
                        
                        video_batch.append(video_data)
                        found_count += 1
                        
                        # Send batch when it reaches BATCH_SIZE
                        if len(video_batch) >= BATCH_SIZE:
                            yield f"data: {json.dumps({'type': 'batch', 'results': video_batch})}\n\n"
                            video_batch = []
                    else:
                        filtered_count += 1
                    
                    # Send progress update
                    progress_data = {
                        'type': 'progress',
                        'processed': processed_count,
                        'total': total_videos,
                        'found': found_count
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    
                except Exception as e:
                    print(f"Error processing video {video.title}: {e}")
                    processed_count += 1
                    filtered_count += 1
                    continue
            
            # Send any remaining videos in the batch
            if video_batch:
                yield f"data: {json.dumps({'type': 'batch', 'results': video_batch})}\n\n"
            
            # Send completion message
            completion_data = {
                'type': 'complete',
                'total': total_videos,
                'totalFound': found_count,
                'filteredCount': filtered_count,
                'maxDurationMinutes': MAX_DURATION_SECONDS / 60
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
            print(f"Streaming search completed. Found {found_count} results, filtered {filtered_count}")
            
        except Exception as e:
            print(f"Error in streaming search: {e}")
            traceback.print_exc()
            error_data = {
                'type': 'error',
                'message': f'Search failed: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Cache-Control'
    
    return response

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
