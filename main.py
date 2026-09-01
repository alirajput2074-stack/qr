import io
import base64
import qrcode
from flask import Flask, render_template_string, request

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Code Generator - Dark Edition</title>
    <style>
        body { background-color: #0b0c10; color: #e1e1e6; font-family: sans-serif; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .app-window { background-color: #121214; width: 1000px; height: 620px; border-radius: 20px; display: flex; box-shadow: 0 25px 60px rgba(0,0,0,0.4); overflow: hidden; border: 1px solid #1f1f23; }
        .window-left { flex: 1.1; background-color: #121214; display: flex; justify-content: center; align-items: center; padding: 40px; }
        .qr-stage-container { width: 340px; height: 340px; background-color: #1c1c1f; border: 1px solid #29292e; border-radius: 16px; display: flex; justify-content: center; align-items: center; }
        .qr-stage-container img { width: 240px; height: 240px; display: block; border-radius: 8px; }
        .window-right { flex: 1.3; background-color: #16161a; border-left: 1px solid #1f1f23; padding: 40px; display: flex; flex-direction: column; box-sizing: border-box; }
        .drawer-box { border: 1px solid #29292e; border-radius: 12px; margin-bottom: 14px; overflow: hidden; background-color: #121214; }
        .drawer-header { padding: 18px 24px; font-weight: 700; font-size: 14px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
        .drawer-header.active-blue { background-color: #00a8ff; color: #ffffff; }
        .drawer-header.plain-dark { background-color: #121214; color: #c5c5d2; }
        .drawer-body { padding: 24px; display: block; background-color: #121214; border-top: 1px solid #1f1f23; }
        .drawer-body.collapsed { display: none !important; }
        .input-text-area { width: 100%; padding: 16px 20px; background-color: #1c1c1f; border: 1px solid #29292e; color: #ffffff; border-radius: 12px; font-size: 15px; box-sizing: border-box; margin-bottom: 20px; }
        .matrix-options-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        .frame-card-node { border: 1px solid #29292e; border-radius: 10px; padding: 12px; text-align: center; font-size: 11px; font-weight: 600; color: #a0a0b0; cursor: pointer; background-color: #1c1c1f; }
        .frame-card-node.selected { border-color: #00a8ff; background-color: #00a8ff20; color: #00a8ff; }
        .action-container-row { display: flex; gap: 16px; margin-top: auto; width: 100%; }
        .btn-action-trigger { flex: 1; border: none; padding: 16px; border-radius: 50px; font-size: 15px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .btn-action-trigger.solid-green { background-color: #05d3a3; color: #ffffff; }
        .btn-action-trigger.outline-cyan { background-color: transparent; border: 2px solid #00d2c4; color: #00d2c4; }
    </style>
</head>
<body>
    <div class="app-window">
        <div class="window-left">
            <div class="qr-stage-container">
                {% if qr_img %}
                <img src="data:image/png;base64,{{ qr_img }}" alt="Live QR">
                {% else %}
                <div style="color: #64748b; font-weight: 600; font-size: 14px;">QR Code Grid Output</div>
                {% endif %}
            </div>
        </div>
        <form class="window-right" method="POST" id="qrForm">
            <div class="drawer-box">
                <div class="drawer-header active-blue" onclick="toggleDrawer('frames-content')">
                    <span>FRAMES <span style="font-size: 10px; margin-left: 5px; background: rgba(255,255,255,0.3); padding: 2px 6px; border-radius: 4px;">NEW!</span></span>
                    <span id="frames-content-arrow">▲</span>
                </div>
                <div id="frames-content" class="drawer-body">
                    <input type="text" class="input-text-area" name="qr_data" placeholder="Enter text or URL..." value="{{ text_data }}" oninput="autoSubmitForm()" required>
                    <div class="matrix-options-grid">
                        <div class="frame-card-node selected">✕</div>
                        <div class="frame-card-node">Standard</div>
                        <div class="frame-card-node">Scan Me</div>
                        <div class="frame-card-node">Watch Now</div>
                    </div>
                </div>
            </div>
            <div class="drawer-box">
                <div class="drawer-header plain-dark" onclick="toggleDrawer('shape-content')">
                    <span>SHAPE & COLOR</span>
                    <span id="shape-content-arrow">▼</span>
                </div>
                <div id="shape-content" class="drawer-body collapsed">
                    <div style="color: #8a8a93; font-size: 13px;">Custom node shapes, colors, and designs.</div>
                </div>
            </div>
            <div class="drawer-box">
                <div class="drawer-header plain-dark" onclick="toggleDrawer('logo-content')">
                    <span>LOGO</span>
                    <span id="logo-content-arrow">▼</span>
                </div>
                <div id="logo-content" class="drawer-body collapsed">
                    <div style="color: #8a8a93; font-size: 13px;">Embed custom logo images.</div>
                </div>
            </div>
            <div class="action-container-row">
                <button type="button" class="btn-action-trigger solid-green" onclick="triggerDownload()">DOWNLOAD JPG</button>
                <button type="button" class="btn-action-trigger outline-cyan">VECTOR SVG/EPS</button>
            </div>
        </form>
    </div>
    <script>
        function toggleDrawer(id) {
            const el = document.getElementById(id);
            const arrow = document.getElementById(id + '-arrow');
            if (el.classList.contains('collapsed')) { el.classList.remove('collapsed'); arrow.innerText = '▲'; }
            else { el.classList.add('collapsed'); arrow.innerText = '▼'; }
        }
        let typingTimer;
        function autoSubmitForm() {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(() => { document.getElementById('qrForm').submit(); }, 400); 
        }
        function triggerDownload() {
            const qrImg = document.querySelector('.qr-stage-container img');
            if (qrImg) {
                const link = document.createElement('a'); link.href = qrImg.src; link.download = 'custom_qrcode.png';
                document.body.appendChild(link); link.click(); document.body.removeChild(link);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    text_data = "https://roblox.com"  
    qr_img_base64 = ""
    if request.method == 'POST':
        text_data = request.form.get('qr_data', '').strip()
    if text_data:
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(text_data)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        img_qr.save(qr_buffer, format="PNG")
        qr_img_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
    return render_template_string(HTML_TEMPLATE, qr_img=qr_img_base64, text_data=text_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
