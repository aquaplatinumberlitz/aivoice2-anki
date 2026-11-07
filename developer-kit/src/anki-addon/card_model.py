"""A separate note type; never rewrites templates of existing note types."""
MODEL_NAME = 'A.I.VOICE2 · Nhật–Việt'
FRONT = '''<main class="aivoice-card">
  <div class="aivoice-eyebrow">日本語 · ĐỌC & NGHE</div>
  <div class="aivoice-japanese" lang="ja">{{Japanese}}</div>
  {{#Romaji}}<details class="aivoice-romaji"><summary>Hiện romaji</summary>
    <div>{{Romaji}}</div></details>{{/Romaji}}
  <div class="aivoice-hint">Bôi đen câu tiếng Nhật → 🎙 Nghe thử</div>
</main>'''
BACK = '''<main class="aivoice-card">
  <div class="aivoice-eyebrow">日本語 · ĐỌC & NGHE</div>
  <div class="aivoice-japanese" lang="ja">{{Japanese}}</div>
  {{#Romaji}}<div class="aivoice-reading">{{Romaji}}</div>{{/Romaji}}
  <hr id="answer">
  <div class="aivoice-eyebrow">NGHĨA TIẾNG VIỆT</div>
  <div class="aivoice-vietnamese">{{Vietnamese}}</div>
  {{#Audio}}<div class="aivoice-audio">{{Audio}}</div>{{/Audio}}
  <div class="aivoice-hint">Bôi đen câu tiếng Nhật → 🎙 Nghe thử → Chèn vào card</div>
</main>'''
CSS = '''.card { font-family: system-ui, sans-serif; font-size: 20px;
  text-align: left; color: #23343a; background: #f5f6f3; margin: 0; padding: 24px; }
.aivoice-card { max-width: 720px; margin: 4vh auto; padding: 32px;
  background: #fff; border: 1px solid #dce4df; border-radius: 20px; }
.aivoice-eyebrow { font-size: 11px; letter-spacing: .12em; color: #607873; font-weight: 600; }
.aivoice-japanese { font-family: "Noto Sans CJK JP", "Noto Sans JP", sans-serif;
  font-size: 32px; line-height: 1.85; margin: 20px 0; user-select: text; }
.aivoice-reading { color: #677c76; font-size: 17px; line-height: 1.6; }
.aivoice-romaji { color: #677c76; font-size: 16px; }
.aivoice-romaji summary { cursor: pointer; }
.aivoice-romaji div { margin-top: 8px; }
.aivoice-vietnamese { font-size: 23px; line-height: 1.7; margin-top: 14px; }
.aivoice-hint { font-size: 12px; color: #7c8c86; margin-top: 28px; line-height: 1.7; }
.aivoice-audio { margin-top: 20px; }
hr { border: 0; border-top: 1px solid #dce4df; margin: 26px 0; }
.nightMode.card { color: #e4ece7; background: #18211f; }
.nightMode .aivoice-card { background: #202c28; border-color: #38493f; }
.nightMode .aivoice-reading, .nightMode .aivoice-romaji { color: #adc3b7; }
.nightMode .aivoice-eyebrow, .nightMode .aivoice-hint { color: #8ca99b; }
.nightMode hr { border-color: #38493f; }
@media(max-width: 500px) { .card { padding: 12px; } .aivoice-card { padding: 22px; }
  .aivoice-japanese { font-size: 27px; } }
'''


def ensure_model(col):
    existing = col.models.by_name(MODEL_NAME)
    if existing:
        return existing
    model = col.models.new(MODEL_NAME)
    for name in ('Japanese', 'Romaji', 'Vietnamese', 'Audio'):
        col.models.add_field(model, col.models.new_field(name))
    template = col.models.new_template('Đọc & nghe')
    template['qfmt'] = FRONT
    template['afmt'] = BACK
    col.models.add_template(model, template)
    model['css'] = CSS
    col.models.add(model)
    return model
