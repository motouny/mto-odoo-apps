(function () {
    'use strict';

    function setupPad(canvas) {
        var ctx = canvas.getContext('2d');
        var hiddenInput = document.getElementById(canvas.dataset.inputId);
        var clearBtn = document.querySelector('[data-clear-for="' + canvas.id + '"]');
        var drawing = false;
        var hasInk = false;

        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#1a1a1a';

        function pos(evt) {
            var rect = canvas.getBoundingClientRect();
            var point = evt.touches ? evt.touches[0] : evt;
            return {
                x: (point.clientX - rect.left) * (canvas.width / rect.width),
                y: (point.clientY - rect.top) * (canvas.height / rect.height),
            };
        }

        function start(evt) {
            evt.preventDefault();
            drawing = true;
            var p = pos(evt);
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
        }

        function move(evt) {
            if (!drawing) return;
            evt.preventDefault();
            var p = pos(evt);
            ctx.lineTo(p.x, p.y);
            ctx.stroke();
            hasInk = true;
        }

        function end() {
            if (!drawing) return;
            drawing = false;
            if (hasInk && hiddenInput) {
                hiddenInput.value = canvas.toDataURL('image/png');
            }
        }

        canvas.addEventListener('mousedown', start);
        canvas.addEventListener('mousemove', move);
        window.addEventListener('mouseup', end);
        canvas.addEventListener('touchstart', start);
        canvas.addEventListener('touchmove', move);
        canvas.addEventListener('touchend', end);

        if (clearBtn) {
            clearBtn.addEventListener('click', function (evt) {
                evt.preventDefault();
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                hasInk = false;
                if (hiddenInput) {
                    hiddenInput.value = '';
                }
            });
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('canvas.o_signature_pad').forEach(setupPad);
    });
})();
