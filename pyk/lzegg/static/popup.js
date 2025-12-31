let cachedAllData = [];
window.currentFilter = 'winners'; 
let currentSortCol = 'profit';      
let isAsc = false;               
// 클릭된 행의 상태를 저장하기 위한 변수
let SELECTEDROWELEMENT_ESC = null;

const stockColorMap = {};
const colorPalette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f43f5e', '#84cc16', '#a855f7'];

/**
 * @description 주석 색상 팔레트에서 종목 코드별로 고유한 색상을 할당
 * @param {string} in_code - 주식 종목 코드
 * @returns {string} 할당된 HEX 색상 코드
 */
function getStockColor(in_code) {
    if (!stockColorMap[in_code]) {
        const index = Object.keys(stockColorMap).length % colorPalette.length;
        stockColorMap[in_code] = colorPalette[index];
    }
    return stockColorMap[in_code];
}

/**
 * @description 분석 리포트용 모달(Modal) 창의 HTML 구조를 생성하고 DOM에 삽입
 * @returns {void}
 */
function injectModalHTML() {
    if (document.getElementById('stockModal')) return; 
    const container = document.getElementById('modalContainer') || document.body;
    
    const modalHTML = `
        <style>
            #chartLoading {
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(15, 23, 42, 0.95); display: flex;
                flex-direction: column; align-items: center; justify-content: center;
                z-index: 99999; color: #f8fafc;
            }
            .sort-header { cursor: pointer; background: #1e293b; padding: 12px 2px !important; transition: 0.2s; user-select: none; font-size: 11px; }
            .sort-header:hover { background: #334155 !important; color: #fff; }
            .sort-indicator { font-size: 9px; margin-left: 2px; color: #3b82f6; }
            
            #stockListContainer::-webkit-scrollbar { width: 4px; }
            #stockListContainer::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
            .stock-row:hover { background: #334155 !important; }
        </style>
        <div id="modalOverlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:9998;"></div>
        <div id="stockModal" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:98%;max-width:1300px;height:90vh;background:#0f172a;z-index:9999;display:flex;flex-direction:column;color:#f8fafc;border-radius:12px;border:1px solid #334155;overflow:hidden;">
            
            <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 15px; border-bottom:1px solid #1e293b;">
                <h2 style="margin:0; font-size:16px;">🏆 모의투자 성공 사례 자산 분석 리포트</h2>
                <button onclick="window.close()" style="background:transparent; border:none; color:#94a3b8; font-size:24px; cursor:pointer;">&times;</button>
            </div>

            <div style="flex:1; display:flex; flex-direction:column; padding:12px; overflow:hidden; position:relative;">
                <div id="chartLoading"><img src="https://i.gifer.com/ZZ5H.gif" width="40"><p style="margin-top:10px; font-size:12px;">차트 데이터 동기화 중...</p></div>

                <div style="margin-bottom:12px; display:flex; gap:15px;">
                    <label style="font-size:12px; cursor:pointer;"><input type="radio" name="filter" value="winners" checked onclick="window.currentFilter='winners'; updateStockDisplay(cachedAllData)"> 수익종목 TOP5</label>
                    <label style="font-size:12px; cursor:pointer;"><input type="radio" name="filter" value="losers" onclick="window.currentFilter='losers'; updateStockDisplay(cachedAllData)"> 손실종목 TOP5</label>
                </div>

                <div id="top3ReportContainer" style="margin-bottom:12px;"></div>
                
                <div style="flex:1; display:flex; gap:12px; overflow:hidden;">
                    <div id="innerChartContainer" style="flex:1.6; background:#1e293b; border-radius:8px; position:relative;">
                        <div id="mainDynamicChart" style="width:100%; height:100%;"></div>
                    </div>
                    <div id="stockListContainer" style="flex:1.6; background:#1e293b; border-radius:8px; overflow-y:auto; border:1px solid #334155;"></div>
                </div>

                <div id="totalSummaryContainer" style="margin-top:12px; padding:12px; background:#1e293b; border-radius:8px; display:grid; grid-template-columns: repeat(4, 1fr); gap:10px;"></div>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', modalHTML);
}
/**
 * @description 테이블 헤더의 현재 정렬 상태에 따른 화살표 아이콘 반환
 * @param {string} in_key - 정렬 기준 컬럼명
 * @returns {string} HTML span 태그 형태의 아이콘
 */
function getSortIndicator(in_key) {
    if (currentSortCol !== in_key) return '<span class="sort-indicator">↕</span>';
    return isAsc ? '<span class="sort-indicator">▲</span>' : '<span class="sort-indicator">▼</span>';
}

/**
 * @description 종목 리스트 데이터를 테이블 형태로 렌더링
 * @param {Array} in_stocks - 가공된 종목 데이터 배열
 * @returns {void}
 */
function renderStockList(in_stocks) {
    const listContainer = document.getElementById('stockListContainer');
    let html = `<table style="width:100%; border-collapse:collapse; font-size:10px; table-layout:fixed;">
        <thead style="position:sticky; top:0; z-index:10; background:#1e293b;">
            <tr style="color:#94a3b8; border-bottom:1px solid #334155;">
                <th class="sort-header" onclick="sortData('date')" style="width:18%;">날짜 ${getSortIndicator('date')}</th>
                <th class="sort-header" onclick="sortData('name')" style="width:24%; text-align:left; padding-left:5px;">종목 ${getSortIndicator('name')}</th>
                <th class="sort-header" onclick="sortData('invest')" style="width:20%; text-align:right;">투자원금 ${getSortIndicator('invest')}</th>
                <th class="sort-header" onclick="sortData('rate')" style="width:16%; text-align:right;">수익률 ${getSortIndicator('rate')}</th>
                <th class="sort-header" onclick="sortData('profit')" style="width:22%; text-align:right; padding-right:8px;">손익금액 ${getSortIndicator('profit')}</th>
            </tr>
        </thead><tbody>`;
    if (in_stocks.length === 0) {
        html += `<tr><td colspan="5" style="text-align:center; padding:20px; color:#94a3b8;">데이터가 없습니다.</td></tr>`;
    } else {
        in_stocks.forEach(s => {
            const color = s.rate >= 0 ? '#ff4d4d' : '#3b82f6';
            // onclick 시 this(현재 행 엘리먼트)를 전달하여 배경색 변경
            html += `<tr class="stock-row" onclick="renderCombinedChartWithProgress(['${s.code}'], cachedAllData, this)" 
                        style="border-bottom:1px solid #1e293b; cursor:pointer; transition: background 0.2s;">
                <td style="padding:10px 2px; text-align:center; color:#64748b;">${s.date}</td>
                <td style="font-weight:bold; color:#f8fafc; padding-left:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${s.name}</td>
                <td style="text-align:right; color:#cbd5e1;">${Math.floor(s.invest).toLocaleString()}</td>
                <td style="text-align:right; color:${color}; font-weight:bold;">${s.rate.toFixed(1)}%</td>
                <td style="text-align:right; color:${color}; padding-right:8px; font-weight:bold;">${Math.floor(s.profit).toLocaleString()}</td>
            </tr>`;
        });
    }
    listContainer.innerHTML = html + '</tbody></table>';
}
/**
 * @description 컬럼 헤더 클릭 시 데이터를 정렬하고 리스트를 갱신
 * @param {string} in_key - 정렬할 컬럼 키 (date, name, invest, rate, profit)
 * @returns {void}
 */
function sortData(in_key) {
    if (currentSortCol === in_key) isAsc = !isAsc;
    else { currentSortCol = in_key; isAsc = (in_key === 'name' ? true : false); }
    renderStockList(applyFilterAndSort(cachedAllData));
}

/**
 * @description 수익/손실 필터 및 정렬 옵션을 적용하여 데이터 처리
 * @param {Array} in_data - 원본 종목 데이터 배열
 * @returns {Array} 필터 및 정렬이 완료된 데이터 배열
 */
function applyFilterAndSort(in_data) {
    if (!in_data) return [];
    let processed = in_data.map(s => ({ 
        ...s, 
        profit: (s.currentPrice - s.buyPrice) * s.quantity, 
        invest: s.buyPrice * s.quantity,
        rate: ((s.currentPrice - s.buyPrice) / s.buyPrice) * 100
    }));
    
    let filtered = (window.currentFilter === 'winners') ? processed.filter(s => s.profit >= 0) : processed.filter(s => s.profit < 0);

    filtered.sort((a, b) => {
        let valA = a[currentSortCol];
        let valB = b[currentSortCol];
        if (valA < valB) return isAsc ? -1 : 1;
        if (valA > valB) return isAsc ? 1 : -1;
        return 0;
    });
    return filtered;
}

/**
 * @description 선택된 종목들의 과거 시세 데이터를 가져와 Plotly 차트 생성
 * @param {Array} in_tickers - 차트에 표시할 종목 코드 배열
 * @param {Array} in_allData - 전체 종목 정보 (이름 매칭용)
 * @param {HTMLElement} in_clickedRow - 클릭된 테이블 행 요소 (강조 표시용)
 * @returns {Promise<void>}
 */
async function renderCombinedChartWithProgress(in_tickers, in_allData, in_clickedRow = null) {
    const loading = document.getElementById('chartLoading');
    if(loading) loading.style.display = 'flex';

    // 행 강조 로직: 마우스 오버(#334155)와 확실히 구분되는 색상 사용
    if (in_clickedRow && in_clickedRow instanceof HTMLElement) {
        if (SELECTEDROWELEMENT_ESC) {
            SELECTEDROWELEMENT_ESC.style.background = 'transparent';
        }
        // 클릭된 행은 더 밝고 투명도가 낮은 남색(Slate-600) 계열로 설정
        in_clickedRow.style.background = '#475569'; 
        SELECTEDROWELEMENT_ESC = in_clickedRow;
    }

    try {
        const traces = [];
        for (const ticker of in_tickers) {
            const res = await fetch(`/apiEsc/stock-chart-data?in_code=${ticker}`);
            const json = await res.json();
            const info = in_allData.find(d => d.code === ticker);

            if (!json.error && info && json.dates && json.dates.length > 0) {
                const combined = json.dates
                    .map((d, i) => ({ x: d, y: json.closes[i] }))
                    .filter(v => v.y !== null); // 값이 없는 날짜는 차트 데이터에서 제외
                combined.sort((a, b) => new Date(a.x) - new Date(b.x));

                traces.push({
                    x: combined.map(v => v.x),
                    y: combined.map(v => v.y),
                    name: info.name,
                    mode: 'lines',
                    line: { width: 2.5, color: getStockColor(info.code) },
                    connectgaps: false,
                    hovertemplate: '<b>%{x}</b><br>가격: %{y:,.0f}원<extra></extra>'
                });
            }
        }

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8', size: 10 },
            margin: { t: 20, b: 60, l: 40, r: 50 },
            xaxis: { 
                type: 'category', 
                // categoryorder: 'array',
                categoryorder: 'category ascending', // 날짜 문자열 순서대로 강제 정렬
                gridcolor: '#1e293b',
                tickangle: -45,
                automargin: true,
                nticks: 8,
                fixedrange: true 
            }, 
            yaxis: { gridcolor: '#1e293b', side: 'right', zeroline: false, tickformat: ',d' },
            showlegend: true,
            legend: { orientation: 'h', y: -0.3, x: 0.5, xanchor: 'center' },
            hovermode: 'x unified'
        };

        Plotly.newPlot('mainDynamicChart', traces, layout, {responsive: true, displayModeBar: false});
    } finally {
        if(loading) loading.style.display = 'none';
    }
}

/**
 * @description 수익 및 손실 기여도가 높은 상위 3개 종목 요약 카드 렌더링
 * @param {Array} in_data - 종목 데이터 배열
 * @returns {void}
 */
function renderTop3Report(in_data) {
    const container = document.getElementById('top3ReportContainer');
    const winners = [...in_data].filter(s => s.profit > 0).sort((a,b) => b.profit - a.profit).slice(0,3);
    const losers = [...in_data].filter(s => s.profit < 0).sort((a,b) => a.profit - b.profit).slice(0,3);
    let html = `<div style="display:flex; gap:10px;">`;
    if(winners.length) html += `<div style="flex:1; padding:8px; background:rgba(239,68,68,0.08); border-left:4px solid #ef4444; border-radius:4px;"><div style="color:#f87171; font-weight:bold; margin-bottom:4px; font-size:11px;">🚀 수익 기여도 Top 3</div>${winners.map(s=>`<div style="display:flex; justify-content:space-between; font-size:10px;"><span>${s.name}</span><b style="color:#ff4d4d;">+${Math.floor(s.profit).toLocaleString()}원</b></div>`).join('')}</div>`;
    if(losers.length) html += `<div style="flex:1; padding:8px; background:rgba(59,130,246,0.08); border-left:4px solid #3b82f6; border-radius:4px;"><div style="color:#60a5fa; font-weight:bold; margin-bottom:4px; font-size:11px;">💧 손실 기여도 Top 3</div>${losers.map(s=>`<div style="display:flex; justify-content:space-between; font-size:10px;"><span>${s.name}</span><b style="color:#3b82f6;">${Math.floor(s.profit).toLocaleString()}원</b></div>`).join('')}</div>`;
    container.innerHTML = html + `</div>`;
}
/**
 * @description 전체 투자금액, 평가금액, 누적 수익률 등 종합 지표 계산 및 표시
 * @param {Array} in_data - 종목 데이터 배열
 * @returns {void}
 */
function renderTotalSummary(in_data) {
    const totalInvest = in_data.reduce((sum, s) => sum + (s.buyPrice * s.quantity), 0);
    const totalEval = in_data.reduce((sum, s) => sum + (s.currentPrice * s.quantity), 0);
    const totalProfit = totalEval - totalInvest;
    const totalRate = totalInvest > 0 ? (totalProfit / totalInvest) * 100 : 0;

    // 지표 데이터 생성
    const metrics = [
        { l: '총 투자금액', v: totalInvest }, 
        { l: '총 평가금액', v: totalEval }, 
        { l: '총 평가손익', v: totalProfit, c: true }, 
        { l: '누적 수익률', v: totalRate.toFixed(2)+'%', r: true }
    ];

    const metricsHtml = metrics.map(i => `
        <div style="flex: 1; min-width: 100px; text-align:center;">
            <div style="font-size:10px; color:#94a3b8; margin-bottom: 2px;">${i.l}</div>
            <div style="font-size:13px; font-weight:bold; color:${i.c ? (totalProfit>=0?'#ff4d4d':'#3b82f6') : '#f8fafc'}">
                ${i.r ? i.v : Math.floor(i.v).toLocaleString()+'원'}
            </div>
        </div>
    `).join('');

    // 컨테이너 HTML 교체
    const container = document.getElementById('totalSummaryContainer');
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.padding = '0 15px';

    container.innerHTML = `
        <div style="display: flex; flex: 1; justify-content: flex-start; gap: 20px;">
            ${metricsHtml}
        </div>
        
        <div style="margin-left: 20px;">
            <button onclick="window.close()" style="
                background: #334155; 
                color: #f8fafc; 
                border: 1px solid #475569; 
                padding: 7px 20px; 
                border-radius: 6px; 
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                white-space: nowrap;
                transition: all 0.2s;
            " onmouseover="this.style.background='#475569'; this.style.borderColor='#64748b'" 
               onmouseout="this.style.background='#334155'; this.style.borderColor='#475569'">
                닫기
            </button>
        </div>
    `;
}
/**
 * @description 필터(수익/손실) 변경 시 차트, 리스트, 요약을 일괄 업데이트
 * @param {Array} in_data - 백엔드에서 받은 원본 데이터
 * @returns {void}
 */
function updateStockDisplay(in_data) {
    if(!in_data || in_data.length === 0) return;
    cachedAllData = in_data;
    
    const processedData = in_data.map(s => ({
        ...s,
        profit: (s.currentPrice - s.buyPrice) * s.quantity,
        invest: s.buyPrice * s.quantity,
        rate: ((s.currentPrice - s.buyPrice) / s.buyPrice) * 100
    }));

    // [중요] 필터 변경 시 초기 정렬 상태 강제 설정
    window.currentSortCol = 'profit';
    window.isAsc = false; 

    let filtered = (window.currentFilter === 'winners') 
        ? processedData.filter(s => s.profit >= 0) 
        : processedData.filter(s => s.profit < 0);

    // [중요] 손실일 때는 절대값이 큰 순(손실액이 가장 큰 순)으로 정렬
    filtered.sort((a, b) => {
        if (window.currentFilter === 'losers') {
            return a.profit - b.profit; // 손실액이 클수록(더 작은 음수) 위로
        }
        return b.profit - a.profit; // 수익액이 클수록 위로
    });

    renderTop3Report(processedData); 
    renderStockList(filtered); // 헤더 화살표 위치가 '손익금액'으로 갱신됨
    renderTotalSummary(processedData);
    
    const chartTickers = filtered.slice(0, 5).map(s => s.code);
    if(chartTickers.length > 0) {
        renderCombinedChartWithProgress(chartTickers, processedData, null);
    }
}
/**
 * @description [엔트리 포인트] 서버에서 유저 데이터를 가져와 모달 초기화 및 실행
 * @param {string} in_userId - 사용자 식별 ID
 * @returns {Promise<void>}
 */
async function getStockModalDOM(in_userId) {
    injectModalHTML();
    try {
        const res = await fetch(`/apiEsc/popup-status?in_userId=${in_userId}`);
        const data = await res.json();
        updateStockDisplay(data);
    } catch (e) { document.getElementById('chartLoading').innerHTML = '데이터 수신 실패'; }
}