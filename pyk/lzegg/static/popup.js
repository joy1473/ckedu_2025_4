/**
 * 전역 상태 관리
 */
let cachedAllData = [];
window.currentFilter = 'winners';
let currentSortCol = 'profit';
let isAsc = false;
let SELECTEDROWELEMENT_ESC = null;

const stockColorMap = {};
const colorPalette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f43f5e', '#84cc16', '#a855f7'];

function getStockColor(in_code) {
    if (!stockColorMap[in_code]) {
        const index = Object.keys(stockColorMap).length % colorPalette.length;
        stockColorMap[in_code] = colorPalette[index];
    }
    return stockColorMap[in_code];
}

/**
 * 초기 진입점
 */
async function getStockModalDOM(in_userId) {
    const existingModal = document.getElementById('stockModal');
    if (existingModal) existingModal.remove();

    injectModalHTML();      
    
    const titleElem = document.querySelector('#stockModal h2');
    if (titleElem) titleElem.innerText = `📊 ${in_userId} 유저 자산 상세 분석 리포트`;
    
    try {
        // 1. [로그 확인용] 랭킹 API를 강제로 다시 호출합니다. (주석 해제)
        // 이 코드가 실행되어야 백엔드 터미널에 로그가 찍힙니다.
        loadGlobalTopRanker(in_userId); 

        // 2. 현재 유저 상세 데이터 로드
        const res = await fetch(`/apiEsc/popup-status?in_userId=${in_userId}`);
        const data = await res.json();
        
        // 3. 내 손익 계산 및 상단 박스 반영 (랭킹 정보는 위에서 덮어씌울 것임)
        updateTopUserSummary(in_userId, data);
        updateStockDisplay(data); 

    } catch (e) {
        console.error("데이터 로드 실패:", e);
    }
}
/**
 * 상단 파란 박스 영역에 현재 조회 유저 정보를 표시하는 함수 (신설)
 */
function updateTopUserSummary(in_userId, in_data) {
    const infoElem = document.getElementById('bestUserInfo');
    const rateElem = document.getElementById('bestUserRate');
    if (!infoElem || !rateElem) return;

    // 현재 유저의 총 평가손익 계산
    const totalProfit = in_data.reduce((sum, s) => sum + ((parseFloat(s.currentPrice) - parseFloat(s.buyPrice)) * parseInt(s.quantity)), 0);
    const color = totalProfit >= 0 ? '#ef4444' : '#3b82f6';

    // UI 주입: 왼쪽은 '조회 대상', 오른쪽은 '수익금'으로 고정
    infoElem.innerHTML = `
        <div style="color: #94a3b8; font-size: 11px;">현재 분석 대상</div>
        <div style="font-size: 18px; font-weight: bold; color: #f8fafc;">${in_userId}</div>
        <div id="globalRankText" style="color: #fbbf24; font-size: 11px; margin-top: 4px;">🏆 랭킹 정보 로딩 중...</div>
    `;
    rateElem.innerHTML = `
        <div style="text-align: right;">
            <div style="font-size: 11px; color: #94a3b8;">조회 유저 총 손익</div>
            <div style="color: ${color}; font-size: 24px; font-weight: 900;">${Math.floor(totalProfit).toLocaleString()}원</div>
        </div>
    `;
}
/**
 * 랭킹 정보 갱신 (명확하게 innerHTML/innerText 주입)
 * * @param {string} targetId - 현재 리포트를 보고 있는 유저 ID
 */
