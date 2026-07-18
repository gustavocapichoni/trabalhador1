// Inicializa o Firebase usando a configuração global importada
if (typeof firebaseConfig !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
} else {
    console.error("Configuração 'firebaseConfig' não encontrada. Verifique se o arquivo firebase-config.js foi importado antes do app.js.");
}
const db = firebase.firestore();

// ── ESTADO GLOBAL ────────────────────────────────────────
let postsData      = [];
let metricasIG     = {};
let metricasYT     = {};
let leadsData      = [];
let leadsCount     = 0;
let filtroAtivo    = 'todos';
let leadsBuscaAtiva = '';

let chartIGLine     = null;
let chartYTLine     = null;
let chartFormatos   = null;
let chartEstrategia = null;
let chartLeadsDia   = null;
let chartLeadsOrigem= null;

// Configurações de exibição dos gráficos
let igMetricaAtiva = 'reach';
let ytMetricaAtiva = 'views';
let igZoomCount    = 15;
let ytZoomCount    = 15;

const NOMES_METRICAS = {
    reach:                    'Alcance',
    likes:                    'Curtidas',
    comments:                 'Comentários',
    saved:                    'Salvamentos',
    shares:                   'Compartilhamentos',
    profile_visits:           'Visitas ao Perfil',
    follows:                  'Novos Seguidores',
    ig_reels_avg_watch_time:  'Retenção Reels (ms)',
    views:                    'Visualizações',
    minutes:                  'Minutos Assistidos'
};

// ── NAVEGAÇÃO ────────────────────────────────────────────
const TABS = {
    overview:  ['Visão Geral',           'Performance do robô separada por plataforma'],
    cientista: ['Cientista de Dados',    'Recomendações e hipóteses do motor de análise'],
    leads:     ['Leads Capturados',      'Histórico e análise dos leads captados pela landing page'],
    posts:     ['Histórico de Postagens','Todos os conteúdos gerados e publicados recentemente']
};

function goTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    document.getElementById('nav-' + name).classList.add('active');
    document.getElementById('page-title').innerText = TABS[name][0];
    document.getElementById('page-sub').innerText   = TABS[name][1];
}

// ── MUDANÇA DE MÉTRICA NOS CARDS IG ─────────────────────
function mudarMétricaIG(metrica, element) {
    igMetricaAtiva = metrica;
    document.querySelectorAll('#ig-metrics .mcard').forEach(c => c.classList.remove('active-ig'));
    element.classList.add('active-ig');
    const nome = NOMES_METRICAS[metrica] || metrica;
    document.getElementById('ig-chart-title').innerText = `📈 ${nome} por postagem (Instagram)`;
    renderGraficos();
}

function mudarMétricaYT(metrica, element) {
    ytMetricaAtiva = metrica;
    document.querySelectorAll('#yt-metrics .mcard').forEach(c => c.classList.remove('active-yt'));
    element.classList.add('active-yt');
    const nome = NOMES_METRICAS[metrica] || metrica;
    document.getElementById('yt-chart-title').innerText = `📈 ${nome} por vídeo (YouTube)`;
    renderGraficos();
}

// ── ZOOM GRADUAL ─────────────────────────────────────────
function alterarZoomIG(delta) {
    const total = postsData.length || 15;
    igZoomCount = Math.max(5, Math.min(igZoomCount + delta, total));
    renderGraficos();
}

function alterarZoomYT(delta) {
    const total = postsData.filter(p => p.video_id_yt).length || 15;
    ytZoomCount = Math.max(5, Math.min(ytZoomCount + delta, total));
    renderGraficos();
}

// ── BOTÃO ATUALIZAR ──────────────────────────────────────
async function acaoAtualizarBotao() {
    goTab('overview');
    igMetricaAtiva = 'reach';
    ytMetricaAtiva = 'views';
    igZoomCount    = 15;
    ytZoomCount    = 15;

    document.querySelectorAll('#ig-metrics .mcard').forEach(c => c.classList.remove('active-ig'));
    const r = document.getElementById('card-ig-reach');
    if (r) r.classList.add('active-ig');
    document.getElementById('ig-chart-title').innerText = '📈 Alcance por postagem (Instagram)';

    document.querySelectorAll('#yt-metrics .mcard').forEach(c => c.classList.remove('active-yt'));
    const v = document.getElementById('card-yt-views');
    if (v) v.classList.add('active-yt');
    document.getElementById('yt-chart-title').innerText = '📈 Views por vídeo (YouTube)';

    const lblIg = document.getElementById('lbl-zoom-ig');
    if (lblIg) lblIg.innerText = 'Exibindo 15 posts';
    const lblYt = document.getElementById('lbl-zoom-yt');
    if (lblYt) lblYt.innerText = 'Exibindo 15 vídeos';

    filtroAtivo = 'todos';
    document.querySelectorAll('.filter-bar .fbtn').forEach(b => b.classList.remove('active'));
    const first = document.querySelector('.filter-bar .fbtn:first-child');
    if (first) first.classList.add('active');

    await carregarTudo();
}

