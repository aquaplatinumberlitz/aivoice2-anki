(() => {
    const state = window.__aivoice2Selection ||= {};
    state.noteId = __AIVOICE_NOTE_ID__;
    state.text = '';
    if (!state.button?.isConnected) {
        const button = document.createElement('button');
        button.id = 'aivoice2-selection-mic';
        button.type = 'button';
        button.textContent = '🎙 Nghe thử';
        button.title = 'Nghe câu tiếng Nhật đã chọn · chưa lưu vào card';
        button.setAttribute('aria-label', button.title);
        button.style.cssText = 'position:fixed;z-index:2147483647;display:none;' +
            'padding:9px 14px;border:1px solid #426d73;border-radius:22px;' +
            'background:#173e43;color:#fff;box-shadow:0 3px 15px #0004;' +
            'font:500 14px sans-serif;cursor:pointer;line-height:1.4;';
        button.addEventListener('mousedown', event => event.preventDefault());
        button.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();
            if (state.text) pycmd('aivoice2:selection:' + JSON.stringify({
                text: state.text, noteId: state.noteId,
            }));
            button.style.display = 'none';
        });
        document.body.appendChild(button);
        state.button = button;
    }
    state.button.style.display = 'none';
    if (state.installed) return;
    state.installed = true;
    function update() {
        const selection = window.getSelection();
        const text = selection?.toString().trim() || '';
        if (!text || text.length > 4096 || !/[\u3040-\u30ff\u3400-\u9fff]/u.test(text)
                || !selection.rangeCount) {
            state.button.style.display = 'none';
            return;
        }
        state.text = text;
        const rect = selection.getRangeAt(0).getBoundingClientRect();
        state.button.style.display = 'block';
        const width = state.button.offsetWidth;
        const height = state.button.offsetHeight;
        state.button.style.left = Math.max(8, Math.min(rect.left, innerWidth - width - 8)) + 'px';
        state.button.style.top = Math.max(8, Math.min(rect.bottom + 8, innerHeight - height - 8)) + 'px';
    }
    document.addEventListener('mouseup', event => {
        if (!state.button.contains(event.target)) setTimeout(update, 20);
    });
    document.addEventListener('keyup', event => {
        if (event.key === 'Escape') state.button.style.display = 'none';
        else if (event.key === 'Shift' || event.shiftKey) setTimeout(update, 20);
    });
    document.addEventListener('scroll', () => state.button.style.display = 'none', true);
})();