async function loadGlobalTopRanker(targetId = "Unknown") {
    const infoElem = document.getElementById('bestUserInfo');
    const rateElem = document.getElementById('bestUserRate');

    try {
        const res = await fetch(`/apiEsc/total-rank-top1?t=${new Date().getTime()}`);
        const topData = await res.json();
        
        // 에러가 났더라도 '로딩 중' 문구는 지워줘야 합니다.
        if (topData.error) {
            console.error("서버 에러:", topData.message);
            if(infoElem) infoElem.innerHTML = `<div style="color: #94a3b8; font-size: 11px;">분석 중: ${targetId}</div><div style="color: #f87171; font-size: 11px;">⚠️ 랭킹 데이터 연결 실패</div>`;
            return;
        }

        if (infoElem && rateElem) {
            infoElem.innerHTML = `
                <div style="color: #94a3b8; font-size: 11px;">분석 중: <strong>${targetId}</strong></div>
                <div style="color: #fbbf24; font-size: 11px; margin-top: 4px;">🏆 전체 1위: ${topData.user_name || topData.user_id}</div>
            `;
            rateElem.innerHTML = `
                <div style="text-align: right;">
                    <div style="font-size: 11px; color: #94a3b8;">1위 누적 수익</div>
                    <div style="color: #ef4444; font-size: 20px; font-weight: 800;">${Math.floor(topData.total_profit).toLocaleString()}원</div>
                </div>
            `;
        }
    } catch (e) {
        console.error("네트워크 에러:", e);
        if(infoElem) infoElem.innerHTML = `<div style="color: #f87171; font-size: 11px;">⚠️ 서버 연결 확인 필요</div>`;
    }
}

/**
 * UI 데이터 가공 및 통합 렌더링
 */
function updateStockDisplay(in_data) {
    if (!in_data || in_data.length === 0) return;

    cachedAllData = in_data.map(s => {
        const bp = parseFloat(s.buyPrice) || 0, cp = parseFloat(s.currentPrice) || 0, qt = parseInt(s.quantity) || 0;
        const invest = bp * qt, profit = (cp - bp) * qt;
        return { ...s, invest, profit, rate: invest > 0 ? (profit / invest) * 100 : 0 };
    });

    renderTop3Report(cachedAllData);
    renderTotalSummary(cachedAllData);
    renderStockList(applyFilterAndSort(cachedAllData));
    
    let topTickers = [...cachedAllData]
        .sort((a, b) => Math.abs(b.profit) - Math.abs(a.profit))
        .map(s => s.code);
    
    let uniqueTickers = [...new Set(topTickers)].slice(0, 5);
    
    const fallback = [
        {code: '005930.KS', name: '삼성전자'}, 
        {code: '000660.KS', name: 'SK하이닉스'}, 
        {code: '035420.KS', name: 'NAVER'}, 
        {code: '035720.KS', name: '카카오'}, 
        {code: '005380.KS', name: '현대차'}
    ];

    for (let f of fallback) {
        if (uniqueTickers.length >= 5) break;
        if (!uniqueTickers.includes(f.code)) uniqueTickers.push(f.code);
    }

    renderCombinedChartWithProgress(uniqueTickers, cachedAllData);
}
/**
 * 다중 차트 렌더링 (동기화 보장)
 */
async function renderCombinedChartWithProgress(in_tickers, in_allData, in_clickedRow = null) {
    const chartElement = document.getElementById('mainDynamicChart');
    if (!chartElement) return;

    try {
        const results = await Promise.all(in_tickers.map(t => 
            fetch(`/apiEsc/stock-chart-data?in_code=${t}&t=${new Date().getTime()}`).then(r => r.json())
        ));
        
        const traces = results.map((json, idx) => {
            if (json.error || !json.dates) return null;
            const ticker = in_tickers[idx];
            // 내 보유 목록에 있으면 그 이름을 쓰고, 없으면 코드를 표시
            const info = in_allData.find(d => d.code === ticker);
            const fallbackNames = {'005930.KS':'삼성전자','000660.KS':'SK하이닉스','035420.KS':'NAVER','035720.KS':'카카오','005380.KS':'현대차'};

            return {
                x: json.dates,
                y: json.closes.map(v => v / 10000),
                name: info ? info.name : (fallbackNames[ticker] || ticker),
                type: 'scatter', 
                mode: 'lines',
                line: { width: 2.5, shape: 'spline' }
            };
        }).filter(t => t !== null);

        Plotly.newPlot(chartElement, traces, {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8', size: 11 },
            margin: { t: 40, b: 50, l: 30, r: 50 },
            legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
            xaxis: { gridcolor: '#1e293b' },
            yaxis: { gridcolor: '#1e293b', side: 'right', title: '(만원)' }
        }, {responsive: true, displayModeBar: false});
    } catch (e) { console.error(e); }
}