// ── CARREGAMENTO PRINCIPAL ───────────────────────────────
async function carregarTudo() {
    document.getElementById('posts-grid').innerHTML =
        '<div class="empty-state"><i data-lucide="loader" class="spinner"></i><span>Conectando ao Firebase...</span></div>';
    lucide.createIcons();

    try {
        // 1. Leads
        try {
            const leadsSnap = await db.collection('leads').get();
            leadsData  = [];
            leadsSnap.forEach(doc => leadsData.push({ id: doc.id, ...doc.data() }));
            leadsCount = leadsData.length;
            document.getElementById('funnel-leads').innerText = fmt(leadsCount);
        } catch (e) {
            console.warn('Erro ao ler leads:', e);
            document.getElementById('funnel-leads').innerText = '0';
        }

        // 2. Estado do bot
        try {
            const cfg = await db.collection('bot_config').doc('app_state').get();
            if (cfg.exists) {
                const d = cfg.data();
                document.getElementById('val-tema').innerText   = d.tema_do_dia  || '--';
                document.getElementById('val-gancho').innerText = d.indice_gancho ?? '--';
                document.getElementById('val-cta').innerText    = d.indice_cta    ?? '--';
            }
        } catch(e) { console.warn('Estado bot:', e); }

        // 3. Histórico de posts (fonte principal: legenda, frase_visual, etc.)
        const postSnap = await db.collection('historico_posts').get();
        const historicoMap = {}; // chave: post_id
        postSnap.forEach(doc => {
            const d = { id: doc.id, ...doc.data() };
            if (d.post_id) historicoMap[d.post_id] = d;
        });

        // 4. Métricas Instagram (também contém info_post dos posts descobertos via API)
        const igSnap = await db.collection('metricas_posts').get();
        metricasIG = {};
        const metricasPostsMap = {}; // info_post de cada post com métrica
        igSnap.forEach(doc => {
            const d = doc.data();
            metricasIG[doc.id] = d.metricas || {};
            if (d.info_post) metricasPostsMap[doc.id] = d.info_post;
        });

        // Merge: todos os posts que têm métrica OU estão no histórico do bot
        const todosPostsMap = {};
        // 1º adiciona descobertos pela API (via metricas_posts)
        Object.entries(metricasPostsMap).forEach(([pid, info]) => {
            todosPostsMap[pid] = {
                post_id: pid,
                data:    info.data    || '',
                tipo:    info.tipo    || 'feed',
                tema:    info.tema    || 'Descoberto',
                legenda: info.caption || info.legenda || '',
                frase_visual: info.frase_visual || ''
            };
        });
        // 2º sobrescreve/enriquece com dados do histórico do bot (mais completo)
        Object.entries(historicoMap).forEach(([pid, h]) => {
            todosPostsMap[pid] = { ...todosPostsMap[pid], ...h };
        });
        postsData = Object.values(todosPostsMap)
            .filter(p => p.post_id)
            .sort((a, b) => new Date(b.data) - new Date(a.data));

        // 5. Métricas YouTube
        const ytSnap = await db.collection('metricas_posts_youtube').get();
        metricasYT = {};
        ytSnap.forEach(doc => { metricasYT[doc.id] = doc.data().metricas || {}; });

        // 6. Renders
        renderMetricasIG();
        renderMetricasYT();
        renderFunilEstrategico();
        renderGraficos();
        renderPosts(filtroAtivo);
        renderLeads();

        // 7. Cientista (async isolado)
        await carregarCientista();

    } catch (err) {
        console.error('[Dashboard] Erro:', err);
        document.getElementById('posts-grid').innerHTML =
            `<div class="err-box">⚠️ ${err.message}<br><small>Verifique as Regras do Firestore.</small></div>`;
        lucide.createIcons();
    }
}

// ── FUNIL ESTRATÉGICO ────────────────────────────────────
function renderFunilEstrategico() {
    // Alcance total IG
    let alcanceIG = 0, profileVisitsTotal = 0, followsTotal = 0;
    Object.values(metricasIG).forEach(m => {
        alcanceIG          += m.reach || 0;
        profileVisitsTotal += m.profile_visits || 0;
        followsTotal       += m.follows || 0;
    });

    // Taxa de Conversão (Leads / Alcance IG)
    if (alcanceIG > 0 && leadsCount > 0) {
        const rate = (leadsCount / alcanceIG) * 100;
        document.getElementById('funnel-rate').innerText = rate.toFixed(2) + '%';
    } else {
        document.getElementById('funnel-rate').innerText = '0,00%';
    }

    document.getElementById('funnel-followers').innerText     = followsTotal > 0 ? fmt(followsTotal) : '--';
    document.getElementById('funnel-profile-visits').innerText = profileVisitsTotal > 0 ? fmt(profileVisitsTotal) : '--';
}

// ── TENDÊNCIA (compara última semana vs semana anterior) ─
function calcularTendencia(posts7, posts14) {
    // Divide posts em dois grupos: 0-7 dias e 7-14 dias
    const agora = Date.now();
    const limiar7  = agora - 7  * 86400000;
    const limiar14 = agora - 14 * 86400000;

    function somaMetrica(lista, metrica) {
        return lista.reduce((acc, p) => {
            const m = metricasIG[p.post_id] || {};
            if (metrica === 'likes')     return acc + (m.likes || m.like_count || 0);
            if (metrica === 'comments')  return acc + (m.comments || m.comments_count || 0);
            if (metrica === 'saved')     return acc + (m.saved || 0);
            if (metrica === 'shares')    return acc + (m.shares || 0);
            if (metrica === 'profile_visits') return acc + (m.profile_visits || 0);
            if (metrica === 'follows')   return acc + (m.follows || 0);
            if (metrica === 'ig_reels_avg_watch_time') return acc + (m.ig_reels_avg_watch_time || 0);
            return acc + (m.reach || 0);
        }, 0);
    }

    const recentes  = postsData.filter(p => new Date(p.data).getTime() >= limiar7);
    const anteriores= postsData.filter(p => {
        const t = new Date(p.data).getTime();
        return t >= limiar14 && t < limiar7;
    });

    const metricas = ['reach','likes','comments','saved','shares','profile_visits','follows','ig_reels_avg_watch_time'];
    const res = {};
    metricas.forEach(m => {
        const atual  = somaMetrica(recentes, m);
        const ant    = somaMetrica(anteriores, m);
        if (ant === 0) { res[m] = 'flat'; return; }
        const delta = ((atual - ant) / ant) * 100;
        res[m] = delta > 3 ? `up|+${delta.toFixed(0)}%` : delta < -3 ? `down|${delta.toFixed(0)}%` : 'flat';
    });
    return res;
}

