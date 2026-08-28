// Inicializa o Firebase usando a configuração global importada
if (typeof firebaseConfig !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
} else {
    console.error("Configuração 'firebaseConfig' não encontrada. Verifique se o arquivo firebase-config.js foi importado antes do app.js.");
}
const db = firebase.firestore();

// ── ESTADO GLOBAL ────────────────────────────────────────
let postsData = [];
let metricasIG = {};
let metricasContaIG = {};
let metricasYT = {};
let leadsData = [];
let leadsCount = 0;
let filtroAtivo = 'todos';
let leadsBuscaAtiva = '';

let chartIGLine = null;
let chartYTLine = null;
let chartFormatos = null;
let chartEstrategia = null;
let chartLeadsDia = null;
let chartLeadsOrigem = null;

// Configurações de exibição dos gráficos
let igMetricaAtiva = 'reach';
let ytMetricaAtiva = 'views';
let igZoomCount = 15;
let ytZoomCount = 15;

const NOMES_METRICAS = {
    reach: 'Alcance',
    likes: 'Curtidas',
    comments: 'Comentários',
    saved: 'Salvamentos',
    shares: 'Compartilhamentos',
    profile_visits: 'Visitas ao Perfil',
    follows: 'Novos Seguidores',
    ig_reels_avg_watch_time: 'Retenção Reels (ms)',
    views: 'Visualizações',
    minutes: 'Minutos Assistidos'
};

// ── NAVEGAÇÃO ────────────────────────────────────────────
const TABS = {
    overview: ['Visão Geral', 'Performance do robô separada por plataforma'],
    criador: ['Studio de Criação', 'Crie, visualize e publique postagens personalizadas'],
    cientista: ['Cientista de Dados', 'Recomendações e hipóteses do motor de análise'],
    leads: ['Leads Capturados', 'Histórico e análise dos leads captados pela landing page'],
    posts: ['Histórico de Postagens', 'Todos os conteúdos gerados e publicados recentemente'],
    caminho: ['Caminho do Visitante', 'Histórico em tempo real da jornada e respostas de cada visitante'],
    pdfs: ['Biblioteca de PDFs & Campanhas', 'Histórico completo de e-books gerados e campanhas de captura de leads']
};

function goTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    document.getElementById('nav-' + name).classList.add('active');
    document.getElementById('page-title').innerText = TABS[name][0];
    document.getElementById('page-sub').innerText = TABS[name][1];

    // Persiste a aba ativa para sobreviver ao reload da página
    localStorage.setItem('dashboard_aba_ativa', name);

    if (name === 'criador') {
        carregarSolicitacoes();
    } else if (name === 'caminho') {
        carregarCaminhoVisitantes();
    } else if (name === 'pdfs') {
        renderizarHistoricoPDFs();
    }
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
    // Atualiza os dados da aba ATUAL sem forçar volta para 'Visão Geral'
    const abaAtual = localStorage.getItem('dashboard_aba_ativa') || 'overview';

    if (abaAtual === 'caminho') {
        await carregarCaminhoVisitantes();
        return;
    }
    if (abaAtual === 'criador') {
        await carregarSolicitacoes();
        return;
    }

    // Para as outras abas, recarrega todos os dados mantendo a aba atual
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
            leadsData = [];
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
                const elTema = document.getElementById('val-tema');
                const elGancho = document.getElementById('val-gancho');
                const elCta = document.getElementById('val-cta');
                if (elTema) elTema.innerText = d.tema_do_dia || '--';
                if (elGancho) elGancho.innerText = d.indice_gancho ?? '--';
                if (elCta) elCta.innerText = d.indice_cta ?? '--';
            }
        } catch (e) { console.warn('Estado bot:', e); }

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

        // 4b. Métricas Conta Instagram (Consolidados globais da conta)
        metricasContaIG = {};
        try {
            const contaSnap = await db.collection('metricas_conta_instagram').doc('consolidados').get();
            if (contaSnap.exists) {
                metricasContaIG = contaSnap.data();
            }
        } catch (e) {
            console.warn('Erro ao ler metricas_conta_instagram:', e);
        }

        // Merge: todos os posts que têm métrica OU estão no histórico do bot
        const todosPostsMap = {};
        // 1º adiciona descobertos pela API (via metricas_posts)
        Object.entries(metricasPostsMap).forEach(([pid, info]) => {
            todosPostsMap[pid] = {
                post_id: pid,
                data: info.data || '',
                tipo: info.tipo || 'feed',
                tema: info.tema || 'Descoberto',
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

        // 7. Caminho do Visitante
        try {
            await carregarCaminhoVisitantes();
        } catch (e) {
            console.warn('Erro ao carregar caminho dos visitantes:', e);
        }

        // 8. Cientista (async isolado)
        try {
            await carregarCientista();
        } catch (e) {
            console.warn('Erro ao carregar dados do cientista:', e);
        }

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

    if (metricasContaIG && metricasContaIG.reach_30d) {
        alcanceIG = metricasContaIG.reach_30d;
        profileVisitsTotal = metricasContaIG.profile_views_30d || 0;
        followsTotal = metricasContaIG.follower_count_30d || 0;
    }

    // Fallback: se follower_count_30d for 0 (limitação de privacidade da Meta),
    // soma os seguidores vindos individualmente de cada post publicado.
    if (followsTotal === 0) {
        Object.values(metricasIG).forEach(m => {
            followsTotal += m.follows || 0;
        });
    }

    // Fallback: se alcance global for 0, soma o alcance de cada post
    if (alcanceIG === 0) {
        Object.values(metricasIG).forEach(m => {
            alcanceIG += m.reach || 0;
            profileVisitsTotal += m.profile_visits || 0;
        });
    }

    // Taxa de Conversão (Leads / Alcance IG)
    if (alcanceIG > 0 && leadsCount > 0) {
        const rate = (leadsCount / alcanceIG) * 100;
        document.getElementById('funnel-rate').innerText = rate.toFixed(2) + '%';
    } else {
        document.getElementById('funnel-rate').innerText = '0,00%';
    }

    document.getElementById('funnel-followers').innerText = followsTotal != null ? fmt(followsTotal) : '--';
    document.getElementById('funnel-profile-visits').innerText = profileVisitsTotal != null ? fmt(profileVisitsTotal) : '--';
}

// ── TENDÊNCIA (compara última semana vs semana anterior) ─
function calcularTendencia(posts7, posts14) {
    // Divide posts em dois grupos: 0-7 dias e 7-14 dias
    const agora = Date.now();
    const limiar7 = agora - 7 * 86400000;
    const limiar14 = agora - 14 * 86400000;

    function somaMetrica(lista, metrica) {
        return lista.reduce((acc, p) => {
            const m = metricasIG[p.post_id] || {};
            if (metrica === 'likes') return acc + (m.likes || m.like_count || 0);
            if (metrica === 'comments') return acc + (m.comments || m.comments_count || 0);
            if (metrica === 'saved') return acc + (m.saved || 0);
            if (metrica === 'shares') return acc + (m.shares || 0);
            if (metrica === 'profile_visits') return acc + (m.profile_visits || 0);
            if (metrica === 'follows') return acc + (m.follows || 0);
            if (metrica === 'ig_reels_avg_watch_time') return acc + (m.ig_reels_avg_watch_time || 0);
            return acc + (m.reach || 0);
        }, 0);
    }

    const recentes = postsData.filter(p => new Date(p.data).getTime() >= limiar7);
    const anteriores = postsData.filter(p => {
        const t = new Date(p.data).getTime();
        return t >= limiar14 && t < limiar7;
    });

    const metricas = ['reach', 'likes', 'comments', 'saved', 'shares', 'profile_visits', 'follows', 'ig_reels_avg_watch_time'];
    const res = {};
    metricas.forEach(m => {
        const atual = somaMetrica(recentes, m);
        const ant = somaMetrica(anteriores, m);
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
    let reach = 0, likes = 0, comments = 0, saves = 0, shares = 0, profVisits = 0, follows = 0, avgWatch = 0, watchCount = 0;

    // Engajamento acumulado dos posts
    Object.values(metricasIG).forEach(m => {
        likes += m.likes || m.like_count || 0;
        comments += m.comments || m.comments_count || 0;
        saves += m.saved || 0;
        shares += m.shares || 0;
        if (m.ig_reels_avg_watch_time) { avgWatch += m.ig_reels_avg_watch_time; watchCount++; }
    });

    // Se temos os dados da conta consolidada, usamos para alcance, visitas e novos seguidores
    if (metricasContaIG && metricasContaIG.reach_30d) {
        reach = metricasContaIG.reach_30d;
        profVisits = metricasContaIG.profile_views_30d || 0;
        follows = metricasContaIG.follower_count_30d || 0;
    } else {
        Object.values(metricasIG).forEach(m => {
            reach += m.reach || 0;
        });
    }

    // Fallback de Visitas ao Perfil e Seguidores se o consolidado da conta retornar 0
    if (profVisits === 0) {
        Object.values(metricasIG).forEach(m => {
            profVisits += m.profile_visits || 0;
        });
    }
    if (follows === 0) {
        Object.values(metricasIG).forEach(m => {
            follows += m.follows || 0;
        });
    }

    document.getElementById('ig-reach').innerText = fmt(reach);
    document.getElementById('ig-likes').innerText = fmt(likes);
    document.getElementById('ig-comments').innerText = fmt(comments);
    document.getElementById('ig-saves').innerText = fmt(saves);
    document.getElementById('ig-shares').innerText = fmt(shares);
    document.getElementById('ig-profile-visits').innerText = profVisits != null ? fmt(profVisits) : '--';
    document.getElementById('ig-follows').innerText = follows != null ? fmt(follows) : '--';
    document.getElementById('ig-avg-watch').innerText = watchCount > 0 ? (avgWatch / watchCount / 1000).toFixed(1) + 's' : '--';

    // Indicadores de tendência
    const trends = calcularTendencia();
    renderTrend('trend-ig-reach', trends['reach']);
    renderTrend('trend-ig-likes', trends['likes']);
    renderTrend('trend-ig-comments', trends['comments']);
    renderTrend('trend-ig-saves', trends['saved']);
    renderTrend('trend-ig-shares', trends['shares']);
    renderTrend('trend-ig-profile_visits', trends['profile_visits']);
    renderTrend('trend-ig-follows', trends['follows']);
    renderTrend('trend-ig-avg_watch', trends['ig_reels_avg_watch_time']);
}

// ── MÉTRICAS YOUTUBE ─────────────────────────────────────
function renderMetricasYT() {
    let views = 0, likes = 0, comments = 0, shares = 0, minutes = 0;
    Object.values(metricasYT).forEach(m => {
        views += m.views || 0;
        likes += m.likes || 0;
        comments += m.comments || 0;
        shares += m.shares || 0;
        minutes += m.watch_time_minutes || m.estimated_minutes_watched || m.estimatedMinutesWatched || 0;
    });
    document.getElementById('yt-views').innerText = fmt(views);
    document.getElementById('yt-likes').innerText = fmt(likes);
    document.getElementById('yt-comments').innerText = fmt(comments);
    document.getElementById('yt-shares').innerText = fmt(shares);
    document.getElementById('yt-minutes').innerText = minutes > 0 ? fmt(Math.round(minutes)) + ' min' : '--';
}

// ── GRÁFICOS ─────────────────────────────────────────────
function renderGraficos() {
    if (chartIGLine) chartIGLine.destroy();
    if (chartYTLine) chartYTLine.destroy();
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
        if (igMetricaAtiva === 'likes') return m.likes || m.like_count || 0;
        if (igMetricaAtiva === 'comments') return m.comments || m.comments_count || 0;
        if (igMetricaAtiva === 'saved') return m.saved || 0;
        if (igMetricaAtiva === 'shares') return m.shares || 0;
        if (igMetricaAtiva === 'profile_visits') return m.profile_visits || 0;
        if (igMetricaAtiva === 'follows') return m.follows || 0;
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
        if (ytMetricaAtiva === 'likes') return m.likes || 0;
        if (ytMetricaAtiva === 'comments') return m.comments || 0;
        if (ytMetricaAtiva === 'shares') return m.shares || 0;
        if (ytMetricaAtiva === 'minutes') return Math.round(m.watch_time_minutes || m.estimated_minutes_watched || m.estimatedMinutesWatched || 0);
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
    let reels = 0, carousel = 0, stories = 0, outros = 0;
    postsData.forEach(p => {
        const t = (p.tipo || '').toLowerCase();
        if (t.includes('reel') || t.includes('pexels')) reels++;
        else if (t.includes('carousel')) carousel++;
        else if (t.includes('story')) stories++;
        else outros++;
    });
    chartFormatos = new Chart(document.getElementById('chart-formatos'), {
        type: 'doughnut',
        data: {
            labels: ['Reels/Vídeos', 'Carrossel', 'Stories', 'Outros'],
            datasets: [{ data: [reels, carousel, stories, outros], backgroundColor: ['#e1306c', '#7c4dff', '#ff9100', '#6b7280'], borderWidth: 0 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Outfit' }, padding: 10, boxWidth: 12 } } }
        }
    });
}

function chartOpts(color) {
    return {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: { labels: { color: '#9ca3af', font: { family: 'Outfit', size: 11 } } },
            tooltip: {
                backgroundColor: 'rgba(13,17,26,0.95)', titleColor: '#fff', bodyColor: '#e5e7eb',
                borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, padding: 10,
                titleFont: { family: 'Outfit', weight: 'bold' }, bodyFont: { family: 'Outfit' }
            }
        },
        scales: {
            x: { grid: { color: 'rgba(255,255,255,.03)' }, ticks: { color: '#9ca3af', font: { family: 'Outfit', size: 10 } } },
            y: { grid: { color: 'rgba(255,255,255,.03)' }, ticks: { color: '#9ca3af', font: { family: 'Outfit', size: 10 } }, beginAtZero: true }
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

            // Fallback de ICC: se não houver dados por post, estima usando dados globais da conta
            let iccParaRender = d.icc_por_tema || {};
            if (!Object.keys(iccParaRender).length && metricasContaIG) {
                const followsGlobal = metricasContaIG.follower_count_30d || 0;
                const visitasGlobal = metricasContaIG.profile_views_30d || 0;
                if (visitasGlobal > 0 && followsGlobal > 0) {
                    // Distribui o ICC global entre os temas na proporção dos pesos estratégicos
                    const pesos = d.peso_final_temas || {};
                    if (Object.keys(pesos).length) {
                        const iccGlobal = followsGlobal / visitasGlobal;
                        Object.entries(pesos).forEach(([tema, peso]) => {
                            iccParaRender[tema] = parseFloat((iccGlobal * peso).toFixed(4));
                        });
                        console.info('📊 ICC calculado via fallback global da conta:', iccParaRender);
                    } else {
                        iccParaRender['geral'] = parseFloat((followsGlobal / visitasGlobal).toFixed(4));
                    }
                }
            }
            renderICCRanking(iccParaRender);
            renderEstrategiaDonut(d.peso_final_temas || {});
            renderCopyRankings(d.ganchos_growth_score || {}, d.ctas_growth_score || {});
            renderRecomendacoes(d);

            // ── Novos painéis de Analytics ──
            renderOlhosDaRede(d);
        }
    } catch (e) {
        console.warn('Cientista de Dados erro:', e);
        renderGrowthScore(null);
    }

    // Hipóteses
    try {
        const snap = await db.collection('memoria_estrategica').doc('hipoteses').get();
        const tbody = document.getElementById('hipo-body');
        if (snap.exists) {
            const data = snap.data();
            const lista = data.hipoteses || data.historico_hipoteses || Object.values(data);
            const arr = Array.isArray(lista) ? lista : [];
            if (arr.length) {
                tbody.innerHTML = arr.map(h => {
                    const desc = h.descricao || h.texto || h.hipotese || JSON.stringify(h);
                    const st = (h.status || 'pendente').toLowerCase().replace(/\s+/g, '');
                    return `<tr><td>${desc}</td><td><span class="badge ${st}">${st.toUpperCase()}</span></td><td>${h.confianca || '--'}</td></tr>`;
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
    } catch (e) { console.warn('Hipóteses:', e); }

    // Heatmap de dias da semana (utiliza posts e métricas carregados da conta)
    try {
        const postsComMetricas = (postsData || []).map(p => ({
            ...p,
            growth_score: (metricasIG && metricasIG[p.post_id]?.growth_score) || p.growth_score || p.metricas?.growth_score || 0,
            metricas: (metricasIG && metricasIG[p.post_id]) || p.metricas || {}
        }));
        renderHeatmapDias(postsComMetricas);
    } catch (e) {
        console.warn('Heatmap dias:', e);
        renderHeatmapDias([]);
    }
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

    const gs = d.growth_score_referencia;
    // GS é uma fração pequena (ex: 0.012). Escala para 0-100 assumindo que 0.1 = 100% de excelência
    const pct = Math.min(gs / 0.1 * 100, 100);
    const cor = gs > 0.05 ? 'var(--neon-green)' : gs > 0.02 ? 'var(--neon-gold)' : 'var(--neon-purple)';

    numEl.innerText = (gs * 100).toFixed(3) + '%';
    numEl.style.color = cor;
    if (barEl) {
        barEl.style.width = pct.toFixed(1) + '%';
        barEl.style.background = `linear-gradient(90deg,${cor},rgba(0,229,255,.7))`;
        barEl.style.boxShadow = `0 0 10px ${cor}`;
    }
    if (cicEl) cicEl.innerText = d.ciclos_utilizados ? d.ciclos_utilizados.map(c => c.toUpperCase()).join(', ') : '--';
    if (tmaEl) tmaEl.innerText = d.tema_maior_icc ? d.tema_maior_icc.toUpperCase() : '--';
    if (atuEl) atuEl.innerText = d.atualizado_em ? d.atualizado_em.split(' ')[0] : '--';
}

// Ranking ICC
function renderICCRanking(icc) {
    const el = document.getElementById('icc-list');
    if (!el) return;
    const entries = Object.entries(icc).sort((a, b) => b[1] - a[1]);
    if (!entries.length) {
        el.innerHTML = '<div class="rec-item empty">Nenhum dado de ICC disponível. Execute um ciclo de analytics.</div>';
        return;
    }
    const max = entries[0][1] || 1;
    el.innerHTML = entries.map(([tema, val], i) => {
        const pct = ((val / max) * 100).toFixed(1);
        const isBest = i === 0;
        return `
        <div class="icc-item">
            <div class="icc-row">
                <span class="icc-tema">${isBest ? '🥇 ' : ''}${tema}</span>
                <span class="icc-valor">${(val * 100).toFixed(2)}%</span>
            </div>
            <div class="icc-track">
                <div class="icc-fill ${isBest ? 'best' : ''}" style="width:${pct}%"></div>
            </div>
        </div>`;
    }).join('');
}

// ── Olhos da Rede — Tendências e Manchetes da Semana ──────────────────────
function renderOlhosDaRede(d) {
    const el = document.getElementById('olhos-rede-grid');
    if (!el) return;

    // Pega dados de tendências e contexto salvos nas recomendações do motor estratégico
    const trends = d?.tendencias_semana || d?.trends_semana || [];
    const manchetes = d?.manchetes_semana || d?.noticias_semana || [];
    const vibeTexto = d?.vibe_foco_semana || d?.vibe_semana || d?.vibe_da_semana || '';
    const tudo = [];

    if (vibeTexto) {
        tudo.push({ tipo: '🧭 Vibe da Semana', texto: vibeTexto, cor: '#7c4dff' });
    }
    if (d?.aviso_estrategico) {
        tudo.push({ tipo: '⚠️ Alerta da Rede', texto: d.aviso_estrategico, cor: '#ff6464' });
    }
    if (d?.padroes_campeoes) {
        tudo.push({ tipo: '🏆 Padrão Campeão', texto: d.padroes_campeoes, cor: '#00e676' });
    }
    if (Array.isArray(d?.ideias_de_narrativa)) {
        d.ideias_de_narrativa.forEach(ideia => {
            let textoIdeia = '';
            if (typeof ideia === 'string') {
                textoIdeia = ideia;
            } else if (typeof ideia === 'object' && ideia !== null) {
                textoIdeia = [ideia.tema, ideia.gancho, ideia.desenvolvimento, ideia.cta].filter(Boolean).join(' → ');
            }
            if (textoIdeia) tudo.push({ tipo: '💡 Ideia de Roteiro', texto: textoIdeia, cor: '#ffd600' });
        });
    }
    if (Array.isArray(d?.temas_prioritarios)) {
        d.temas_prioritarios.forEach(tema => {
            tudo.push({ tipo: '🎯 Tema em Alta', texto: tema, cor: '#00e5ff' });
        });
    }
    manchetes.forEach(m => tudo.push({ tipo: '📰 Notícia', texto: m, cor: '#ff6464' }));
    trends.forEach(t => tudo.push({ tipo: '🔥 Google Trends', texto: t, cor: '#ffd600' }));

    if (!tudo.length) {
        el.innerHTML = '<div class="rec-item empty">Nenhuma tendência registrada ainda. O radar atualiza toda segunda-feira.</div>';
        return;
    }

    el.innerHTML = tudo.map(item => `
        <div class="olhos-rede-card" style="border-left: 3px solid ${item.cor};">
            <span class="olhos-rede-tipo" style="color:${item.cor};">${item.tipo}</span>
            <p class="olhos-rede-texto">${item.texto}</p>
        </div>
    `).join('');
}

// ── Heatmap de Melhores Dias da Semana ────────────────────────────────────
function renderHeatmapDias(posts) {
    const el = document.getElementById('heatmap-dias');
    if (!el) return;

    const dias = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const acum = Array(7).fill(0);
    const count = Array(7).fill(0);

    posts.forEach(p => {
        try {
            const dt = p.data ? new Date(p.data) : null;
            const gs = parseFloat(p.growth_score || p.metricas?.growth_score || 0);
            if (dt && !isNaN(dt) && gs > 0) {
                const dw = dt.getDay(); // 0=Dom .. 6=Sáb
                acum[dw] += gs;
                count[dw]++;
            }
        } catch (_) {}
    });

    const medias = acum.map((v, i) => count[i] > 0 ? v / count[i] : 0);
    const maxMedia = Math.max(...medias) || 1;

    if (maxMedia === 0 || medias.every(v => v === 0)) {
        el.innerHTML = '<div class="rec-item empty">Ainda não há posts suficientes com Growth Score registrado para montar o mapa de horários.</div>';
        return;
    }

    el.innerHTML = `
        <div class="heatmap-bars">
            ${dias.map((dia, i) => {
                const pct = ((medias[i] / maxMedia) * 100).toFixed(1);
                const isBest = medias[i] === maxMedia && medias[i] > 0;
                const cor = isBest ? 'var(--neon-green)' : medias[i] > maxMedia * 0.6 ? 'var(--neon-purple)' : 'rgba(255,255,255,0.15)';
                return `
                    <div class="heatmap-col">
                        <div class="heatmap-bar-track">
                            <div class="heatmap-bar-fill" style="height:${pct}%;background:${cor};box-shadow:${isBest ? '0 0 10px var(--neon-green)' : 'none'};"></div>
                        </div>
                        <div class="heatmap-day-label ${isBest ? 'best' : ''}">${dia}</div>
                        <div class="heatmap-gs-label">${medias[i] > 0 ? (medias[i] * 100).toFixed(2) + '%' : '—'}</div>
                        ${isBest ? '<div class="heatmap-best-badge">⭐ Melhor</div>' : ''}
                    </div>
                `;
            }).join('')}
        </div>
        <p style="font-size:.75rem;color:var(--text-sec);margin-top:1rem;text-align:center;">
            Baseado em ${posts.filter(p => p.growth_score || p.metricas?.growth_score).length} posts com GS registrado.
        </p>
    `;
}

// Donut de Estratégia do Bot
function renderEstrategiaDonut(pesos) {
    if (chartEstrategia) { chartEstrategia.destroy(); chartEstrategia = null; }
    const canvas = document.getElementById('chart-estrategia');
    const legEl = document.getElementById('estrategia-legend');
    if (!canvas || !legEl) return;

    const entries = Object.entries(pesos).sort((a, b) => b[1] - a[1]);
    if (!entries.length) {
        legEl.innerHTML = '<div style="color:var(--text-sec);font-size:.82rem;">Sem dados ainda.</div>';
        return;
    }

    const cores = [
        '#7c4dff', '#00e5ff', '#e1306c', '#00e676', '#ffd600',
        '#ff9100', '#ff1744', '#64ffda', '#ea80fc', '#82b1ff'
    ];
    const labels = entries.map(([t]) => t);
    const data = entries.map(([, v]) => +(v * 100).toFixed(1));

    chartEstrategia = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{ data, backgroundColor: cores.slice(0, labels.length), borderWidth: 0 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false }, tooltip: {
                    backgroundColor: 'rgba(13,17,26,.95)', titleColor: '#fff', bodyColor: '#e5e7eb',
                    bodyFont: { family: 'Outfit' }, titleFont: { family: 'Outfit', weight: 'bold' }
                }
            }
        }
    });

    legEl.innerHTML = entries.map(([tema, val], i) => `
        <div class="estrat-leg-item">
            <span class="estrat-dot" style="background:${cores[i] || '#666'}"></span>
            <span class="estrat-nome">${tema}</span>
            <span class="estrat-pct">${(val * 100).toFixed(0)}%</span>
        </div>`).join('');
}

// Rankings de Copy
function renderCopyRankings(ganchos, ctas) {
    const posEmoji = ['rank-1', 'rank-2', 'rank-3'];

    function renderLista(containerId, dados) {
        const el = document.getElementById(containerId);
        if (!el) return;
        const entries = Object.entries(dados).sort((a, b) => b[1] - a[1]).slice(0, 5);
        if (!entries.length) {
            el.innerHTML = '<div class="rec-item empty">Execute um ciclo de analytics para ver este ranking.</div>';
            return;
        }
        el.innerHTML = entries.map(([nome, gs], i) => `
        <div class="copy-rank-item">
            <div class="copy-rank-pos ${posEmoji[i] || ''}">${i + 1}</div>
            <div class="copy-rank-nome">${nome}</div>
            <div class="copy-rank-gs">GS: ${(gs * 10000).toFixed(2)}</div>
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

    // Função auxiliar local para formatar cada item de recomendação
    const recHtml = (titulo, texto, tipo = 'info') => {
        let borderCor = 'var(--neon-blue)';
        let bgCor = 'rgba(255, 255, 255, 0.02)';

        if (tipo === 'aviso') {
            borderCor = '#ff3b30';
            bgCor = 'rgba(255, 59, 48, 0.04)';
        } else if (tipo === 'vibe') {
            borderCor = 'var(--neon-purple)';
            bgCor = 'rgba(124, 77, 255, 0.04)';
        } else if (tipo === 'padrao') {
            borderCor = 'var(--neon-green)';
            bgCor = 'rgba(0, 230, 118, 0.04)';
        } else if (tipo === 'ideias') {
            borderCor = 'var(--neon-gold)';
            bgCor = 'rgba(255, 214, 0, 0.04)';
        }

        if (tipo === 'info') {
            // Estilo idêntico ao clássico (caixa azul sem título separado)
            return `
            <div class="rec-item" style="border-left: 3px solid var(--neon-blue); background: rgba(255,255,255,0.015); margin-bottom: 0.8rem; border-radius: 0 8px 8px 0; padding: 0.8rem 1rem; font-size: 0.88rem; line-height: 1.5; color: var(--text-sec);">
                ${texto}
            </div>
            `;
        }

        return `
        <div class="rec-item" style="border-left: 3px solid ${borderCor}; background: ${bgCor}; margin-bottom: 0.8rem; border-radius: 0 8px 8px 0; padding: 0.8rem 1rem;">
            <div style="font-weight: 700; font-size: 0.76rem; text-transform: uppercase; color: ${borderCor}; margin-bottom: 0.25rem; letter-spacing: 0.4px;">${titulo}</div>
            <div style="font-size: 0.86rem; line-height: 1.45; color: var(--text-sec);">${texto}</div>
        </div>
        `;
    };

    let html = '';

    // 1. AVISO ESTRATÉGICO DA IA (Maior Prioridade)
    if (d.aviso_estrategico) {
        html += recHtml('⚠️ Aviso Urgente da IA', d.aviso_estrategico, 'aviso');
    }

    // 2. VIBE DA SEMANA
    if (d.vibe_da_semana) {
        html += recHtml('🔮 Vibe de Foco da Semana', d.vibe_da_semana, 'vibe');
    }

    // 3. PADRÕES CAMPEÕES (O que bombou)
    if (d.padroes_campeoes) {
        html += recHtml('📈 Padrões Campeões Identificados', d.padroes_campeoes, 'padrao');
    }

    // 4. GANCHOS EXCLUSIVOS SUGERIDOS
    if (d.ganchos_exclusivos && d.ganchos_exclusivos.length) {
        const listGanchos = d.ganchos_exclusivos.map(g => `<li style="margin-bottom: 0.3rem;">"${g}"</li>`).join('');
        html += recHtml('🎣 Ganchos Exclusivos Sugeridos', `<ul style="margin: 0; padding-left: 1.1rem; font-size: 0.83rem;">${listGanchos}</ul>`, 'ideias');
    }

    // 5. IDEIAS DE NARRATIVA
    if (d.ideias_de_narrativa && d.ideias_de_narrativa.length) {
        const listNarrativas = d.ideias_de_narrativa.map(n => {
            let txt = '';
            if (typeof n === 'string') {
                txt = n;
            } else if (typeof n === 'object' && n !== null) {
                txt = [n.tema, n.gancho, n.desenvolvimento, n.cta].filter(Boolean).join(' → ');
            }
            return `<li style="margin-bottom: 0.5rem;">${txt}</li>`;
        }).join('');
        html += recHtml('💡 Ideias de Narrativa para Explorar', `<ul style="margin: 0; padding-left: 1.1rem; font-size: 0.83rem;">${listNarrativas}</ul>`, 'ideias');
    }

    // --- RECOMENDAÇÕES MATEMÁTICAS CLÁSSICAS ---
    if (d.growth_score_referencia !== undefined) {
        html += recHtml(null, `📊 <strong>Growth Score de Referência:</strong> ${(d.growth_score_referencia * 100).toFixed(3)}%`, 'info');
    }

    if (d.peso_final_temas) {
        Object.entries(d.peso_final_temas).sort((a, b) => b[1] - a[1]).slice(0, 4).forEach(([t, p]) => {
            html += recHtml(null, `🏆 <strong>${t}:</strong> ${(p * 100).toFixed(1)}% do mix de conteúdo`, 'info');
        });
    }

    if (d.ciclos_utilizados && d.ciclos_utilizados.length) {
        html += recHtml(null, `🔄 <strong>Ciclos analisados:</strong> ${d.ciclos_utilizados.join(', ').toUpperCase()}`, 'info');
    }

    if (d.atualizado_em) {
        html += `<div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 0.6rem; text-align: right;">Atualizado em: ${d.atualizado_em}</div>`;
    }

    box.innerHTML = html || '<div class="rec-item empty">Dados incompletos. Aguarde o próximo ciclo.</div>';
}

// ── LEADS ────────────────────────────────────────────────
function renderLeads() {
    if (!leadsData) return;
    const agora = Date.now();
    const limiarSem = agora - 7 * 86400000;
    const limiarHoj = agora - 86400000;

    let semana = 0, hoje = 0;
    leadsData.forEach(l => {
        const ts = extrairTimestampLead(l);
        if (ts >= limiarSem) semana++;
        if (ts >= limiarHoj) hoje++;
    });

    const el = (id, v) => { const e = document.getElementById(id); if (e) e.innerText = v; };
    el('leads-total', fmt(leadsCount));
    el('leads-semana', fmt(semana));
    el('leads-hoje', fmt(hoje));

    // Taxa de Conversão
    let alcanceIG = 0;
    if (metricasContaIG && metricasContaIG.reach_30d) {
        alcanceIG = metricasContaIG.reach_30d;
    } else {
        Object.values(metricasIG).forEach(m => { alcanceIG += m.reach || 0; });
    }
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
    if (l.data_captura) return new Date(l.data_captura).getTime();
    if (l.created_at && typeof l.created_at === 'string') return new Date(l.created_at).getTime();
    if (l.timestamp && typeof l.timestamp === 'string') return new Date(l.timestamp).getTime();
    // Firestore Timestamp já convertido pelo SDK compat (toDate)
    if (l.timestamp?.toDate) return l.timestamp.toDate().getTime();
    if (l.created_at?.toDate) return l.created_at.toDate().getTime();
    return 0;
}

function filtrarLeads(busca) {
    leadsBuscaAtiva = busca.toLowerCase();
    const filtrado = leadsData.filter(l => {
        const nome = (l.nome || l.name || '').toLowerCase();
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
    const ordenados = [...lista].sort((a, b) => extrairTimestampLead(b) - extrairTimestampLead(a));
    el.innerHTML = ordenados.map(l => {
        const nome = l.nome || l.name || '(sem nome)';
        const email = l.email || '(sem e-mail)';
        const ts = extrairTimestampLead(l);
        const data = ts ? fmtDataCompleta(new Date(ts).toISOString()) : '--';
        return `<div class="lead-row">
            <span>${nome}</span>
            <span class="lead-email">${email}</span>
            <span class="lead-date">${data}</span>
        </div>`;
    }).join('');
}

function renderLeadsGraficos() {
    if (chartLeadsDia) { chartLeadsDia.destroy(); chartLeadsDia = null; }
    if (chartLeadsOrigem) { chartLeadsOrigem.destroy(); chartLeadsOrigem = null; }

    const canvasDia = document.getElementById('chart-leads-dia');
    const canvasOrigem = document.getElementById('chart-leads-origem');
    if (!canvasDia || !canvasOrigem) return;

    // Agrupa leads por dia (últimos 30 dias)
    const dias = {};
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    for (let i = 29; i >= 0; i--) {
        const d = new Date(hoje); d.setDate(d.getDate() - i);
        const key = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
        dias[key] = 0;
    }
    leadsData.forEach(l => {
        const ts = extrairTimestampLead(l);
        if (!ts) return;
        const d = new Date(ts);
        const key = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
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
            datasets: [{ data: origensEntries.map(([, v]) => v), backgroundColor: ['#ffd600', '#7c4dff', '#00e5ff', '#00e676', '#ff1744'], borderWidth: 0 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Outfit' }, padding: 10, boxWidth: 12 } } }
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
    const grid = document.getElementById('posts-grid');

    // ── FILTRO ESPECIAL: Acima da Média ──────────────────────────────────────
    if (tipo === 'acima_media') {
        // Calcula um growth_score simplificado para cada post usando as métricas do Instagram
        const postsComScore = postsData.map(p => {
            const m = metricasIG[p.post_id] || {};
            const views = m.reach || m.plays || m.video_views || 0;
            const saves = m.saved || 0;
            const shares = m.shares || 0;
            const follows = m.follows || 0;
            const gs = views + (saves * 5) + (shares * 3) + (follows * 10);
            return { ...p, _gs: gs };
        }).filter(p => p._gs > 0); // apenas posts com alguma métrica

        if (!postsComScore.length) {
            grid.innerHTML = '<div class="empty-state"><i data-lucide="bar-chart-2"></i><span>Sem métricas disponíveis para calcular desempenho. Aguarde a próxima coleta de analytics.</span></div>';
            lucide.createIcons(); return;
        }

        const mediaGs = postsComScore.reduce((s, p) => s + p._gs, 0) / postsComScore.length;
        const limiteViral = mediaGs * 2.0;

        const bombaram = postsComScore.filter(p => p._gs >= limiteViral).sort((a, b) => b._gs - a._gs);
        const acimaMedia = postsComScore.filter(p => p._gs >= mediaGs && p._gs < limiteViral).sort((a, b) => b._gs - a._gs);

        if (!bombaram.length && !acimaMedia.length) {
            grid.innerHTML = '<div class="empty-state"><i data-lucide="inbox"></i><span>Nenhuma postagem acima da média ainda.</span></div>';
            lucide.createIcons(); return;
        }

        let html = '';
        if (bombaram.length) {
            html += `<div class="perf-section-title">🔥 Postagens que Bombaram <span>(acima de 2× a média — score médio: ${Math.round(mediaGs).toLocaleString('pt-BR')})</span></div>`;
            html += `<div class="post-row-container">${bombaram.map(p => renderPostCard(p, '🔥 VIRAL')).join('')}</div>`;
        }
        if (acimaMedia.length) {
            html += `<div class="perf-section-title" style="margin-top:2rem;">⭐ Acima da Média <span>(entre 1× e 2× a média)</span></div>`;
            html += `<div class="post-row-container">${acimaMedia.map(p => renderPostCard(p, '⭐ DESTAQUE')).join('')}</div>`;
        }
        grid.innerHTML = html;
        lucide.createIcons(); return;
    }

    const lista = postsData.filter(p => {
        if (tipo === 'todos') return true;
        const t = (p.tipo || '').toLowerCase();
        if (tipo === 'story') return t.includes('story') && !t.includes('pexels');
        if (tipo === 'reels') return (t.includes('reel') || t === 'reels_noite' || t === 'reels') && !t.includes('leads') && !t.includes('conquistador');
        if (tipo === 'pexels') return t.includes('pexels');
        if (tipo === 'especiais') return t.includes('leads') || t.includes('conquistador');
        if (tipo === 'carousel') return t.includes('carousel');
        return false;
    });
    if (!lista.length) {
        grid.innerHTML = '<div class="empty-state"><i data-lucide="inbox"></i><span>Nenhuma postagem neste filtro.</span></div>';
        lucide.createIcons(); return;
    }

    let html = `<div class="post-row-container">`;
    html += lista.map(p => renderPostCard(p)).join('');
    html += `</div>`;
    grid.innerHTML = html;
    lucide.createIcons();
}

// ── Renderiza o card de um post (extraído de renderPosts para reuso) ──────────
function renderPostCard(p, forcedTag) {
    const m = metricasIG[p.post_id] || {};
    const reach = fmt(m.reach || 0);
    const likes = fmt(m.likes || m.like_count || 0);
    const saves = fmt(m.saved || 0);
    const shares = fmt(m.shares || 0);
    const watchTimeMs = m.ig_reels_avg_watch_time || m.watch_time || 0;
    const watchTimeSec = watchTimeMs > 0 ? (watchTimeMs / 1000).toFixed(1) + 's' : (m.retencao ? `${m.retencao}s` : '--');

    // Determina a tag legível baseada no tipo e hora da postagem
    const tipoBruto = (p.tipo || 'post').toLowerCase();
    // Se uma tag forçada for passada (ex: '🔥 VIRAL'), usa ela. Senão, calcula a normal.
    let tag = forcedTag || tipoBruto.toUpperCase().replace(/_/g, ' ');
    if (!forcedTag) {
        if (tipoBruto === 'reels') {
            try {
                const dt = new Date(p.data);
                const hora = dt.getHours();
                if (hora < 11) tag = 'REELS MANHÃ';
                else if (hora >= 11 && hora < 16) tag = 'REELS TARDE';
                else tag = 'REELS NOITE';
            } catch (e) { tag = 'REELS'; }
        } else if (tipoBruto === 'story_manha') tag = 'STORY MANHÃ';
        else if (tipoBruto === 'story_tarde') tag = 'STORY TARDE';
        else if (tipoBruto === 'pexels_story') tag = 'PEXELS STORY MANHÃ';
        else if (tipoBruto === 'pexels_story_noite') tag = 'PEXELS STORY NOITE';
        else if (tipoBruto === 'reels_noite') tag = 'REELS NOITE';
        else if (tipoBruto === 'reels_conquistador') tag = 'REELS CONQUISTADOR';
        else if (tipoBruto === 'reels_leads') tag = 'REELS LEADS';
    }

    const tagLower = (forcedTag || tag).toLowerCase();
    const badgeClass = tagLower.includes('viral') ? 'reels' : tagLower.includes('destaque') ? 'especiais' : tagLower.includes('reel') ? 'reels' : tagLower.includes('story') ? 'story' : tagLower.includes('carousel') ? 'carousel' : 'default';

    // Extração e sanitização dos campos de DNA da postagem
    const objetivoVal = p.objetivo || 'Engajamento';
    const personaVal = p.estilo_copy || p.estilo || 'Mente Lúcida';
    const ganchoVal = p.gancho_categoria || 'Identidade';
    const tomVal = p.tom_emocional || 'Reflexão';
    const complexVal = p.complexidade || 'Média';
    const estruturaVal = p.estrutura_narrativa || p.arquitetura_nome || 'Problema-Solução';
    const subAnguloVal = p.sub_angulo || '';
    const ganchoAberturaVal = p.gancho_abertura || '';
    const estiloSorteadoVal = p.estilo_sorteado || '';
    const sentimentoPostVal = p.sentimento_post || '';
    const analyticsAtivo = p.analytics_ativo || false;
    const analyticsVibe = p.analytics_vibe || '';
    const analyticsPatterns = p.analytics_padroes || '';

    // Extração de mídias e recursos
    let pexelsQueriesHtml = '';
    const plataformaVal = p.plataforma_video || 'Automático / Biblioteca Local';
    const queryVideoVal = p.query_video || (p.pexels_queries ? (Array.isArray(p.pexels_queries) ? p.pexels_queries.join(', ') : p.pexels_queries) : '');

    if (queryVideoVal) {
        pexelsQueriesHtml = `<div><strong>Fundo (${plataformaVal}):</strong> "${queryVideoVal}"</div>`;
    } else if (p.prompt_imagem) {
        pexelsQueriesHtml = `<div><strong>Fundo IA:</strong> "${p.prompt_imagem}"</div>`;
    } else {
        pexelsQueriesHtml = `<div><strong>Fundo:</strong> ${plataformaVal}</div>`;
    }

    const musicaVal = p.musica_real || p.categoria_musica || 'Misteriosa / Ambiente';
    const duracaoVal = p.duracao_video ? `${p.duracao_video}s` : '--';

    // Formatação dos slides do post
    let slidesHtml = '';
    const slides = p.slides || p.frase || p.frase_visual || '';
    if (Array.isArray(slides)) {
        slidesHtml = slides.map((s, idx) => `
                <div class="post-row-slide-item">
                    <span class="post-row-slide-num">${idx + 1}.</span>
                    <span>${s.replace(/\\n/g, ' ')}</span>
                </div>
            `).join('');
    } else if (typeof slides === 'string' && slides.trim()) {
        if (slides.includes(' | ')) {
            const partes = slides.split(' | ');
            slidesHtml = partes.map((s, idx) => `
                    <div class="post-row-slide-item">
                        <span class="post-row-slide-num">${idx + 1}.</span>
                        <span>${s.trim()}</span>
                    </div>
                `).join('');
        } else {
            slidesHtml = `
                    <div class="post-row-slide-item">
                        <span class="post-row-slide-num">1.</span>
                        <span>${slides}</span>
                    </div>
                `;
        }
    } else {
        slidesHtml = `<div>Nenhum slide registrado.</div>`;
    }

    const legendaLimpa = (p.legenda || 'Sem legenda.').replace(/</g, '&lt;');
    const legendaFormatada = formatarLegenda(legendaLimpa);

    const permalink = m.permalink || '';

    return `
        <article class="post-row">
            <!-- Cabeçalho do Bloco -->
            <div class="post-row-header">
                <div class="post-row-title-wrap">
                    <span class="post-row-badge ${badgeClass}">${tag}</span>
                    <strong style="font-size:0.95rem;color:var(--text)">🏷️ ${p.tema || 'espiritualidade'} ${p.subtema ? ` | ${p.subtema}` : ''}</strong>
                </div>
                <span class="post-row-date">📅 ${fmtDataCompleta(p.data)}</span>
            </div>

            <!-- Tags de DNA Estratégico -->
            <div class="post-row-dna">
                <div class="post-row-dna-chip tema-chip" title="Tema da Postagem" style="border: 1px solid rgba(255,214,0,0.3); color: var(--neon-gold);"><i data-lucide="book-open"></i> Tema: ${p.tema || 'Geral'}</div>
                <div class="post-row-dna-chip" title="Objetivo da Postagem"><i data-lucide="target"></i> Objetivo: ${objetivoVal}</div>
                <div class="post-row-dna-chip" title="Estilo de Copy / Persona"><i data-lucide="cpu"></i> Persona: ${personaVal.split('(')[0].trim()}</div>
                <div class="post-row-dna-chip gancho-chip" title="Gatilho de Gancho" style="border: 1px solid rgba(0,229,255,0.3); color: var(--neon-blue);"><i data-lucide="magnet"></i> Gancho: ${ganchoVal}</div>
                <div class="post-row-dna-chip cta-chip" title="Chamada para Ação (CTA)" style="border: 1px solid rgba(124,77,255,0.3); color: var(--neon-purple);"><i data-lucide="megaphone"></i> CTA: ${p.tipo_cta || 'Nenhum'}</div>
                <div class="post-row-dna-chip" title="Tom Emocional"><i data-lucide="theater"></i> Tom: ${tomVal}</div>
                <div class="post-row-dna-chip" title="Estrutura Narrativa"><i data-lucide="align-left"></i> Estrutura: ${estruturaVal}</div>
                <div class="post-row-dna-chip" title="Complexidade"><i data-lucide="bar-chart-2"></i> Nível: ${complexVal}</div>
                ${subAnguloVal ? `<div class="post-row-dna-chip angulo" title="Ângulo Temático Sorteado"><i data-lucide="compass"></i> Ângulo: ${subAnguloVal}</div>` : ''}
                ${sentimentoPostVal ? `<div class="post-row-dna-chip sentimento" title="Sentimento da Postagem"><i data-lucide="heart-pulse"></i> Sentimento: ${sentimentoPostVal.toUpperCase()}</div>` : ''}
            </div>

            <!-- Recursos de Mídia -->
            <div class="post-row-media-box">
                <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.25rem;">
                    <span>⏱️ Duração: <strong>${duracaoVal}</strong></span>
                    <span>🎵 Trilha sugerida: <strong>${musicaVal}</strong></span>
                </div>
                <div style="border-top: 1px solid rgba(255,255,255,0.03); padding-top:0.4rem;">
                    ${pexelsQueriesHtml}
                </div>
            </div>

            <!-- Conteúdo Textual -->
            <div class="post-row-body-text">
                <div class="post-row-text-section">
                    <h4>📝 Texto dos Slides / Vídeo</h4>
                    <div class="post-row-slides-box">
                        ${slidesHtml}
                    </div>
                </div>
                <div class="post-row-text-section">
                    <h4>🧠 Briefing enviado para a IA</h4>
                    <div class="post-row-briefing-box">
                        ${ganchoAberturaVal ? `<div class="briefing-item"><span class="briefing-label">⚡ Gancho de Abertura:</span> <span>"${ganchoAberturaVal}"</span></div>` : ''}
                        ${subAnguloVal ? `<div class="briefing-item"><span class="briefing-label">🧭 Ângulo Temático:</span> <span>${subAnguloVal}</span></div>` : ''}
                        ${estiloSorteadoVal ? `<div class="briefing-item"><span class="briefing-label">🎭 Estilo de Abordagem:</span> <span>${estiloSorteadoVal}</span></div>` : ''}
                        ${analyticsAtivo && analyticsVibe ? `<div class="briefing-item analytics-rec"><span class="briefing-label">🤖 Vibe do Analytics:</span> <span>${analyticsVibe}</span></div>` : ''}
                        ${analyticsAtivo && analyticsPatterns ? `<div class="briefing-item analytics-rec"><span class="briefing-label">📈 Padrão Aplicado:</span> <span>${analyticsPatterns}</span></div>` : ''}
                        ${!ganchoAberturaVal && !subAnguloVal && !estiloSorteadoVal ? `<div style="color:var(--text-muted);font-size:0.82rem;">Disponível em postagens geradas a partir de agora.</div>` : ''}
                    </div>
                </div>
                <div class="post-row-text-section">
                    <h4>💬 Legenda</h4>
                    <div class="post-row-caption-box">
                        ${legendaFormatada}
                    </div>
                </div>
            </div>

            <!-- Rodapé / Métricas -->
            <div class="post-row-footer">
                <div class="post-row-stats">
                    <div class="post-row-stat-item"><i data-lucide="eye"></i> <span>Alcance: <strong>${reach}</strong></span></div>
                    <div class="post-row-stat-item active-likes"><i data-lucide="heart"></i> <span>Curtidas: <strong>${likes}</strong></span></div>
                    <div class="post-row-stat-item active-saves"><i data-lucide="bookmark"></i> <span>Saves: <strong>${saves}</strong></span></div>
                    <div class="post-row-stat-item active-shares"><i data-lucide="share-2"></i> <span>Shares: <strong>${shares}</strong></span></div>
                    <div class="post-row-stat-item" style="color:var(--neon-gold);"><i data-lucide="timer"></i> <span>Retenção: <strong>${watchTimeSec}</strong></span></div>
                </div>
                ${permalink ? `<a href="${permalink}" target="_blank" rel="noopener" class="post-row-link" onclick="event.stopPropagation();"><i data-lucide="external-link"></i> Ver no Instagram</a>` : ''}
            </div>
        </article>
        `;
}

// ── MODAL DETALHES DO POST ────────────────────────────────
function abrirModalPost(postId) {
    const post = postsData.find(p => p.post_id === postId);
    if (!post) return;

    const m = metricasIG[postId] || {};
    const tag = (post.tipo || 'post').replace('_', ' ');
    const isVid = tag.includes('reel') || tag.includes('pexels');
    const imgUrl = m.media_url || '';

    let mediaClass = 'media-default';
    if (tag.includes('reel') || tag.includes('pexels')) mediaClass = 'media-reels';
    else if (tag.includes('story')) mediaClass = 'media-story';
    else if (tag.includes('carousel')) mediaClass = 'media-carousel';

    // Métricas básicas
    const reach = fmt(m.reach || 0);
    const likes = fmt(m.likes || m.like_count || 0);
    const saves = fmt(m.saved || 0);
    const shares = fmt(m.shares || 0);

    // Métricas avançadas
    const profVisits = m.profile_visits ? fmt(m.profile_visits) : '--';
    const follows = m.follows ? fmt(m.follows) : '--';
    const ctrFeed = m.CTR_feed ? (m.CTR_feed * 100).toFixed(1) + '%' : (m.taxa_salvamento ? '--' : '--');
    const taxaSalv = m.taxa_salvamento ? (m.taxa_salvamento * 100).toFixed(1) + '%' : '--';
    const taxaComp = m.taxa_compartilhamento ? (m.taxa_compartilhamento * 100).toFixed(1) + '%' : '--';
    const retencao = m.retencao_media_pct ? (m.retencao_media_pct * 100).toFixed(1) + '%' : '--';
    const avgWatch = m.ig_reels_avg_watch_time ? (m.ig_reels_avg_watch_time / 1000).toFixed(1) + 's' : '--';
    const permalink = m.permalink || '';

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
        modalMediaEl = `<div class="no-img-gradient"><i data-lucide="${isVid ? 'video' : 'image'}"></i><span>Mídia Local / Publicada</span></div>`;
    }

    const legendaFormatada = formatarLegenda(post.legenda || '');

    const metCard = (label, val, color = 'var(--text)') => `
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
                <h3 style="font-size:1.05rem;font-weight:700;color:var(--neon-blue);margin-bottom:.5rem;">${post.frase_visual || 'Conteúdo do Post'}</h3>
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
                <span>🏷️ Tema: <strong>${post.tema || 'espiritualidade'}</strong></span>
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
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function fmtDataCompleta(str) {
    if (!str) return '--';
    const d = new Date(str);
    if (isNaN(d)) return str;
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()} às ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function rec(html) { return `<div class="rec-item">${html}</div>`; }

// ── LÓGICA DA ÁREA DO USUÁRIO / CRIADOR ─────────────────
let criadorModoTexto = 'ia';
let criadorTipoPost = 'reels';
let criadorSolicitacaoPendente = null;

function selecionarModoTexto(modo) {
    criadorModoTexto = modo;
    document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('active'));
    const target = document.getElementById('mode-' + modo);
    if (target) target.classList.add('active');
}

function selecionarTipoPost(tipo, element) {
    criadorTipoPost = tipo;
    document.querySelectorAll('.pt-card').forEach(c => c.classList.remove('active'));
    if (element) element.classList.add('active');
}

const NOMES_FORMATOS = {
    reels: 'Reels Tradicional',
    reels_leads: 'Reels Captura de Leads',
    pexels_story: 'Pexels Story (B-roll)',
    carousel: 'Carrossel Informativo',
    storytelling: 'Storytelling Noturno',
    story: 'Dupla de Stories',
    reels_conquistador: 'Reels Conquistador (VSL)'
};

function gerarPreviewPostagem() {
    const tema = document.getElementById('input-tema-livre').value.trim();
    const mensagem = document.getElementById('textarea-mensagem').value.trim();

    if (!tema && !mensagem) {
        alert("Por favor, preencha o Tema/Profissão ou a Mensagem antes de criar a pré-visualização.");
        return;
    }

    criadorSolicitacaoPendente = {
        tema: tema || 'Geral',
        modo_texto: criadorModoTexto,
        mensagem: mensagem || 'Conteúdo livre sobre o tema.',
        tipo_post: criadorTipoPost
    };

    // Preenche o painel de preview
    document.getElementById('prev-tema').innerText = criadorSolicitacaoPendente.tema;
    document.getElementById('prev-formato').innerText = NOMES_FORMATOS[criadorTipoPost] || criadorTipoPost;
    document.getElementById('prev-modo').innerText = (criadorModoTexto === 'ia')
        ? '🤖 IA Formular / Aprimorar'
        : '✍️ Texto Exato do Usuário';
    document.getElementById('prev-mensagem').innerText = criadorSolicitacaoPendente.mensagem;

    // Exibe a div de preview e ajusta a rolagem da tela
    const previewBox = document.getElementById('card-preview-criador');
    previewBox.style.display = 'block';
    previewBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
    lucide.createIcons();
}

async function dispararGitHubActions() {
    try {
        // Busca o token de forma segura do Firebase (nunca fica exposto no código)
        const configDoc = await db.collection('config').doc('sistema').get();
        const pat = configDoc.exists ? configDoc.data().github_pat : null;
        if (!pat) {
            console.error("❌ [Studio de Criação] Token do GitHub (github_pat) NÃO encontrado no Firebase (config/sistema). O robô não será ativado na nuvem. Configure o PAT no Firebase para que as postagens funcionem.");
            return false;
        }

        const res = await fetch('https://api.github.com/repos/gustavocapichoni/trabalhador1/actions/workflows/instagram_bot.yml/dispatches', {
            method: 'POST',
            headers: {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': `token ${pat}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ref: 'main',
                inputs: {
                    tipo_post: 'user_requests'
                }
            })
        });

        if (res.status === 204) {
            console.log("✅ [Studio de Criação] GitHub Actions disparado com sucesso! (HTTP 204)");
            return true;
        } else {
            // Tenta ler o corpo do erro para diagnóstico
            let errBody = '';
            try { errBody = await res.text(); } catch(_) {}
            console.error(`❌ [Studio de Criação] Falha ao disparar GitHub Actions. Status: ${res.status}. Resposta: ${errBody}`);
            return false;
        }
    } catch (e) {
        console.error("❌ [Studio de Criação] Erro ao chamar API do GitHub:", e);
        return false;
    }
}

async function confirmarPublicacao() {
    if (!criadorSolicitacaoPendente) return;

    const btn = document.getElementById('btn-pub-now');
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" class="spinner"></i> Disparando Robô na Nuvem...';
    lucide.createIcons();

    try {
        await db.collection('solicitacoes_postagem').add({
            tema: criadorSolicitacaoPendente.tema,
            modo_texto: criadorSolicitacaoPendente.modo_texto,
            mensagem: criadorSolicitacaoPendente.mensagem,
            tipo_post: criadorSolicitacaoPendente.tipo_post,
            status: 'pendente',
            solicitado_em: firebase.firestore.FieldValue.serverTimestamp()
        });

        // Dispara o acionamento no GitHub Actions e verifica se funcionou
        const disparouOk = await dispararGitHubActions();

        if (disparouOk) {
            alert("🚀 Sucesso! Sua postagem foi solicitada e o robô foi ativado na nuvem! Aguarde alguns minutos para a publicação.");
        } else {
            alert("⚠️ Postagem registrada com sucesso, porém não foi possível acionar o robô na nuvem automaticamente. Verifique o console do navegador para detalhes. Você pode acionar o workflow 'user_requests' manualmente no GitHub Actions.");
        }
        resetarFormularioCriador();
        await carregarSolicitacoes();
    } catch (e) {
        console.error("Erro ao salvar solicitação:", e);
        alert("⚠️ Erro ao salvar solicitação no Firebase: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="send"></i> 🚀 Publicar Agora';
        lucide.createIcons();
    }
}

function resetarFormularioCriador() {
    criadorSolicitacaoPendente = null;
    document.getElementById('input-tema-livre').value = '';
    document.getElementById('textarea-mensagem').value = '';
    document.getElementById('card-preview-criador').style.display = 'none';
    selecionarModoTexto('ia');
    const defaultPt = document.getElementById('pt-reels');
    if (defaultPt) selecionarTipoPost('reels', defaultPt);
}

async function carregarSolicitacoes() {
    const listEl = document.getElementById('user-requests-list');
    if (!listEl) return;

    try {
        const snap = await db.collection('solicitacoes_postagem').limit(20).get();
        if (snap.empty) {
            listEl.innerHTML = '<div class="empty-state"><i data-lucide="inbox"></i><span>Nenhuma solicitação enviada ainda.</span></div>';
            lucide.createIcons();
            return;
        }

        // Ordena no JS para não precisar de índice composto no Firebase
        const docs = [];
        snap.forEach(doc => docs.push({ id: doc.id, ...doc.data() }));
        docs.sort((a, b) => {
            const ta = a.solicitado_em?.seconds || 0;
            const tb = b.solicitado_em?.seconds || 0;
            return tb - ta;
        });
        const dez = docs.slice(0, 10);

        let html = '';
        dez.forEach(data => {
            const fmt = NOMES_FORMATOS[data.tipo_post] || data.tipo_post;
            const dataStr = data.solicitado_em ? fmtDataCompleta(data.solicitado_em.toDate()) : 'Recentemente';
            const statusClass = (data.status === 'publicado') ? 'status-publicado' : (data.status === 'erro') ? 'status-erro' : 'status-pendente';
            const statusLabel = (data.status === 'publicado') ? '✅ Publicado' : (data.status === 'erro') ? '❌ Erro' : '⏳ Pendente (Robô)';

            html += `
                <div class="req-item">
                    <div class="req-info">
                        <strong>${data.tema || 'Geral'}</strong>
                        <span style="color:var(--text-sec);">(${fmt})</span><br>
                        <small style="color:var(--text-muted);">${dataStr}</small>
                    </div>
                    <span class="req-status ${statusClass}">${statusLabel}</span>
                </div>
            `;
        });

        listEl.innerHTML = html;
        lucide.createIcons();
    } catch (e) {
        console.warn("Aviso ao carregar solicitações do usuário:", e);
        listEl.innerHTML = '<div class="empty-state"><i data-lucide="inbox"></i><span>Solicitações prontas para uso.</span></div>';
        lucide.createIcons();
    }
}

// ── CAMINHO DO VISITANTE (TELEMETRIA E JORNADA) ───────────
let caminhosData = [];
let filtroCaminhoCategoriaAtivo = 'todos';

async function carregarCaminhoVisitantes() {
    const container = document.getElementById('caminhos-list-container');
    if (!container) return;

    try {
        const snap = await db.collection('caminho_do_visitante').get();
        caminhosData = [];

        snap.forEach(doc => {
            caminhosData.push({ id: doc.id, ...doc.data() });
        });

        // Ordena pelos mais recentes com base no timestamp de chegada ou última atualização
        caminhosData.sort((a, b) => {
            const da = new Date(a.ultima_atualizacao || a.data_chegada || 0).getTime();
            const db = new Date(b.ultima_atualizacao || b.data_chegada || 0).getTime();
            return db - da;
        });

        // Atualiza as métricas do topo
        const total = caminhosData.length;
        const iniciou = caminhosData.filter(c => c.funil?.iniciou_quiz).length;
        const concluiu = caminhosData.filter(c => c.funil?.concluiu_quiz).length;
        const checkout = caminhosData.filter(c => c.funil?.clicou_checkout).length;

        document.getElementById('caminho-metric-total').innerText = total;
        document.getElementById('caminho-metric-iniciou').innerText = iniciou;
        document.getElementById('caminho-metric-concluiu').innerText = concluiu;
        document.getElementById('caminho-metric-checkout').innerText = checkout;

        renderizarCaminhoVisitantes();
    } catch (err) {
        console.error("Erro ao carregar caminho dos visitantes:", err);
        container.innerHTML = `
            <div class="empty-state" style="text-align:center; padding:3rem;">
                <i data-lucide="alert-circle" style="width:48px; height:48px; color:var(--neon-pink); margin-bottom:1rem;"></i>
                <p style="color:var(--text-muted);">Erro ao carregar dados do Firebase. Verifique a conexão.</p>
            </div>
        `;
        lucide.createIcons();
    }
}

const NOMES_EVENTOS_PT = {
    "page_view": "👁️ Entrou na página da Coletânea",
    "cta_click": "⚡ Clicou no botão 'Começar Desafio'",
    "quiz_start": "🚀 Iniciou o Quiz",
    "quiz_answer": "📝 Respondeu a Pergunta",
    "quiz_complete_click": "🎯 Clicou em Ver Resultado",
    "quiz_complete": "✅ Concluiu o Quiz",
    "offer_view": "⚡ Visualizou a Oferta Especial",
    "google_login": "🔑 Fez Login com Conta Google",
    "download_area": "📥 Acessou a Área de Download",
    "collection_click": "📚 Clicou em Acessar Material da Coletânea",
    "checkout_click": "🛒 Clicou para ir ao Checkout",
    "chatbot_open": "🤖 Abriu o Chatbot de Ajuda",
    "chatbot_option": "💬 Interagiu com o Chatbot"
};

function renderizarCaminhoVisitantes() {
    const container = document.getElementById('caminhos-list-container');
    if (!container) return;

    const termoBusca = (document.getElementById('caminho-search-input')?.value || '').toLowerCase().trim();

    const filtrados = caminhosData.filter(c => {
        const matchEmail = (c.usuario?.email || '').toLowerCase().includes(termoBusca);
        const matchNome = (c.usuario?.nome || '').toLowerCase().includes(termoBusca);
        const matchId = c.sessao_id.toLowerCase().includes(termoBusca);
        const bateBusca = matchEmail || matchNome || matchId;

        if (filtroCaminhoCategoriaAtivo === 'oferta') return bateBusca && c.funil?.chegou_oferta;
        if (filtroCaminhoCategoriaAtivo === 'checkout') return bateBusca && c.funil?.clicou_checkout;
        if (filtroCaminhoCategoriaAtivo === 'comprou') return bateBusca && c.funil?.comprou;
        return bateBusca;
    });

    if (filtrados.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="text-align:center; padding:3rem; background:var(--bg-card); border:1px solid var(--border); border-radius:16px;">
                <i data-lucide="inbox" style="width:48px; height:48px; color:var(--text-muted); margin-bottom:1rem;"></i>
                <p style="color:var(--text-muted);">Nenhum visitante encontrado com os filtros selecionados.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    let html = '';
    filtrados.forEach((c, index) => {
        const numVisitante = filtrados.length - index; // Numeração inversa para manter #1 no mais antigo ou sequencial
        const dataStr = c.data_chegada ? new Date(c.data_chegada).toLocaleString('pt-BR') : 'Desconhecido';
        
        const tituloVisitante = c.usuario?.email 
            ? `<strong style="color:var(--cyan); font-size:1.05rem;">${c.usuario.email}</strong> <span style="font-size:0.85rem; color:var(--text-muted);">(Visitante #${numVisitante})</span>`
            : `<strong style="color:var(--text-main); font-size:1.05rem;">👤 Visitante #${numVisitante}</strong> <span style="color:var(--text-muted); font-size:0.85rem;">(Anônimo)</span>`;

        const dispIcon = c.dispositivo?.tipo === 'mobile' ? '📱 Mobile' : '💻 Desktop';
        const inAppBadge = c.dispositivo?.embutido_instagram ? ' • <span style="color:var(--neon-pink);">Instagram Browser</span>' : '';

        // Status do funil em Badges
        let statusBadge = '<span class="req-status status-pendente">Entrou na Página</span>';
        if (c.funil?.comprou) {
            statusBadge = '<span class="req-status status-publicado" style="background:rgba(0,255,136,0.15); color:#00ff88; border:1px solid rgba(0,255,136,0.3);">✅ Comprou</span>';
        } else if (c.funil?.clicou_checkout) {
            statusBadge = '<span class="req-status" style="background:rgba(255,214,0,0.15); color:#ffd600; border:1px solid rgba(255,214,0,0.3);">🛒 Clicou no Checkout</span>';
        } else if (c.funil?.chegou_oferta) {
            statusBadge = '<span class="req-status" style="background:rgba(0,229,255,0.15); color:#00e5ff; border:1px solid rgba(0,229,255,0.3);">⚡ Chegou na Oferta</span>';
        } else if (c.funil?.concluiu_quiz) {
            statusBadge = '<span class="req-status" style="background:rgba(157,0,255,0.15); color:#a855f7; border:1px solid rgba(157,0,255,0.3);">🎯 Concluiu o Quiz</span>';
        } else if (c.funil?.iniciou_quiz) {
            statusBadge = `<span class="req-status status-pendente">Quiz (Etapa ${c.progresso?.etapa_maxima || 1})</span>`;
        }

        const respostasObj = c.progresso?.respostas || {};
        const qtdRespostas = Object.keys(respostasObj).length;

        html += `
            <div class="caminho-card" style="background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:1.2rem; display:flex; flex-direction:column; gap:1rem; transition:all 0.2s;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <div style="margin-bottom:0.2rem;">${tituloVisitante}</div>
                        <div style="font-size:0.82rem; color:var(--text-muted);">ID: <code>${c.sessao_id}</code> • ${dispIcon}${inAppBadge}</div>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.8rem;">
                        ${statusBadge}
                        <button onclick="removerCaminhoVisitante('${c.sessao_id}')" title="Excluir ficha deste visitante" style="background:rgba(255,0,85,0.1); border:1px solid rgba(255,0,85,0.3); color:#ff0055; padding:0.4rem 0.6rem; border-radius:8px; cursor:pointer; font-size:0.85rem; transition:all 0.2s;">
                            🗑️ Excluir
                        </button>
                    </div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:0.8rem 1rem; border-radius:8px; font-size:0.88rem; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <span style="color:var(--text-sec);">Entrou em:</span> <strong>${dataStr}</strong>
                    </div>
                    <div>
                        <span style="color:var(--text-sec);">Respostas no Quiz:</span> <strong>${qtdRespostas} / 5</strong>
                    </div>
                    <button class="btn-refresh" onclick="alternarDetalhesCaminho('${c.sessao_id}')" style="padding:0.4rem 0.8rem; font-size:0.82rem;">
                        👁️ Ver Jornada Completa
                    </button>
                </div>

                <!-- DETALHES EXPANSÍVEIS DO VISITANTE -->
                <div id="detalhes-${c.sessao_id}" style="display:none; border-top:1px solid var(--border); padding-top:1rem; margin-top:0.5rem;">
                    
                    <h4 style="color:var(--cyan); margin-bottom:0.8rem; font-size:0.95rem; display:flex; align-items:center; gap:6px;">
                        🧠 RESPOSTAS SELECIONADAS NO QUIZ
                    </h4>
                    <div style="display:flex; flex-direction:column; gap:0.5rem; margin-bottom:1.5rem; background:rgba(0,0,0,0.2); padding:1rem; border-radius:10px;">
                        ${respostasObj.p1 ? `<div><strong style="color:var(--neon-pink);">P1 (Objetivo):</strong> ${respostasObj.p1}</div>` : ''}
                        ${respostasObj.p2 ? `<div><strong style="color:var(--neon-pink);">P2 (Diferencial):</strong> ${respostasObj.p2}</div>` : ''}
                        ${respostasObj.p3 ? `<div><strong style="color:var(--neon-pink);">P3 (Uso de IA):</strong> ${respostasObj.p3}</div>` : ''}
                        ${respostasObj.p4 ? `<div><strong style="color:var(--neon-pink);">P4 (Prioridade):</strong> ${respostasObj.p4}</div>` : ''}
                        ${respostasObj.p6 ? `<div><strong style="color:var(--neon-pink);">P6 (Prontidão):</strong> ${respostasObj.p6}</div>` : ''}
                        ${qtdRespostas === 0 ? '<div style="color:var(--text-muted);">Nenhuma pergunta respondida.</div>' : ''}
                    </div>

                    <h4 style="color:var(--neon-gold); margin-bottom:0.8rem; font-size:0.95rem; display:flex; align-items:center; gap:6px;">
                        🕒 LINHA DO TEMPO DOS EVENTOS
                    </h4>
                    <div style="display:flex; flex-direction:column; gap:0.5rem; background:rgba(0,0,0,0.2); padding:1rem; border-radius:10px;">
                        ${(c.eventos || []).map(ev => {
                            const hora = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString('pt-BR') : '--:--';
                            const nomeEventoPt = NOMES_EVENTOS_PT[ev.tipo] || ev.tipo;
                            const detalheQuest = ev.numPergunta ? `(Pergunta ${ev.numPergunta})` : '';
                            const detalheOpcao = ev.opcao ? `- "${ev.opcao}"` : '';
                            return `<div style="font-size:0.88rem; display:flex; gap:8px; align-items:center;"><span style="color:var(--text-muted); font-family:monospace; font-size:0.8rem;">[${hora}]</span> <strong>${nomeEventoPt}</strong> <span style="color:var(--text-sec); font-size:0.82rem;">${detalheQuest} ${detalheOpcao}</span></div>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    lucide.createIcons();
}

async function removerCaminhoVisitante(sessaoId) {
    if (!confirm("Tem certeza que deseja remover esta ficha de visitante do sistema?")) return;
    try {
        await db.collection('caminho_do_visitante').doc(sessaoId).delete();
        caminhosData = caminhosData.filter(c => c.sessao_id !== sessaoId);
        renderizarCaminhoVisitantes();
    } catch (err) {
        console.error("Erro ao remover ficha do visitante:", err);
        alert("Erro ao remover a ficha do visitante do Firebase.");
    }
}

function alternarDetalhesCaminho(sessaoId) {
    const el = document.getElementById(`detalhes-${sessaoId}`);
    if (el) {
        el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }
}

function filtrarCaminhoCategoria(categoria, btn) {
    filtroCaminhoCategoriaAtivo = categoria;
    document.querySelectorAll('.leads-toolbar .btn-filter').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderizarCaminhoVisitantes();
}

function filtrarCaminhosVisitantes() {
    renderizarCaminhoVisitantes();
}

// ── HISTÓRICO DE PDFS E CAMPANHAS ───────────────────────
async function renderizarHistoricoPDFs() {
    const loadingEl = document.getElementById('pdfs-loading');
    const gridEl = document.getElementById('pdfs-grid');
    if (!gridEl) return;

    loadingEl.style.display = 'block';
    gridEl.style.display = 'none';

    try {
        // Busca coleções campanhas e historico_pdfs em paralelo
        const [campanhasSnap, histSnap] = await Promise.all([
            db.collection('campanhas').get(),
            db.collection('historico_pdfs').get()
        ]);

        const historicoMap = {};
        histSnap.forEach(doc => {
            historicoMap[doc.id] = doc.data();
        });

        const listaCampanhas = [];
        campanhasSnap.forEach(doc => {
            listaCampanhas.push({ id: doc.id, ...doc.data() });
        });

        // Ordena por criada_em decrescente
        listaCampanhas.sort((a, b) => {
            const tA = a.criada_em ? (a.criada_em.seconds || new Date(a.criada_em).getTime() / 1000) : 0;
            const tB = b.criada_em ? (b.criada_em.seconds || new Date(b.criada_em).getTime() / 1000) : 0;
            return tB - tA;
        });

        if (listaCampanhas.length === 0) {
            loadingEl.style.display = 'none';
            gridEl.style.display = 'block';
            gridEl.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-sec); padding: 2rem;">Nenhum PDF ou campanha encontrado.</div>';
            return;
        }

        let html = '';
        listaCampanhas.forEach((c, idx) => {
            const histInfo = historicoMap[c.semana] || {};
            const dataFmt = c.criada_em && c.criada_em.seconds 
                ? new Date(c.criada_em.seconds * 1000).toLocaleString('pt-BR')
                : (c.criada_em || '--');

            const beneficios = (c.landing_page && c.landing_page.beneficios) ? c.landing_page.beneficios : [];
            // Apenas a campanha mais recente (primeiro elemento da lista ordenada por data) recebe a tag de Ativa
            const isAtiva = (idx === 0);

                    const dorAlvo = c.dor_central || histInfo.dor_principal || '';
                    const contexto = c.contexto_semana || '';
                    const perfIA = c.dados_performance_perfil || '';

                    html += `
                        <div class="pdf-card ${isAtiva ? 'ativa' : ''}">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;">
                                <span class="pdf-badge-semana"><i data-lucide="calendar"></i> ${c.semana || 'Semana N/A'}</span>
                                ${isAtiva ? '<span class="pdf-badge-ativa"><i data-lucide="check-circle-2"></i> Campanha Ativa</span>' : ''}
                            </div>

                            <h3 class="pdf-titulo">${c.titulo || 'PDF Sem Título'}</h3>

                            <div class="pdf-meta-grid">
                                <div class="pdf-meta-item"><i data-lucide="book-open"></i> <strong>Livro Base:</strong> ${c.livro_base || 'N/A'}</div>
                                <div class="pdf-meta-item"><i data-lucide="compass"></i> <strong>Tema:</strong> ${c.tema || 'N/A'}</div>
                                ${dorAlvo ? `<div class="pdf-meta-item full"><i data-lucide="heart-pulse"></i> <strong>Dor Alvo:</strong> ${dorAlvo}</div>` : ''}
                            </div>

                            ${contexto ? `
                                <div class="pdf-intel-box">
                                    <div class="pdf-intel-title"><i data-lucide="globe"></i> Olhos da Rede (Tendências):</div>
                                    <p>${contexto}</p>
                                </div>
                            ` : ''}

                            ${perfIA ? `
                                <div class="pdf-intel-box">
                                    <div class="pdf-intel-title"><i data-lucide="brain-circuit"></i> Recomendação de Inteligência:</div>
                                    <pre style="white-space: pre-wrap; font-family: inherit; font-size: 0.78rem; margin: 0; color: var(--text-sec);">${perfIA}</pre>
                                </div>
                            ` : ''}

                            ${beneficios.length > 0 ? `
                                <div class="pdf-beneficios">
                                    <div class="pdf-beneficios-title"><i data-lucide="sparkles"></i> Benefícios da Landing Page:</div>
                                    <ul>
                                        ${beneficios.map(b => `<li>${b}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}

                            <div class="pdf-card-footer">
                                <span style="font-size: 0.78rem; color: var(--text-muted);">${dataFmt}</span>
                                ${c.pdf_url ? `
                                    <a href="${c.pdf_url}" target="_blank" class="pdf-btn-link">
                                        <i data-lucide="external-link"></i> Abrir PDF
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    `;
        });

        loadingEl.style.display = 'none';
        gridEl.style.display = 'grid';
        gridEl.innerHTML = html;

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Erro ao buscar histórico de PDFs:', err);
        loadingEl.style.display = 'none';
        gridEl.style.display = 'block';
        gridEl.innerHTML = `<div style="grid-column: 1/-1; color: #ff5252; text-align: center; padding: 2rem;">Erro ao carregar os dados de PDFs: ${err.message}</div>`;
    }
}

// ── TOGGLE SIDEBAR ───────────────────────────────────────
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main');
    const btn = document.getElementById('btn-toggle-sidebar');
    
    sidebar.classList.toggle('collapsed');
    main.classList.toggle('collapsed-sidebar');
    
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebar_collapsed', isCollapsed ? 'true' : 'false');
    
    if (btn) btn.classList.toggle('active', isCollapsed);
}

// Lógica de restauração inicial da sidebar
(() => {
    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    if (isCollapsed) {
        setTimeout(() => {
            const sidebar = document.querySelector('.sidebar');
            const main = document.querySelector('.main');
            const btn = document.getElementById('btn-toggle-sidebar');
            if (sidebar) sidebar.classList.add('collapsed');
            if (main) main.classList.add('collapsed-sidebar');
            if (btn) btn.classList.add('active');
        }, 50);
    }
})();

// ── INIT ─────────────────────────────────────────────────
lucide.createIcons();
// Restaura a última aba ativa salva (sobrevive ao reload da página)
(async () => {
    const abaRestaurada = localStorage.getItem('dashboard_aba_ativa') || 'overview';
    if (abaRestaurada !== 'overview' && TABS[abaRestaurada]) {
        // Ativa visualmente a aba salva sem chamar goTab (evita double-load)
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const tabEl = document.getElementById('tab-' + abaRestaurada);
        const navEl = document.getElementById('nav-' + abaRestaurada);
        if (tabEl) tabEl.classList.add('active');
        if (navEl) navEl.classList.add('active');
        document.getElementById('page-title').innerText = TABS[abaRestaurada][0];
        document.getElementById('page-sub').innerText = TABS[abaRestaurada][1];
    }
    await carregarTudo();
})();