function renderStockList(in_stocks) {
    const listContainer = document.getElementById('stockListContainer');
    if(!listContainer) return;

    const getArr = (key) => currentSortCol === key ? (isAsc ? '▲' : '▼') : '↕';
    let html = `<table style="width:100%; border-collapse:collapse; font-size:10px; table-layout:fixed;">
        <thead style="position:sticky; top:0; z-index:10; background:#1e293b;">
            <tr style="color:#94a3b8; border-bottom:1px solid #334155;">
                <th class="sort-header" onclick="sortData('date')" style="width:18%;">날짜 ${getArr('date')}</th>
                <th class="sort-header" onclick="sortData('name')" style="width:24%; text-align:left; padding-left:5px;">종목 ${getArr('name')}</th>
                <th class="sort-header" onclick="sortData('invest')" style="width:20%; text-align:right;">투자원금 ${getArr('invest')}</th>
                <th class="sort-header" onclick="sortData('rate')" style="width:16%; text-align:right;">수익률 ${getArr('rate')}</th>
                <th class="sort-header" onclick="sortData('profit')" style="width:22%; text-align:right; padding-right:8px;">손익금액 ${getArr('profit')}</th>
            </tr>
        </thead><tbody>`;

    in_stocks.forEach(s => {
        const color = s.profit >= 0 ? '#ff4d4d' : '#3b82f6';
        // 클릭 시 리스트의 데이터를 참고하여 해당 종목만 차트에 그림
        html += `<tr class="stock-row" onclick="renderCombinedChartWithProgress(['${s.code}'], cachedAllData, this)" 
                     style="border-bottom:1px solid #1e293b; cursor:pointer;">
            <td style="padding:10px 2px; text-align:center; color:#64748b;">${s.date}</td>
            <td style="font-weight:bold; color:#f8fafc; padding-left:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${s.name}</td>
            <td style="text-align:right; color:#cbd5e1;">${Math.floor(s.invest).toLocaleString()}</td>
            <td style="text-align:right; color:${color}; font-weight:bold;">${s.rate.toFixed(1)}%</td>
            <td style="text-align:right; color:${color}; padding-right:8px; font-weight:bold;">${Math.floor(s.profit).toLocaleString()}</td>
        </tr>`;
    });
    listContainer.innerHTML = html + '</tbody></table>';
}

function renderTop3Report(in_data) {
    const winners = [...in_data].filter(s => s.profit > 0).sort((a,b)=>b.profit-a.profit).slice(0,3);
    const losers = [...in_data].filter(s => s.profit < 0).sort((a,b)=>a.profit-b.profit).slice(0,3);
    const container = document.getElementById('top3ReportContainer');
    if(!container) return;

    container.innerHTML = `
        <div style="display:flex; gap:12px; margin-bottom:12px;">
            <div style="flex:1; padding:10px; background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.2); border-top:3px solid #ef4444; border-radius:8px;">
                <div style="color:#ef4444; font-weight:bold; font-size:11px; margin-bottom:5px;">🚀 수익 기여 TOP 3</div>
                ${winners.map(s => `<div style="display:flex; justify-content:space-between; font-size:10px; color:#cbd5e1;"><span>${s.name}</span><b>+${Math.floor(s.profit).toLocaleString()}</b></div>`).join('')}
            </div>
            <div style="flex:1; padding:10px; background:rgba(59,130,246,0.05); border:1px solid rgba(59,130,246,0.2); border-top:3px solid #3b82f6; border-radius:8px;">
                <div style="color:#60a5fa; font-weight:bold; font-size:11px; margin-bottom:5px;">💧 손실 기여 TOP 3</div>
                ${losers.map(s => `<div style="display:flex; justify-content:space-between; font-size:10px; color:#cbd5e1;"><span>${s.name}</span><b>${Math.floor(s.profit).toLocaleString()}</b></div>`).join('')}
            </div>
        </div>`;
}