function renderTrend(id, valor) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!valor || valor === 'flat') {
        el.className = 'trend flat'; el.innerHTML = '─ estável'; return;
    }
    const [dir, pct] = valor.split('|');
    if (dir === 'up') {
        el.className = 'trend up';
        el.innerHTML = `▲ ${pct} vs sem. ant.`;
    } else {
        el.className = 'trend down';
        el.innerHTML = `▼ ${pct} vs sem. ant.`;
    }
}

// ── MÉTRICAS INSTAGRAM ───────────────────────────────────
function renderMetricasIG() {
    let reach=0, likes=0, comments=0, saves=0, shares=0, profVisits=0, follows=0, avgWatch=0, watchCount=0;
    Object.values(metricasIG).forEach(m => {
        reach      += m.reach      || 0;
        likes      += m.likes      || m.like_count     || 0;
        comments   += m.comments   || m.comments_count || 0;
        saves      += m.saved      || 0;
        shares     += m.shares     || 0;
        profVisits += m.profile_visits || 0;
        follows    += m.follows    || 0;
        if (m.ig_reels_avg_watch_time) { avgWatch += m.ig_reels_avg_watch_time; watchCount++; }
    });

    document.getElementById('ig-reach').innerText         = fmt(reach);
    document.getElementById('ig-likes').innerText         = fmt(likes);
    document.getElementById('ig-comments').innerText      = fmt(comments);
    document.getElementById('ig-saves').innerText         = fmt(saves);
    document.getElementById('ig-shares').innerText        = fmt(shares);
    document.getElementById('ig-profile-visits').innerText= profVisits > 0 ? fmt(profVisits) : '--';
    document.getElementById('ig-follows').innerText       = follows > 0 ? fmt(follows) : '--';
    document.getElementById('ig-avg-watch').innerText     = watchCount > 0 ? (avgWatch / watchCount / 1000).toFixed(1) + 's' : '--';

    // Indicadores de tendência
    const trends = calcularTendencia();
    renderTrend('trend-ig-reach',          trends['reach']);
    renderTrend('trend-ig-likes',          trends['likes']);
    renderTrend('trend-ig-comments',       trends['comments']);
    renderTrend('trend-ig-saves',          trends['saved']);
    renderTrend('trend-ig-shares',         trends['shares']);
    renderTrend('trend-ig-profile_visits', trends['profile_visits']);
    renderTrend('trend-ig-follows',        trends['follows']);
    renderTrend('trend-ig-avg_watch',      trends['ig_reels_avg_watch_time']);
}

// ── MÉTRICAS YOUTUBE ─────────────────────────────────────
function renderMetricasYT() {
    let views=0, likes=0, comments=0, shares=0, minutes=0;
    Object.values(metricasYT).forEach(m => {
        views    += m.views    || 0;
        likes    += m.likes    || 0;
        comments += m.comments || 0;
        shares   += m.shares   || 0;
        minutes  += m.watch_time_minutes || m.estimated_minutes_watched || 0;
    });
    document.getElementById('yt-views').innerText    = fmt(views);
    document.getElementById('yt-likes').innerText    = fmt(likes);
    document.getElementById('yt-comments').innerText = fmt(comments);
    document.getElementById('yt-shares').innerText   = fmt(shares);
    document.getElementById('yt-minutes').innerText  = minutes > 0 ? fmt(Math.round(minutes)) + ' min' : '--';
}

