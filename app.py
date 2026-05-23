
from flask import Flask, render_template_string, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>X Video Downloader HQ</title>

<style>
body{
    background:#0f172a;
    color:white;
    font-family:Arial;
    max-width:850px;
    margin:40px auto;
    padding:20px;
}

.card{
    background:#1e293b;
    padding:25px;
    border-radius:16px;
}

input, select{
    width:100%;
    padding:14px;
    margin-top:12px;
    border:none;
    border-radius:10px;
    font-size:16px;
}

button{
    padding:14px 20px;
    border:none;
    border-radius:10px;
    margin-top:15px;
    cursor:pointer;
    font-size:16px;
}

.fetch{
    background:#3b82f6;
    color:white;
}

.download{
    background:#22c55e;
    color:white;
}

.meta{
    margin-top:20px;
    background:#334155;
    padding:18px;
    border-radius:12px;
}

img{
    width:100%;
    border-radius:12px;
    margin-top:15px;
}
</style>
</head>

<body>

<div class="card">

<h1>X(Twitter) 動画保存ツール HQ</h1>

<form method="POST">

<input type="text" name="url" placeholder="投稿URLを貼り付け" required>

<button class="fetch" type="submit">
動画情報を取得
</button>

</form>

{% if title %}

<div class="meta">

<h2>{{ title }}</h2>
<p>投稿者: {{ uploader }}</p>

{% if thumbnail %}
<img src="{{ thumbnail }}">
{% endif %}

<form action="/download" method="POST">

<input type="hidden" name="url" value="{{ original_url }}">

<label>画質を選択</label>

<select name="format_id">

{% for f in formats %}
<option value="{{ f['format_id'] }}">
{{ f['label'] }}
</option>
{% endfor %}

</select>

<button class="download" type="submit">
MP4ダウンロード
</button>

</form>

</div>

{% endif %}

{% if error %}
<div class="meta">
{{ error }}
</div>
{% endif %}

</div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():

    title = None
    uploader = None
    thumbnail = None
    formats = []
    original_url = None
    error = None

    if request.method == "POST":

        url = request.form.get("url")

        try:

            ydl_opts = {
                "quiet": True,
                "skip_download": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=False)

                title = info.get("title")
                uploader = info.get("uploader")
                thumbnail = info.get("thumbnail")
                original_url = url

                seen = set()

                for f in info.get("formats", []):

                    if f.get("vcodec") == "none":
                        continue

                    height = f.get("height")

                    if not height:
                        continue

                    label = f"{height}p"

                    if label in seen:
                        continue

                    seen.add(label)

                    formats.append({
                        "format_id": f.get("format_id"),
                        "label": label
                    })

                formats = sorted(
                    formats,
                    key=lambda x: int(x["label"].replace("p","")),
                    reverse=True
                )

        except Exception as e:
            error = str(e)

    return render_template_string(
        HTML,
        title=title,
        uploader=uploader,
        thumbnail=thumbnail,
        formats=formats,
        original_url=original_url,
        error=error
    )

@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url")
    format_id = request.form.get("format_id")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        "format": format_id,
        "outtmpl": filepath,
        "merge_output_format": "mp4",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