function renderTotalSummary(in_data) {
    const totalInvest = in_data.reduce((sum, s) => sum + s.invest, 0);
    const totalProfit = in_data.reduce((sum, s) => sum + s.profit, 0);
    const totalRate = totalInvest > 0 ? (totalProfit / totalInvest) * 100 : 0;
    const color = totalProfit >= 0 ? '#ff4d4d' : '#3b82f6';
    const container = document.getElementById('totalSummaryContainer');
    if(!container) return;

    container.innerHTML = `
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;"><div style="font-size:10px; color:#94a3b8;">총 투자원금</div><div style="font-size:14px; font-weight:bold;">${Math.floor(totalInvest).toLocaleString()}원</div></div>
            <div style="text-align:center;"><div style="font-size:10px; color:#94a3b8;">총 평가손익</div><div style="font-size:14px; font-weight:bold; color:${color};">${Math.floor(totalProfit).toLocaleString()}원</div></div>
            <div style="text-align:center;"><div style="font-size:10px; color:#94a3b8;">누적 수익률</div><div style="font-size:14px; font-weight:bold; color:${color};">${totalRate.toFixed(2)}%</div></div>
            <button onclick="document.getElementById('stockModal').remove();document.getElementById('modalOverlay').remove();" style="background:#334155; color:white; border:none; padding:8px 20px; border-radius:6px; cursor:pointer;">닫기</button>
        </div>`;
}

function applyFilterAndSort(in_data) {
    if (!in_data || in_data.length === 0) return [];
    let filtered = (window.currentFilter === 'winners') ? in_data.filter(s => s.profit >= 0) : in_data.filter(s => s.profit < 0);
    filtered.sort((a, b) => {
        let valA = a[currentSortCol], valB = b[currentSortCol];
        if (typeof valA === 'string') return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        return isAsc ? valA - valB : valB - valA;
    });
    return filtered;
}

function sortData(in_key) {
    if (currentSortCol === in_key) isAsc = !isAsc;
    else { currentSortCol = in_key; isAsc = false; }
    renderStockList(applyFilterAndSort(cachedAllData));
}

function injectModalHTML() {
    const html = `
        <div id="modalOverlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:9998;"></div>
        <div id="stockModal" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:98%;max-width:1300px;height:90vh;background:#0f172a;z-index:9999;display:flex;flex-direction:column;color:#f8fafc;border-radius:12px;border:1px solid #334155;overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 15px; border-bottom:1px solid #1e293b;">
                <h2 style="margin:0; font-size:16px;">🏆 모의투자 자산 분석 리포트</h2>
                <button onclick="document.getElementById('stockModal').remove();document.getElementById('modalOverlay').remove();" style="background:transparent; border:none; color:#94a3b8; font-size:24px; cursor:pointer;">&times;</button>
            </div>
            <div style="flex:1; display:flex; flex-direction:column; padding:12px; overflow:hidden; position:relative;">
                <div id="globalBestUser" style="background: rgba(30, 41, 59, 0.5); border: 1px dashed #3b82f6; padding: 12px; margin-bottom: 15px; border-radius: 8px; display: flex; align-items: center; justify-content: center; gap: 40px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size: 24px;">🏆</span>
                        <div id="bestUserInfo" style="text-align: left; line-height:1.4;">분석 중...</div>
                    </div>
                    <div style="width:1px; height:30px; background:#334155;"></div>
                    <div id="bestUserRate" style="font-size: 20px; font-weight: 800; color: #ef4444;">0원</div>
                </div>

                <div style="display:flex; gap:15px; margin-bottom:10px; font-size:12px;">
                    <label style="cursor:pointer;"><input type="radio" name="filter" value="winners" checked onclick="window.currentFilter='winners'; renderStockList(applyFilterAndSort(cachedAllData))"> 수익종목 TOP</label>
                    <label style="cursor:pointer;"><input type="radio" name="filter" value="losers" onclick="window.currentFilter='losers'; renderStockList(applyFilterAndSort(cachedAllData))"> 손실종목 TOP</label>
                </div>

                <div id="chartLoading" style="position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.9); z-index:100; display:none; align-items:center; justify-content:center;">로딩 중...</div>
                <div id="top3ReportContainer"></div>
                
                <div style="flex:1; display:flex; gap:12px; overflow:hidden;">
                    <div id="mainDynamicChart" style="flex:1.6; background:#1e293b; border-radius:8px;"></div>
                    <div id="stockListContainer" style="flex:1.4; background:#1e293b; border-radius:8px; overflow-y:auto;"></div>
                </div>
                <div id="totalSummaryContainer" style="margin-top:12px;"></div>
            </div>
        </div>`;
    document.body.insertAdjacentHTML('beforeend', html);
}