// ── GRÁFICOS ─────────────────────────────────────────────
function renderGraficos() {
    if (chartIGLine)   chartIGLine.destroy();
    if (chartYTLine)   chartYTLine.destroy();
    if (chartFormatos) chartFormatos.destroy();

    // IG Line
    let postsIG = [...postsData].reverse();
    const totalPosts = postsData.length || 15;
    igZoomCount = Math.min(igZoomCount, totalPosts);
    postsIG = postsIG.slice(-igZoomCount);

    const lblIg = document.getElementById('lbl-zoom-ig');
    if (lblIg) lblIg.innerText = igZoomCount >= totalPosts ? 'Exibindo tudo' : `Exibindo ${igZoomCount} posts`;

    const igDataMapeada = postsIG.map(p => {
        const m = metricasIG[p.post_id] || {};
        if (igMetricaAtiva === 'likes')     return m.likes || m.like_count || 0;
        if (igMetricaAtiva === 'comments')  return m.comments || m.comments_count || 0;
        if (igMetricaAtiva === 'saved')     return m.saved || 0;
        if (igMetricaAtiva === 'shares')    return m.shares || 0;
        if (igMetricaAtiva === 'profile_visits') return m.profile_visits || 0;
        if (igMetricaAtiva === 'follows')   return m.follows || 0;
        if (igMetricaAtiva === 'ig_reels_avg_watch_time') return Math.round((m.ig_reels_avg_watch_time || 0) / 1000);
        return m.reach || 0;
    });

    chartIGLine = new Chart(document.getElementById('chart-ig-line'), {
        type: 'line',
        data: {
            labels: postsIG.map(p => fmtData(p.data)),
            datasets: [{
                label: NOMES_METRICAS[igMetricaAtiva] || igMetricaAtiva,
                data: igDataMapeada,
                borderColor: '#e1306c',
                backgroundColor: 'rgba(225,48,108,.08)',
                borderWidth: 2.5, fill: true, tension: .4,
                pointRadius: 4, pointHoverRadius: 7
            }]
        },
        options: chartOpts('#e1306c')
    });

    // YT Line
    let postsYT = [...postsData].filter(p => p.video_id_yt).reverse();
    const totalVideos = postsYT.length || 15;
    ytZoomCount = Math.min(ytZoomCount, totalVideos);
    postsYT = postsYT.slice(-ytZoomCount);

    const lblYt = document.getElementById('lbl-zoom-yt');
    if (lblYt) lblYt.innerText = ytZoomCount >= totalVideos ? 'Exibindo tudo' : `Exibindo ${ytZoomCount} vídeos`;

    const ytDataMapeada = postsYT.map(p => {
        const m = metricasYT[p.video_id_yt] || {};
        if (ytMetricaAtiva === 'likes')    return m.likes || 0;
        if (ytMetricaAtiva === 'comments') return m.comments || 0;
        if (ytMetricaAtiva === 'shares')   return m.shares || 0;
        if (ytMetricaAtiva === 'minutes')  return Math.round(m.watch_time_minutes || m.estimated_minutes_watched || 0);
        return m.views || 0;
    });

    chartYTLine = new Chart(document.getElementById('chart-yt-line'), {
        type: 'line',
        data: {
            labels: postsYT.length ? postsYT.map(p => fmtData(p.data)) : ['Sem dados'],
            datasets: [{
                label: NOMES_METRICAS[ytMetricaAtiva] || ytMetricaAtiva,
                data: ytDataMapeada.length ? ytDataMapeada : [0],
                borderColor: '#ff1e1e',
                backgroundColor: 'rgba(255,30,30,.08)',
                borderWidth: 2.5, fill: true, tension: .4,
                pointRadius: 4, pointHoverRadius: 7
            }]
        },
        options: chartOpts('#ff1e1e')
    });

    // Donut Formatos
    let reels=0, carousel=0, stories=0, outros=0;
    postsData.forEach(p => {
        const t = (p.tipo||'').toLowerCase();
        if (t.includes('reel')||t.includes('pexels')) reels++;
        else if (t.includes('carousel')) carousel++;
        else if (t.includes('story'))    stories++;
        else outros++;
    });
    chartFormatos = new Chart(document.getElementById('chart-formatos'), {
        type: 'doughnut',
        data: {
            labels: ['Reels/Vídeos','Carrossel','Stories','Outros'],
            datasets: [{ data: [reels,carousel,stories,outros], backgroundColor: ['#e1306c','#7c4dff','#ff9100','#6b7280'], borderWidth: 0 }]
        },
        options: {
            responsive:true, maintainAspectRatio:false,
            plugins:{ legend:{ position:'bottom', labels:{ color:'#9ca3af', font:{family:'Outfit'}, padding:10, boxWidth:12 } } }
        }
    });
}

function chartOpts(color) {
    return {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode:'index', intersect:false },
        plugins: {
            legend: { labels: { color:'#9ca3af', font:{family:'Outfit',size:11} } },
            tooltip: {
                backgroundColor:'rgba(13,17,26,0.95)', titleColor:'#fff', bodyColor:'#e5e7eb',
                borderColor:'rgba(255,255,255,0.1)', borderWidth:1, padding:10,
                titleFont:{family:'Outfit',weight:'bold'}, bodyFont:{family:'Outfit'}
            }
        },
        scales: {
            x: { grid:{color:'rgba(255,255,255,.03)'}, ticks:{color:'#9ca3af',font:{family:'Outfit',size:10}} },
            y: { grid:{color:'rgba(255,255,255,.03)'}, ticks:{color:'#9ca3af',font:{family:'Outfit',size:10}}, beginAtZero:true }
        }
    };
}

// ── CIENTISTA DE DADOS ───────────────────────────────────
async function carregarCientista() {
    try {
        const snap = await db.collection('memoria_estrategica').doc('recomendacoes').get();

        if (!snap.exists) {
            // Sem dados ainda — mostra placeholders
            renderGrowthScore(null);
            renderICCRanking({});
            renderEstrategiaDonut({});
            renderCopyRankings({}, {});
            renderRecomendacoes(null);
        } else {
            const d = snap.data();
            renderGrowthScore(d);
            renderICCRanking(d.icc_por_tema || {});
            renderEstrategiaDonut(d.peso_final_temas || {});
            renderCopyRankings(d.ganchos_growth_score || {}, d.ctas_growth_score || {});
            renderRecomendacoes(d);
        }
    } catch(e) {
        console.warn('Cientista de Dados erro:', e);
        renderGrowthScore(null);
    }

    // Hipóteses
    try {
        const snap  = await db.collection('memoria_estrategica').doc('hipoteses').get();
        const tbody = document.getElementById('hipo-body');
        if (snap.exists) {
            const data  = snap.data();
            const lista = data.hipoteses || data.historico_hipoteses || Object.values(data);
            const arr   = Array.isArray(lista) ? lista : [];
            if (arr.length) {
                tbody.innerHTML = arr.map(h => {
                    const desc = h.descricao || h.texto || h.hipotese || JSON.stringify(h);
                    const st   = (h.status||'pendente').toLowerCase().replace(/\s+/g,'');
                    return `<tr><td>${desc}</td><td><span class="badge ${st}">${st.toUpperCase()}</span></td><td>${h.confianca||'--'}</td></tr>`;
                }).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="3">Nenhuma hipótese cadastrada.</td></tr>';
            }
        } else {
            tbody.innerHTML = `
                <tr><td>Reels publicados à noite têm maior retenção</td><td><span class="badge validando">VALIDANDO</span></td><td>Média</td></tr>
                <tr><td>Trilha misteriosa aumenta o tempo assistido</td><td><span class="badge validando">VALIDANDO</span></td><td>Alta</td></tr>
                <tr><td>CTA de salvamento converte melhor em Carrosséis</td><td><span class="badge validando">VALIDANDO</span></td><td>Alta</td></tr>`;
        }
    } catch(e) { console.warn('Hipóteses:', e); }
}

