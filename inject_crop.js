(function() {
    if (document.getElementById('dify-crop-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'dify-crop-overlay';
    Object.assign(overlay.style, {
        position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
        backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 999999, cursor: 'crosshair'
    });

    const selection = document.createElement('div');
    Object.assign(selection.style, {
        position: 'absolute', border: '2px solid #007bff', backgroundColor: 'rgba(0,123,255,0.1)', display: 'none', pointerEvents: 'none'
    });
    
    overlay.appendChild(selection);
    document.body.appendChild(overlay);

    let startX, startY;
    overlay.onmousedown = (e) => {
        startX = e.clientX; startY = e.clientY;
        selection.style.left = startX + 'px';
        selection.style.top = startY + 'px';
        selection.style.width = '0px';
        selection.style.height = '0px';
        selection.style.display = 'block';
        
        overlay.onmousemove = (ev) => {
            const curX = ev.clientX; const curY = ev.clientY;
            selection.style.width = Math.abs(curX - startX) + 'px';
            selection.style.height = Math.abs(curY - startY) + 'px';
            selection.style.left = Math.min(curX, startX) + 'px';
            selection.style.top = Math.min(curY, startY) + 'px';
        };
    };

    overlay.onmouseup = (e) => {
        const rect = {
            x: Math.min(e.clientX, startX), y: Math.min(e.clientY, startY),
            w: Math.abs(e.clientX - startX), h: Math.abs(e.clientY - startY)
        };
        overlay.remove();
        if (rect.w > 10 && rect.h > 10) {
            chrome.runtime.sendMessage({ type: 'CROP_AREA_SELECTED', rect });
        }
    };

    window.addEventListener('keydown', (e) => { if (e.key === 'Escape') overlay.remove(); }, { once: true });
})();