// API設定
const API_BASE_URL = window.location.origin || 'http://localhost:8000';

// DOM要素
const elements = {
    // フォーム要素
    theme: document.getElementById('theme'),
    style: document.getElementById('style'),
    model: document.getElementById('model'),
    use_ai: document.getElementById('use_ai'),
    bpm: document.getElementById('bpm'),
    key: document.getElementById('key'),
    custom_prompt: document.getElementById('custom_prompt'),
    direct_lyrics: document.getElementById('direct_lyrics'),
    
    // ボタン
    generateBtn: document.getElementById('generateBtn'),
    composeBtn: document.getElementById('composeBtn'),
    composeFromLyricsBtn: document.getElementById('composeFromLyricsBtn'),
    downloadBtn: document.getElementById('downloadBtn'),
    listSongsBtn: document.getElementById('listSongsBtn'),
    
    // 結果表示
    resultsSection: document.getElementById('resultsSection'),
    loading: document.getElementById('loading'),
    error: document.getElementById('error'),
    lyricsResult: document.getElementById('lyricsResult'),
    lyricsContent: document.getElementById('lyricsContent'),
    lyricsMetadata: document.getElementById('lyricsMetadata'),
    mp3Result: document.getElementById('mp3Result'),
    mp3Info: document.getElementById('mp3Info'),
    audioPlayer: document.getElementById('audioPlayer'),
    historyList: document.getElementById('historyList')
};

// ユーティリティ関数
function showLoading() {
    elements.loading.style.display = 'block';
    elements.error.style.display = 'none';
    elements.lyricsResult.style.display = 'none';
    elements.mp3Result.style.display = 'none';
    elements.resultsSection.style.display = 'block';
}

function hideLoading() {
    elements.loading.style.display = 'none';
}

function showError(message) {
    elements.error.textContent = `❌ エラー: ${message}`;
    elements.error.style.display = 'block';
    hideLoading();
}

function hideError() {
    elements.error.style.display = 'none';
}

// API呼び出し関数
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// 歌詞生成
async function generateLyrics() {
    showLoading();
    hideError();
    
    try {
        const prompt = {
            theme: elements.theme.value,
            style: elements.style.value,
            model: elements.model.value,
            use_ai: elements.use_ai.value === 'true',
            bpm: parseInt(elements.bpm.value) || undefined,
            key: elements.key.value || undefined,
            custom_prompt: elements.custom_prompt.value || undefined
        };
        
        const result = await apiCall('/generate', 'POST', prompt);
        
        // 歌詞を表示
        elements.lyricsContent.textContent = result.song.lyrics.join('\n');
        
        // メタデータを表示
        elements.lyricsMetadata.innerHTML = `
            <div class="metadata-item">
                <span class="metadata-label">タイトル:</span>
                <span class="metadata-value">${result.song.title}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">BPM:</span>
                <span class="metadata-value">${result.song.bpm}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">キー:</span>
                <span class="metadata-value">${result.song.key}</span>
            </div>
        `;
        
        elements.lyricsResult.style.display = 'block';
        hideLoading();
        
    } catch (error) {
        showError(error.message);
    }
}

// 作曲（歌詞生成 + 作曲 + MP3出力）
async function composeSong() {
    showLoading();
    hideError();
    
    try {
        const prompt = {
            theme: elements.theme.value,
            style: elements.style.value,
            model: elements.model.value,
            use_ai: elements.use_ai.value === 'true',
            bpm: parseInt(elements.bpm.value) || undefined,
            key: elements.key.value || undefined,
            custom_prompt: elements.custom_prompt.value || undefined
        };
        
        const result = await apiCall('/compose', 'POST', { prompt });
        
        // MP3結果を表示
        elements.mp3Info.innerHTML = `
            <div class="metadata-item">
                <span class="metadata-label">ファイル名:</span>
                <span class="metadata-value">${result.filename}</span>
            </div>
            ${result.metadata ? `
                <div class="metadata-item">
                    <span class="metadata-label">タイトル:</span>
                    <span class="metadata-value">${result.metadata.title || 'N/A'}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">BPM:</span>
                    <span class="metadata-value">${result.metadata.bpm || 'N/A'}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">キー:</span>
                    <span class="metadata-value">${result.metadata.key || 'N/A'}</span>
                </div>
            ` : ''}
        `;
        
        // オーディオプレーヤー
        const audioUrl = `${API_BASE_URL}${result.download_url}`;
        elements.audioPlayer.innerHTML = `
            <audio controls>
                <source src="${audioUrl}" type="audio/mpeg">
                お使いのブラウザはオーディオタグをサポートしていません。
            </audio>
        `;
        
        // ダウンロードボタンの設定
        elements.downloadBtn.onclick = () => downloadMP3(result.filename);
        
        elements.mp3Result.style.display = 'block';
        hideLoading();
        
    } catch (error) {
        showError(error.message);
    }
}