// Growth Score — gauge visual
function renderGrowthScore(d) {
    const numEl = document.getElementById('gs-numero');
    const barEl = document.getElementById('gs-bar');
    const cicEl = document.getElementById('gs-ciclos');
    const tmaEl = document.getElementById('gs-tema-icc');
    const atuEl = document.getElementById('gs-atualizado');

    if (!d || d.growth_score_referencia === undefined) {
        numEl.innerText = '--';
        if (barEl) barEl.style.width = '0%';
        if (cicEl) cicEl.innerText = '--';
        if (tmaEl) tmaEl.innerText = '--';
        if (atuEl) atuEl.innerText = '--';
        return;
    }

    const gs  = d.growth_score_referencia;
    // GS é uma fração pequena (ex: 0.012). Escala para 0-100 assumindo que 0.1 = 100% de excelência
    const pct = Math.min(gs / 0.1 * 100, 100);
    const cor = gs > 0.05 ? 'var(--neon-green)' : gs > 0.02 ? 'var(--neon-gold)' : 'var(--neon-purple)';

    numEl.innerText        = (gs * 100).toFixed(3) + '%';
    numEl.style.color      = cor;
    if (barEl) {
        barEl.style.width      = pct.toFixed(1) + '%';
        barEl.style.background = `linear-gradient(90deg,${cor},rgba(0,229,255,.7))`;
        barEl.style.boxShadow  = `0 0 10px ${cor}`;
    }
    if (cicEl) cicEl.innerText = d.ciclos_utilizados ? d.ciclos_utilizados.map(c => c.toUpperCase()).join(', ') : '--';
    if (tmaEl) tmaEl.innerText = d.tema_maior_icc ? d.tema_maior_icc.toUpperCase() : '--';
    if (atuEl) atuEl.innerText = d.atualizado_em ? d.atualizado_em.split(' ')[0] : '--';
}

// Ranking ICC
function renderICCRanking(icc) {
    const el = document.getElementById('icc-list');
    if (!el) return;
    const entries = Object.entries(icc).sort((a,b) => b[1]-a[1]);
    if (!entries.length) {
        el.innerHTML = '<div class="rec-item empty">Nenhum dado de ICC disponível. Execute um ciclo de analytics.</div>';
        return;
    }
    const max = entries[0][1] || 1;
    el.innerHTML = entries.map(([tema,val], i) => {
        const pct = ((val / max) * 100).toFixed(1);
        const isBest = i === 0;
        return `
        <div class="icc-item">
            <div class="icc-row">
                <span class="icc-tema">${isBest ? '🥇 ' : ''}${tema}</span>
                <span class="icc-valor">${(val*100).toFixed(2)}%</span>
            </div>
            <div class="icc-track">
                <div class="icc-fill ${isBest ? 'best' : ''}" style="width:${pct}%"></div>
            </div>
        </div>`;
    }).join('');
}

// Donut de Estratégia do Bot
function renderEstrategiaDonut(pesos) {
    if (chartEstrategia) { chartEstrategia.destroy(); chartEstrategia = null; }
    const canvas = document.getElementById('chart-estrategia');
    const legEl  = document.getElementById('estrategia-legend');
    if (!canvas || !legEl) return;

    const entries = Object.entries(pesos).sort((a,b) => b[1]-a[1]);
    if (!entries.length) {
        legEl.innerHTML = '<div style="color:var(--text-sec);font-size:.82rem;">Sem dados ainda.</div>';
        return;
    }

    const cores = [
        '#7c4dff','#00e5ff','#e1306c','#00e676','#ffd600',
        '#ff9100','#ff1744','#64ffda','#ea80fc','#82b1ff'
    ];
    const labels = entries.map(([t]) => t);
    const data   = entries.map(([,v]) => +(v*100).toFixed(1));

    chartEstrategia = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{ data, backgroundColor: cores.slice(0,labels.length), borderWidth: 0 }]
        },
        options: {
            responsive:true, maintainAspectRatio:false,
            plugins:{ legend:{display:false}, tooltip:{
                backgroundColor:'rgba(13,17,26,.95)', titleColor:'#fff', bodyColor:'#e5e7eb',
                bodyFont:{family:'Outfit'}, titleFont:{family:'Outfit',weight:'bold'}
            }}
        }
    });

    legEl.innerHTML = entries.map(([tema,val], i) => `
        <div class="estrat-leg-item">
            <span class="estrat-dot" style="background:${cores[i] || '#666'}"></span>
            <span class="estrat-nome">${tema}</span>
            <span class="estrat-pct">${(val*100).toFixed(0)}%</span>
        </div>`).join('');
}

// Rankings de Copy
function renderCopyRankings(ganchos, ctas) {
    const posEmoji = ['rank-1','rank-2','rank-3'];

    function renderLista(containerId, dados) {
        const el = document.getElementById(containerId);
        if (!el) return;
        const entries = Object.entries(dados).sort((a,b) => b[1]-a[1]).slice(0,5);
        if (!entries.length) {
            el.innerHTML = '<div class="rec-item empty">Execute um ciclo de analytics para ver este ranking.</div>';
            return;
        }
        el.innerHTML = entries.map(([nome, gs], i) => `
        <div class="copy-rank-item">
            <div class="copy-rank-pos ${posEmoji[i] || ''}">${i+1}</div>
            <div class="copy-rank-nome">${nome}</div>
            <div class="copy-rank-gs">GS: ${(gs*10000).toFixed(2)}</div>
        </div>`).join('');
    }

    renderLista('ganchos-ranking', ganchos);
    renderLista('ctas-ranking', ctas);
}

