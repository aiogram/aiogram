<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
    <meta name="format-detection" content="telephone=no"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="MobileOptimized" content="176"/>
    <meta name="HandheldFriendly" content="True"/>
    <meta name="robots" content="noindex,nofollow"/>
    <script src="https://telegram.org/js/telegram-web-app.js?1"></script>
    <script>
        function setThemeClass() {
            document.documentElement.className = Telegram.WebApp.colorScheme;
        }

        Telegram.WebApp.onEvent('themeChanged', setThemeClass);
        setThemeClass();

    </script>
    <style>
        body {
            font-family: sans-serif;
            background-color: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #222222);
            font-size: 16px;
            margin: 0;
            padding: 0;
            color-scheme: var(--tg-color-scheme);
        }

        a {
            color: var(--tg-theme-link-color, #2678b6);
        }

        button {
            display: block;
            width: 100%;
            font-size: 14px;
            margin: 15px 0;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            background-color: var(--tg-theme-button-color, #50a8eb);
            color: var(--tg-theme-button-text-color, #ffffff);
            cursor: pointer;
        }

        button[disabled] {
            opacity: 0.6;
            cursor: auto;
            pointer-events: none;
        }

        button.close_btn {
            /*position: fixed;*/
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 0;
            margin: 0;
            padding: 16px 20px;
            text-transform: uppercase;
        }

        section {
            padding: 15px 15px 65px;
            text-align: center;
        }

        p {
            margin: 40px 0 15px;
        }

        ul {
            text-align: left;
        }

        li {
            color: var(--tg-theme-hint-color, #a8a8a8);
        }

        textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 7px;
        }

        pre {
            background: rgba(0, 0, 0, .07);
            border-radius: 4px;
            padding: 4px;
            margin: 7px 0;
            word-break: break-all;
            word-break: break-word;
            white-space: pre-wrap;
            text-align: left;
        }

        .dark pre {
            background: rgba(255, 255, 255, .15);
        }

        .hint {
            font-size: .8em;
            color: var(--tg-theme-hint-color, #a8a8a8);
        }

        .ok {
            color: green;
        }

        .err {
            color: red;
        }

        #fixed_wrap {
            position: fixed;
            left: 0;
            right: 0;
            top: 0;
            transform: translateY(100vh);
        }

        .viewport_border,
        .viewport_stable_border {
            position: fixed;
            left: 0;
            right: 0;
            top: 0;
            height: var(--tg-viewport-height, 100vh);
            pointer-events: none;
        }

        .viewport_stable_border {
            height: var(--tg-viewport-stable-height, 100vh);
        }

        .viewport_border:before,
        .viewport_stable_border:before {
            content: attr(text);
            display: inline-block;
            position: absolute;
            background: gray;
            right: 0;
            top: 0;
            font-size: 7px;
            padding: 2px 4px;
            vertical-align: top;
        }

        .viewport_stable_border:before {
            background: green;
            left: 0;
            right: auto;
        }

        .viewport_border:after,
        .viewport_stable_border:after {
            content: '';
            display: block;
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            bottom: 0;
            border: 2px dashed gray;
        }

        .viewport_stable_border:after {
            border-color: green;
        }
    </style>
</head>
<body style="visibility: hidden;">
<section>
    <button id="main_btn" onclick="sendMessage('');">Send «Hello, World!»</button>
    <button id="with_webview_btn" onclick="sendMessage('', true);">
        Send «Hello, World!» with inline webview button
    </button>
    <button onclick="webviewExpand();">Expand Webview</button>
    <button onclick="toggleMainButton(this);">Hide Main Button</button>
    <div id="btn_status" class="hint" style="display: none;">
    </div>
    <p>Test links:</p>
    <ul>
        <li><a id="regular_link" href="?nextpage=1">Regular link #1</a> (opens inside webview)</li>
        <li><a href="https://telegram.org/" target="_blank">target="_blank" link</a> (opens outside
            webview)
        </li>
        <li><a href="javascript:window.open('https://telegram.org/');">window.open() link</a>
            (opens outside webview)
        </li>
        <li><a href="https://t.me/like">LikeBot t.me link</a> (opens inside Telegram app)</li>
        <li><a href="tg://resolve?domain=vote">VoteBot tg:// link</a> (does not open)</li>
    </ul>
    <p>Test permissions:</p>
    <ul>
        <li><a href="javascript:;" onclick="return requestLocation(this);">Request Location</a>
            <span></span></li>
        <li><a href="javascript:;" onclick="return requestVideo(this);">Request Video</a>
            <span></span></li>
        <li><a href="javascript:;" onclick="return requestAudio(this);">Request Audio</a>
            <span></span></li>
    </ul>
    <pre><code id="webview_data"></code></pre>
    <div class="hint">
        Data passed to webview.
        <span id="webview_data_status" style="display: none;">Checking hash...</span>
    </div>
    <pre><code id="theme_data"></code></pre>
    <div class="hint">
        Theme params
    </div>
</section>
<div class="viewport_border"></div>
<div class="viewport_stable_border"></div>
<script src="https://webappcontent.telegram.org/js/jquery.min.js"></script>
<script>
    Telegram.WebApp.ready();

    var initData = Telegram.WebApp.initData || '';
    var initDataUnsafe = Telegram.WebApp.initDataUnsafe || {};

    function sendMessage(msg_id, with_webview) {
        if (!initDataUnsafe.query_id) {
            alert('WebViewQueryId not defined');
            return;
        }
        $('button').prop('disabled', true);
        $('#btn_status').text('Sending...').removeClass('ok err').show();
        $.ajax('/demo/sendMessage', {
            type: 'POST',
            data: {
                _auth: initData,
                msg_id: msg_id || '',
                with_webview: !initDataUnsafe.receiver && with_webview ? 1 : 0
            },
            dataType: 'json',
            success: function (result) {
                $('button').prop('disabled', false);
                if (result.response) {
                    if (result.response.ok) {
                        $('#btn_status').html('Message sent successfully!').addClass('ok').show();
                    } else {
                        $('#btn_status').text(result.response.description).addClass('err').show();
                        alert(result.response.description);
                    }
                } else {
                    $('#btn_status').text('Unknown error').addClass('err').show();
                    alert('Unknown error');
                }
            },
            error: function (xhr) {
                $('button').prop('disabled', false);
                $('#btn_status').text('Server error').addClass('err').show();
                alert('Server error');
            }
        });
    }

    function webviewExpand() {
        Telegram.WebApp.expand();
    }

    function webviewClose() {
        Telegram.WebApp.close();
    }

    function requestLocation(el) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function (position) {
                $(el).next('span').html('(' + position.coords.latitude + ', ' + position.coords.longitude + ')').attr('class', 'ok');
            });
        } else {
            $(el).next('span').html('Geolocation is not supported in this browser.').attr('class', 'err');
        }
        return false;
    }

    function requestVideo(el) {
        if (navigator.mediaDevices) {
            navigator.mediaDevices.getUserMedia({
                audio: false,
                video: true
            }).then(function (stream) {
                $(el).next('span').html('(Access granted)').attr('class', 'ok');
            });
        } else {
            $(el).next('span').html('Media devices is not supported in this browser.').attr('class', 'err');
        }
        return false;
    }

    function requestAudio(el) {
        if (navigator.mediaDevices) {
            navigator.mediaDevices.getUserMedia({
                audio: true,
                video: false
            }).then(function (stream) {
                $(el).next('span').html('(Access granted)').attr('class', 'ok');
            });
        } else {
            $(el).next('span').html('Media devices is not supported in this browser.').attr('class', 'err');
        }
        return false;
    }

    Telegram.WebApp.onEvent('themeChanged', function () {
        $('#theme_data').html(JSON.stringify(Telegram.WebApp.themeParams, null, 2));
    });

    $('#main_btn').toggle(!!initDataUnsafe.query_id);
    $('#with_webview_btn').toggle(!!initDataUnsafe.query_id && !initDataUnsafe.receiver);
    // $('#data_btn').toggle(!initDataUnsafe.query_id || !initDataUnsafe.receiver);
    $('#webview_data').html(JSON.stringify(initDataUnsafe, null, 2));
    $('#theme_data').html(JSON.stringify(Telegram.WebApp.themeParams, null, 2));
    $('#regular_link').attr('href', $('#regular_link').attr('href') + location.hash);
    $('#text_field').focus();
    if (initDataUnsafe.query_id && initData) {
        $('#webview_data_status').show();
        $.ajax('/demo/checkData', {
            type: 'POST',
            data: {_auth: initData},
            dataType: 'json',
            success: function (result) {
                if (result.ok) {
                    $('#webview_data_status').html('Hash is correct').addClass('ok');
                } else {
                    $('#webview_data_status').html(result.error).addClass('err');
                }
            },
            error: function (xhr) {
                $('#webview_data_status').html('Server error').addClass('err');
            }
        });
    }
    $('body').css('visibility', '');
    Telegram.WebApp.MainButton
        .setText('CLOSE WEBVIEW')
        .show()
        .onClick(function () {
            webviewClose();
        });

    function toggleMainButton(el) {
        var mainButton = Telegram.WebApp.MainButton;
        if (mainButton.isVisible) {
            mainButton.hide();
            el.innerHTML = 'Show Main Button';
        } else {
            mainButton.show();
            el.innerHTML = 'Hide Main Button';
        }
    }

    function round(val, d) {
        var k = Math.pow(10, d || 0);
        return Math.round(val * k) / k;
    }

    function setViewportData() {
        $('.viewport_border').attr('text', window.innerWidth + ' x ' + round(Telegram.WebApp.viewportHeight, 2));
        $('.viewport_stable_border').attr('text', window.innerWidth + ' x ' + round(Telegram.WebApp.viewportStableHeight, 2) + ' | is_expanded: ' + (Telegram.WebApp.isExpanded ? 'true' : 'false'));
    }

    Telegram.WebApp.onEvent('viewportChanged', setViewportData);
    setViewportData();


</script>
</body>
</html>
<!-- page generated in 1.11ms -->