// 直接歌詞から作曲
async function composeFromLyrics() {
    const lyrics = elements.direct_lyrics.value.trim();
    
    if (!lyrics) {
        showError('歌詞を入力してください');
        return;
    }
    
    showLoading();
    hideError();
    
    try {
        const result = await apiCall('/compose', 'POST', {
            lyrics: lyrics,
            output_filename: `custom_${Date.now()}.mp3`
        });
        
        // MP3結果を表示
        elements.mp3Info.innerHTML = `
            <div class="metadata-item">
                <span class="metadata-label">ファイル名:</span>
                <span class="metadata-value">${result.filename}</span>
            </div>
        `;
        
        // オーディオプレーヤー
        const audioUrl = `${API_BASE_URL}${result.download_url}`;
        elements.audioPlayer.innerHTML = `
            <audio controls>
                <source src="${audioUrl}" type="audio/mpeg">
                お使いのブラウザはオーディオタグをサポートしていません。
            </audio>
        `;
        
        // ダウンロードボタンの設定
        elements.downloadBtn.onclick = () => downloadMP3(result.filename);
        
        elements.mp3Result.style.display = 'block';
        hideLoading();
        
    } catch (error) {
        showError(error.message);
    }
}

// MP3ダウンロード
function downloadMP3(filename) {
    const url = `${API_BASE_URL}/download/${filename}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 楽曲一覧取得
async function listSongs() {
    showLoading();
    hideError();
    
    try {
        const result = await apiCall('/list', 'GET');
        
        if (result.files && result.files.length > 0) {
            elements.historyList.innerHTML = result.files.map(file => `
                <div class="history-item">
                    <div class="history-item-info">
                        <div class="history-item-name">${file.filename}</div>
                        <div class="history-item-meta">
                            サイズ: ${(file.size / 1024).toFixed(2)} KB | 
                            作成日: ${new Date(file.created * 1000).toLocaleString('ja-JP')}
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn btn-small btn-primary" onclick="downloadMP3('${file.filename}')">
                            ⬇️ ダウンロード
                        </button>
                        <button class="btn btn-small btn-info" onclick="playMP3('${file.filename}')">
                            ▶️ 再生
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            elements.historyList.innerHTML = '<p>生成された楽曲はありません</p>';
        }
        
        hideLoading();
        
    } catch (error) {
        showError(error.message);
    }
}

// MP3再生
function playMP3(filename) {
    const audioUrl = `${API_BASE_URL}/download/${filename}`;
    elements.audioPlayer.innerHTML = `
        <audio controls autoplay>
            <source src="${audioUrl}" type="audio/mpeg">
            お使いのブラウザはオーディオタグをサポートしていません。
        </audio>
    `;
    elements.mp3Result.style.display = 'block';
    elements.mp3Result.scrollIntoView({ behavior: 'smooth' });
}

// イベントリスナー
elements.generateBtn.addEventListener('click', generateLyrics);
elements.composeBtn.addEventListener('click', composeSong);
elements.composeFromLyricsBtn.addEventListener('click', composeFromLyrics);
elements.listSongsBtn.addEventListener('click', listSongs);

// 初期化: APIの状態確認
async function init() {
    try {
        const health = await apiCall('/');
        console.log('API connected:', health);
        
        // 利用可能なモデルを表示
        if (health.available_models) {
            console.log('Available models:', health.available_models);
        }
    } catch (error) {
        console.error('Failed to connect to API:', error);
        showError('APIに接続できません。サーバーが起動しているか確認してください。');
    }
}

// ページ読み込み時に初期化
init();

// グローバル関数（HTMLから呼び出し用）
window.downloadMP3 = downloadMP3;
window.playMP3 = playMP3;