// Recomendações
function renderRecomendacoes(d) {
    const box = document.getElementById('rec-list');
    if (!box) return;
    if (!d) {
        box.innerHTML = '<div class="rec-item empty">Nenhuma recomendação ainda. Elas aparecem após o próximo ciclo de analytics.</div>';
        return;
    }
    let html = '';
    if (d.growth_score_referencia !== undefined)
        html += rec(`📊 <strong>Growth Score de Referência:</strong> ${(d.growth_score_referencia*100).toFixed(3)}%`);
    if (d.tema_maior_icc && d.icc_por_tema)
        html += rec(`🎯 <strong>Tema que mais converte seguidores (ICC):</strong> ${d.tema_maior_icc.toUpperCase()} — ${(d.icc_por_tema[d.tema_maior_icc]*100).toFixed(1)}%`);
    if (d.peso_final_temas) {
        Object.entries(d.peso_final_temas).sort((a,b) => b[1]-a[1]).slice(0,4).forEach(([t,p]) =>
            html += rec(`🏆 <strong>${t}:</strong> ${(p*100).toFixed(1)}% do mix de conteúdo`)
        );
    }
    if (d.ciclos_utilizados?.length)
        html += rec(`🔄 <strong>Ciclos analisados:</strong> ${d.ciclos_utilizados.map(c => c.toUpperCase()).join(', ')}`);
    if (d.atualizado_em)
        html += `<div class="rec-item" style="font-size:.78rem;color:var(--text-muted)">Atualizado: ${d.atualizado_em}</div>`;
    box.innerHTML = html || '<div class="rec-item empty">Dados incompletos. Aguarde o próximo ciclo.</div>';
}

// ── LEADS ────────────────────────────────────────────────
function renderLeads() {
    if (!leadsData) return;
    const agora     = Date.now();
    const limiarSem = agora - 7 * 86400000;
    const limiarHoj = agora - 86400000;

    let semana = 0, hoje = 0;
    leadsData.forEach(l => {
        const ts = extrairTimestampLead(l);
        if (ts >= limiarSem) semana++;
        if (ts >= limiarHoj) hoje++;
    });

    const el = (id, v) => { const e = document.getElementById(id); if(e) e.innerText = v; };
    el('leads-total',  fmt(leadsCount));
    el('leads-semana', fmt(semana));
    el('leads-hoje',   fmt(hoje));

    // Taxa de Conversão
    let alcanceIG = 0;
    Object.values(metricasIG).forEach(m => { alcanceIG += m.reach || 0; });
    if (alcanceIG > 0 && leadsCount > 0) {
        const r = (leadsCount / alcanceIG) * 100;
        el('leads-taxa', r.toFixed(2) + '%');
        el('funnel-rate', r.toFixed(2) + '%');
    } else {
        el('leads-taxa', '0,00%');
    }

    renderLeadsTabela(leadsData);
    renderLeadsGraficos();
}

function extrairTimestampLead(l) {
    // Timestamp nativo do Firestore (objeto com .seconds e .nanoseconds)
    if (l.timestamp && typeof l.timestamp === 'object' && l.timestamp.seconds)
        return l.timestamp.seconds * 1000;
    if (l.created_at && typeof l.created_at === 'object' && l.created_at.seconds)
        return l.created_at.seconds * 1000;
    // String ISO ou formato legível
    if (l.data_captura)  return new Date(l.data_captura).getTime();
    if (l.created_at && typeof l.created_at === 'string') return new Date(l.created_at).getTime();
    if (l.timestamp  && typeof l.timestamp  === 'string') return new Date(l.timestamp).getTime();
    // Firestore Timestamp já convertido pelo SDK compat (toDate)
    if (l.timestamp?.toDate)  return l.timestamp.toDate().getTime();
    if (l.created_at?.toDate) return l.created_at.toDate().getTime();
    return 0;
}

function filtrarLeads(busca) {
    leadsBuscaAtiva = busca.toLowerCase();
    const filtrado = leadsData.filter(l => {
        const nome  = (l.nome  || l.name  || '').toLowerCase();
        const email = (l.email || '').toLowerCase();
        return nome.includes(leadsBuscaAtiva) || email.includes(leadsBuscaAtiva);
    });
    renderLeadsTabela(filtrado);
}

function renderLeadsTabela(lista) {
    const el = document.getElementById('leads-lista');
    if (!el) return;
    if (!lista.length) {
        el.innerHTML = '<div class="leads-empty">Nenhum lead encontrado.</div>';
        return;
    }
    const ordenados = [...lista].sort((a,b) => extrairTimestampLead(b) - extrairTimestampLead(a));
    el.innerHTML = ordenados.map(l => {
        const nome  = l.nome  || l.name  || '(sem nome)';
        const email = l.email || '(sem e-mail)';
        const ts    = extrairTimestampLead(l);
        const data  = ts ? fmtDataCompleta(new Date(ts).toISOString()) : '--';
        return `<div class="lead-row">
            <span>${nome}</span>
            <span class="lead-email">${email}</span>
            <span class="lead-date">${data}</span>
        </div>`;
    }).join('');
}

function renderLeadsGraficos() {
    if (chartLeadsDia)    { chartLeadsDia.destroy();    chartLeadsDia    = null; }
    if (chartLeadsOrigem) { chartLeadsOrigem.destroy(); chartLeadsOrigem = null; }

    const canvasDia    = document.getElementById('chart-leads-dia');
    const canvasOrigem = document.getElementById('chart-leads-origem');
    if (!canvasDia || !canvasOrigem) return;

    // Agrupa leads por dia (últimos 30 dias)
    const dias = {};
    const hoje = new Date(); hoje.setHours(0,0,0,0);
    for (let i = 29; i >= 0; i--) {
        const d = new Date(hoje); d.setDate(d.getDate() - i);
        const key = `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}`;
        dias[key] = 0;
    }
    leadsData.forEach(l => {
        const ts = extrairTimestampLead(l);
        if (!ts) return;
        const d = new Date(ts);
        const key = `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}`;
        if (key in dias) dias[key]++;
    });

    chartLeadsDia = new Chart(canvasDia, {
        type: 'line',
        data: {
            labels: Object.keys(dias),
            datasets: [{
                label: 'Leads por dia',
                data: Object.values(dias),
                borderColor: '#ffd600',
                backgroundColor: 'rgba(255,214,0,.06)',
                borderWidth: 2.5, fill: true, tension: .4,
                pointRadius: 3, pointHoverRadius: 6
            }]
        },
        options: chartOpts('#ffd600')
    });

    // Origem dos leads (campo 'origem' ou 'source')
    const origens = {};
    leadsData.forEach(l => {
        const o = l.origem || l.source || 'Landing Page';
        origens[o] = (origens[o] || 0) + 1;
    });
    const origensEntries = Object.entries(origens);
    chartLeadsOrigem = new Chart(canvasOrigem, {
        type: 'doughnut',
        data: {
            labels: origensEntries.map(([k]) => k),
            datasets: [{ data: origensEntries.map(([,v]) => v), backgroundColor: ['#ffd600','#7c4dff','#00e5ff','#00e676','#ff1744'], borderWidth: 0 }]
        },
        options: {
            responsive:true, maintainAspectRatio:false,
            plugins:{ legend:{ position:'bottom', labels:{ color:'#9ca3af', font:{family:'Outfit'}, padding:10, boxWidth:12 } } }
        }
    });
}

// ── POSTS GRID ───────────────────────────────────────────
function filtrar(tipo, btn) {
    filtroAtivo = tipo;
    document.querySelectorAll('.filter-bar .fbtn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderPosts(tipo);
}

function renderPosts(tipo) {
    const grid  = document.getElementById('posts-grid');
    const lista = postsData.filter(p => {
        if (tipo==='todos') return true;
        const t = (p.tipo||'').toLowerCase();
        if (tipo==='reels')    return t.includes('reel')||t.includes('pexels');
        if (tipo==='carousel') return t.includes('carousel');
        if (tipo==='story')    return t.includes('story');
        return false;
    });
    if (!lista.length) {
        grid.innerHTML = '<div class="empty-state"><i data-lucide="inbox"></i><span>Nenhuma postagem neste filtro.</span></div>';
        lucide.createIcons(); return;
    }
    grid.innerHTML = lista.map(p => {
        const m      = metricasIG[p.post_id] || {};
        const reach  = fmt(m.reach || 0);
        const likes  = fmt(m.likes || m.like_count || 0);
        const saves  = fmt(m.saved || 0);
        const shares = fmt(m.shares || 0);
        const img    = m.media_url || '';
        const tag    = (p.tipo||'post').replace('_',' ');
        const isVid  = tag.includes('reel')||tag.includes('pexels');

        let mediaClass = 'media-default';
        if (tag.includes('reel')||tag.includes('pexels')) mediaClass = 'media-reels';
        else if (tag.includes('story'))    mediaClass = 'media-story';
        else if (tag.includes('carousel')) mediaClass = 'media-carousel';

        const legendaLimpa = (p.legenda||'Sem legenda.').replace(/</g,'&lt;');

        // Elemento de mídia: vídeo para Reels, imagem para os demais
        let mediaEl = '';
        if (img) {
            if (isVid) {
                mediaEl = `<video src="${img}" preload="none" muted playsinline
                    style="width:100%;height:100%;object-fit:cover;border-radius:0;"
                    onmouseover="this.play()" onmouseout="this.pause();this.currentTime=0;"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"></video>
                    <div class="no-img-gradient" style="display:none"><i data-lucide="video"></i><span>Mídia Local</span><small>Vídeo da postagem</small></div>`;
            } else {
                mediaEl = `<img src="${img}" alt="" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
                    <div class="no-img-gradient" style="display:none"><i data-lucide="image"></i><span>Mídia Local</span><small>Imagem da postagem</small></div>`;
            }
        } else {
            mediaEl = `<div class="no-img-gradient"><i data-lucide="${isVid?'video':'image'}"></i><span>Mídia Local</span><small>Vídeo/Imagem da postagem</small></div>`;
        }

        return `
        <article class="post-card" onclick="abrirModalPost('${p.post_id}')">
            <div class="post-media ${mediaClass}">
                <span class="post-tag">${tag}</span>
                ${mediaEl}
            </div>
            <div class="post-body">
                ${p.frase_visual?`<div class="post-title">${p.frase_visual}</div>`:''}
                <div class="post-caption">${legendaLimpa}</div>
                <div class="post-foot">
                    <div class="post-meta"><span>🏷️ ${p.tema||'espiritualidade'}</span><span>${fmtData(p.data)}</span></div>
                    <div class="post-stats">
                        <div class="pstat"><i data-lucide="eye"></i>${reach}</div>
                        <div class="pstat"><i data-lucide="heart"></i>${likes}</div>
                        <div class="pstat"><i data-lucide="bookmark"></i>${saves}</div>
                        <div class="pstat"><i data-lucide="share-2"></i>${shares}</div>
                    </div>
                </div>
            </div>
        </article>`;
    }).join('');
    lucide.createIcons();
}

// ── MODAL DETALHES DO POST ────────────────────────────────
function abrirModalPost(postId) {
    const post = postsData.find(p => p.post_id === postId);
    if (!post) return;

    const m       = metricasIG[postId] || {};
    const tag     = (post.tipo||'post').replace('_',' ');
    const isVid   = tag.includes('reel')||tag.includes('pexels');
    const imgUrl  = m.media_url || '';

    let mediaClass = 'media-default';
    if (tag.includes('reel')||tag.includes('pexels')) mediaClass = 'media-reels';
    else if (tag.includes('story'))    mediaClass = 'media-story';
    else if (tag.includes('carousel')) mediaClass = 'media-carousel';

    // Métricas básicas
    const reach  = fmt(m.reach || 0);
    const likes  = fmt(m.likes || m.like_count || 0);
    const saves  = fmt(m.saved || 0);
    const shares = fmt(m.shares || 0);

    // Métricas avançadas
    const profVisits = m.profile_visits ? fmt(m.profile_visits) : '--';
    const follows    = m.follows ? fmt(m.follows) : '--';
    const ctrFeed    = m.CTR_feed  ? (m.CTR_feed * 100).toFixed(1) + '%' : (m.taxa_salvamento ? '--' : '--');
    const taxaSalv   = m.taxa_salvamento  ? (m.taxa_salvamento * 100).toFixed(1) + '%' : '--';
    const taxaComp   = m.taxa_compartilhamento ? (m.taxa_compartilhamento * 100).toFixed(1) + '%' : '--';
    const retencao   = m.retencao_media_pct ? (m.retencao_media_pct * 100).toFixed(1) + '%' : '--';
    const avgWatch   = m.ig_reels_avg_watch_time ? (m.ig_reels_avg_watch_time / 1000).toFixed(1) + 's' : '--';
    const permalink  = m.permalink || '';

        // Elemento de mídia do modal
        let modalMediaEl = '';
        if (imgUrl) {
            if (isVid) {
                modalMediaEl = `<video src="${imgUrl}" controls preload="metadata"
                    style="width:100%;height:100%;object-fit:cover;"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"></video>
                    <div class="no-img-gradient" style="display:none;"><i data-lucide="video"></i><span>Mídia Local / Publicada</span></div>`;
            } else {
                modalMediaEl = `<img src="${imgUrl}" alt="" style="width:100%;height:100%;object-fit:cover;"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
                    <div class="no-img-gradient" style="display:none;"><i data-lucide="image"></i><span>Mídia Local / Publicada</span></div>`;
            }
        } else {
            modalMediaEl = `<div class="no-img-gradient"><i data-lucide="${isVid?'video':'image'}"></i><span>Mídia Local / Publicada</span></div>`;
        }

    const metCard = (label, val, color='var(--text)') => `
        <div style="background:rgba(255,255,255,0.01);border:1px solid var(--border);padding:.5rem;border-radius:8px;text-align:center;">
            <div style="font-size:.62rem;color:var(--text-sec);text-transform:uppercase;margin-bottom:.15rem;">${label}</div>
            <div style="font-size:.95rem;font-weight:700;color:${color};">${val}</div>
        </div>`;

    const modalContent = `
        <div class="post-media ${mediaClass}" style="height:220px;width:100%;">
            <span class="post-tag">${tag}</span>
            ${modalMediaEl}
        </div>
        <div style="padding:1.4rem;max-height:420px;overflow-y:auto;display:flex;flex-direction:column;gap:1rem;">
            <div>
                <h3 style="font-size:1.05rem;font-weight:700;color:var(--neon-blue);margin-bottom:.5rem;">${post.frase_visual||'Conteúdo do Post'}</h3>
                <p style="font-size:.87rem;color:var(--text);line-height:1.6;word-break:break-word;">${legendaFormatada}</p>
            </div>

            <!-- Métricas básicas -->
            <div>
                <div style="font-size:.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:.5rem;">📊 Métricas Básicas</div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.45rem;">
                    ${metCard('Alcance', reach)}
                    ${metCard('Curtidas', likes, 'var(--ig)')}
                    ${metCard('Saves', saves, 'var(--neon-purple)')}
                    ${metCard('Shares', shares, 'var(--neon-green)')}
                </div>
            </div>

            <!-- Métricas avançadas -->
            <div>
                <div style="font-size:.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:.5rem;">🔬 Métricas Avançadas</div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.45rem;">
                    ${metCard('Visitas Perfil', profVisits, 'var(--neon-blue)')}
                    ${metCard('Novos Seguid.', follows, 'var(--neon-green)')}
                    ${metCard('Taxa Salvam.', taxaSalv, 'var(--neon-purple)')}
                    ${metCard('Taxa Compart.', taxaComp, '#ff9100')}
                    ${metCard('Retenção', retencao, 'var(--neon-gold)')}
                    ${metCard('Tempo Assistido', avgWatch, 'var(--neon-blue)')}
                </div>
            </div>

            <!-- Rodapé -->
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:.75rem;color:var(--text-muted);border-top:1px solid var(--border);padding-top:.8rem;flex-wrap:wrap;gap:.5rem;">
                <span>🏷️ Tema: <strong>${post.tema||'espiritualidade'}</strong></span>
                <span>📅 Data: <strong>${fmtDataCompleta(post.data)}</strong></span>
                ${permalink ? `<a href="${permalink}" target="_blank" rel="noopener" style="color:var(--ig);font-weight:600;text-decoration:none;">🔗 Ver no Instagram</a>` : ''}
            </div>
        </div>`;

    document.getElementById('modal-body-content').innerHTML = modalContent;
    document.getElementById('post-modal').style.display = 'flex';
    lucide.createIcons();
}

function fecharModalPost(e) {
    if (e && e.target !== document.getElementById('post-modal')) return;
    document.getElementById('post-modal').style.display = 'none';
}

// ── UTILITÁRIOS ──────────────────────────────────────────
function formatarLegenda(str) {
    if (!str) return 'Sem legenda gerada.';
    return str.replace(/\|/g, '<br><br>').replace(/\n/g, '<br>');
}

function fmt(n) { return Number(n).toLocaleString('pt-BR'); }

function fmtData(str) {
    if (!str) return '--';
    const d = new Date(str);
    if (isNaN(d)) return str;
    return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}`;
}

function fmtDataCompleta(str) {
    if (!str) return '--';
    const d = new Date(str);
    if (isNaN(d)) return str;
    return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()} às ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

function rec(html) { return `<div class="rec-item">${html}</div>`; }

// ── INIT ─────────────────────────────────────────────────
lucide.createIcons();
carregarTudo();
