/* ==========================================================================
   APP.JS - LÓGICA DE NEGÓCIO, CÁLCULOS E GRÁFICOS
   ========================================================================== */

// Estado Global do Aplicativo
let state = {
    salaries: [],
    extraIncome: [],
    savedIncome: [],
    fixedExpenses: [],
    variableExpenses: [],
    unexpectedExpenses: [],
    investments: [],
    settings: {
        databasePath: "dados_financeiros.json",
        githubOwner: "RobsonSilva31",
        githubRepo: "gestor-financeiro",
        suggestions: {
            salaries: ["Salário Principal", "Salário Cônjuge", "Pró-labore"],
            extraIncome: ["Freelance", "Venda de Produto", "Rendimento", "Reembolso"],
            savedIncome: ["Reserva de Emergência", "Poupança de Emergência", "Caixa de Segurança"],
            fixedExpenses: ["Aluguel / Financiamento", "Condomínio", "Energia Elétrica", "Água e Esgoto", "Internet e TV", "Plano de Saúde", "Escola / Faculdade"],
            variableExpenses: ["Supermercado / Feira", "Combustível / Uber", "Restaurantes / Delivery", "Lazer / Cinema", "Roupas e Calçados", "Assinaturas (Netflix, Spotify)"],
            unexpectedExpenses: ["Mecânico / Oficina", "Farmácia / Médico", "Conserto Doméstico", "Presentes", "Impostos Anuais (IPVA/IPTU)"],
            investments: ["CDB 100% CDI", "Ações (B3)", "Fundos Imobiliários (FIIs)", "Tesouro Direto", "Poupança", "Criptomoedas"]
        }
    }
};

// Instâncias Globais dos Gráficos
let chartDistributionInstance = null;
let chartExpensesInstance = null;

// Inicialização do App
document.addEventListener("DOMContentLoaded", () => {
    // Inicializar com dados em branco / padrão se nada for carregado do Python
    initDefaultData();
    ensureDefaultSuggestions();
    
    // Inicializar ícones do Lucide
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Configurar Navegação de Abas
    setupTabs();
    
    // Configurar Eventos de Configurações e Salvamento
    setupEventListeners();
    
    // Preencher datalists de sugestões e inputs na UI
    populateDatalists();
    fillSuggestionsInputs();
    
    // Renderizar Tabelas e Gráficos Inicialmente
    renderAllTables();
    recalculateAll(false);
});

// Configuração de Eventos de Abas
function setupTabs() {
    const menuItems = document.querySelectorAll(".menu-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    const tabMeta = {
        dashboard: { title: "Dashboard Financeiro", subtitle: "Visão geral do seu patrimônio e fluxo de caixa." },
        incomes: { title: "Receitas & Rendas", subtitle: "Gerencie seus salários, rendas extras e reservas." },
        expenses: { title: "Despesas & Gastos", subtitle: "Monitore seus gastos fixos, variáveis e imprevistos." },
        investments: { title: "Investimentos", subtitle: "Acompanhe seus aportes e construção de patrimônio." },
        insights: { title: "Dicas & Insights", subtitle: "Diagnóstico automático baseado no seu comportamento de gastos." },
        settings: { title: "Configurações", subtitle: "Ajuste caminhos de dados e atualizações do software." }
    };

    menuItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            // Ativa botão no menu
            menuItems.forEach(btn => btn.classList.remove("active"));
            item.classList.add("active");
            
            // Ativa conteúdo
            tabContents.forEach(content => content.classList.remove("active"));
            document.getElementById(`tab-${targetTab}`).classList.add("active");
            
            // Atualiza cabeçalho
            if (tabMeta[targetTab]) {
                pageTitle.innerText = tabMeta[targetTab].title;
                pageSubtitle.innerText = tabMeta[targetTab].subtitle;
            }
            
            // Força redimensionamento do gráfico para evitar distorção
            if (targetTab === 'dashboard') {
                setTimeout(() => {
                    if (chartDistributionInstance) chartDistributionInstance.resize();
                    if (chartExpensesInstance) chartExpensesInstance.resize();
                }, 50);
            }
        });
    });
}

// Configura Listeners de Botões
function setupEventListeners() {
    // Botão Salvar Agora (Header)
    const btnSaveNow = document.getElementById("btn-save-now");
    if (btnSaveNow) {
        btnSaveNow.addEventListener("click", () => {
            triggerSaveToPython();
            showNotification("Sucesso", "Todas as alterações foram salvas localmente!", "success");
        });
    }

    // Botão Alterar Caminho do Banco (Configurações)
    const btnChangePath = document.getElementById("btn-change-database-path");
    if (btnChangePath) {
        btnChangePath.addEventListener("click", () => {
            console.log("CHOOSE_PATH:REQUESTED");
        });
    }
    
    // Botão Restaurar Caminho Padrão
    const btnResetPath = document.getElementById("btn-reset-default-path");
    if (btnResetPath) {
        btnResetPath.addEventListener("click", () => {
            state.settings.databasePath = "dados_financeiros.json";
            document.getElementById("input-database-path").value = state.settings.databasePath;
            triggerSaveToPython();
            showNotification("Restaurado", "Caminho restaurado para o padrão local.", "success");
        });
    }

    // Input do Repositório GitHub
    const inputOwner = document.getElementById("github-owner");
    const inputRepo = document.getElementById("github-repo");
    
    const updateGitHubSettings = () => {
        state.settings.githubOwner = inputOwner.value || "RobsonSilva31";
        state.settings.githubRepo = inputRepo.value || "gestor-financeiro";
        triggerSaveToPython();
    };

    if (inputOwner) inputOwner.addEventListener("change", updateGitHubSettings);
    if (inputRepo) inputRepo.addEventListener("change", updateGitHubSettings);
}

// Inicializar dados de demonstração vazios
function initDefaultData() {
    if (state.salaries.length === 0) {
        state.salaries = [{ id: "sal_1", description: "Salário Principal", value: 5000 }];
    }
    if (state.fixedExpenses.length === 0) {
        state.fixedExpenses = [
            { id: "fix_1", description: "Aluguel / Financiamento", value: 1500 },
            { id: "fix_2", description: "Internet e TV", value: 150 }
        ];
    }
    if (state.variableExpenses.length === 0) {
        state.variableExpenses = [
            { id: "var_1", description: "Alimentação / Mercado", value: 800 }
        ];
    }
}

// --------------------------------------------------------------------------
// RENDERIZAÇÃO DE TABELAS DINÂMICAS
// --------------------------------------------------------------------------

// Adiciona uma linha vazia a um tipo de categoria e foca nela
function addEntryRow(category) {
    const prefixMap = {
        salaries: 'sal_',
        extraIncome: 'ext_',
        savedIncome: 'sav_',
        fixedExpenses: 'fix_',
        variableExpenses: 'var_',
        unexpectedExpenses: 'unp_',
        investments: 'inv_'
    };
    
    const newId = prefixMap[category] + Date.now();
    state[category].push({
        id: newId,
        description: "",
        value: 0
    });
    
    renderTable(category);
    recalculateAll(true);
    
    // Foca no primeiro input da linha adicionada
    setTimeout(() => {
        const row = document.getElementById(newId);
        if (row) {
            const firstInput = row.querySelector("input");
            if (firstInput) firstInput.focus();
        }
    }, 50);
}

// Remove uma linha específica
function deleteRow(category, id) {
    state[category] = state[category].filter(item => item.id !== id);
    renderTable(category);
    recalculateAll(true);
}

// Atualiza o valor digitado diretamente no estado
function updateStateValue(category, id, field, value) {
    const item = state[category].find(x => x.id === id);
    if (item) {
        if (field === 'value') {
            item.value = parseFloat(value) || 0;
        } else {
            item.description = value;
        }
        recalculateAll(true); // Recalcula totais em tempo real ao digitar
    }
}

// Renderiza uma tabela específica
function renderTable(category) {
    const tbody = document.querySelector(`#table-${category} tbody`);
    if (!tbody) return;
    
    tbody.innerHTML = "";
    
    if (state[category].length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" style="text-align: center; color: var(--text-disabled); padding: 16px; font-size: 13px;">
                    Nenhum lançamento adicionado. Clique no botão acima para adicionar.
                </td>
            </tr>
        `;
        return;
    }
    
    state[category].forEach(item => {
        const tr = document.createElement("tr");
        tr.id = item.id;
        
        tr.innerHTML = `
            <td>
                <input type="text" class="table-input" 
                       value="${item.description}" 
                       list="list-${category}"
                       placeholder="Descrição (ex: ${getPlaceholderText(category)})"
                       oninput="updateStateValue('${category}', '${item.id}', 'description', this.value)">
            </td>
            <td>
                <div class="value-cell">
                    <span class="currency-prefix">R$</span>
                    <input type="text" class="table-input table-value-input" 
                           value="${formatNumberBRL(item.value)}" 
                           placeholder="0,00"
                           onfocus="onValueFocus(this)"
                           oninput="maskNumberBRL(this, '${category}', '${item.id}')"
                           onblur="onValueBlur(this, '${category}', '${item.id}')"
                           onkeydown="if(event.key === 'Enter') this.blur()">
                </div>
            </td>
            <td style="text-align: center;">
                <button class="btn-delete" onclick="deleteRow('${category}', '${item.id}')" title="Excluir Lançamento">
                    <i data-lucide="trash-2"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    // Recarregar os ícones recém-criados na tabela
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({
            attrs: { class: 'lucide' },
            nameAttr: 'data-lucide',
            nodeList: tbody.querySelectorAll('[data-lucide]')
        });
    }
}

// Renderiza todas as tabelas
function renderAllTables() {
    const categories = ['salaries', 'extraIncome', 'savedIncome', 'fixedExpenses', 'variableExpenses', 'unexpectedExpenses', 'investments'];
    categories.forEach(renderTable);
}

// Retorna placeholders intuitivos
function getPlaceholderText(category) {
    const placeholders = {
        salaries: "Salário CLT, Pro-labore",
        extraIncome: "Venda de produto, Freelance",
        savedIncome: "Dinheiro guardado da poupança",
        fixedExpenses: "Aluguel, Condomínio, Energia",
        variableExpenses: "Mercado, Combustível, Lazer",
        unexpectedExpenses: "Mecânico, Farmácia, Presentes",
        investments: "CDB 100% CDI, Ações, FIIs"
    };
    return placeholders[category] || "";
}

// --------------------------------------------------------------------------
// CÁLCULOS E GRÁFICOS
// --------------------------------------------------------------------------

// Executa todos os cálculos e atualiza a interface + gráficos
function recalculateAll(shouldAutoSave = true) {
    // 1. Somar Categorias
    const sum = arr => arr.reduce((acc, curr) => acc + (curr.value || 0), 0);
    
    const totalSalaries = sum(state.salaries);
    const totalExtra = sum(state.extraIncome);
    const totalSaved = sum(state.savedIncome);
    
    const totalIncome = totalSalaries + totalExtra; // Receitas recorrentes do mês
    const totalRevenue = totalIncome + totalSaved; // Receitas totais incluindo economias guardadas
    
    const totalFixed = sum(state.fixedExpenses);
    const totalVariable = sum(state.variableExpenses);
    const totalUnexpected = sum(state.unexpectedExpenses);
    const totalExpenses = totalFixed + totalVariable + totalUnexpected;
    
    const totalInvestments = sum(state.investments);
    
    // Saldo Líquido
    const netTotal = totalIncome - totalExpenses;
    
    // 2. Atualizar Cards da Dashboard
    document.getElementById("dash-total-income").innerText = formatCurrency(totalIncome);
    document.getElementById("dash-salary-count").innerText = `${state.salaries.length} salário(s) / ${state.extraIncome.length} renda(s) extra`;
    
    document.getElementById("dash-total-expenses").innerText = formatCurrency(totalExpenses);
    const expenseRatio = totalIncome > 0 ? ((totalExpenses / totalIncome) * 100).toFixed(0) : 0;
    document.getElementById("dash-expense-ratio").innerText = `${expenseRatio}% da renda mensal`;
    
    document.getElementById("dash-net-total").innerText = formatCurrency(netTotal);
    const netStatus = document.getElementById("dash-net-status");
    if (netTotal > 0) {
        netStatus.className = "text-success";
        netStatus.innerHTML = `<i data-lucide="trending-up" style="display:inline-block;width:12px;height:12px;vertical-align:middle;margin-right:4px;"></i>Sobrando no caixa`;
    } else if (netTotal < 0) {
        netStatus.className = "text-danger";
        netStatus.innerHTML = `<i data-lucide="trending-down" style="display:inline-block;width:12px;height:12px;vertical-align:middle;margin-right:4px;"></i>Orçamento no vermelho`;
    } else {
        netStatus.className = "text-muted";
        netStatus.innerText = "Balanço zerado";
    }
    
    document.getElementById("dash-total-invested").innerText = formatCurrency(totalInvestments);
    const investRatio = totalIncome > 0 ? ((totalInvestments / totalIncome) * 100).toFixed(0) : 0;
    document.getElementById("dash-invest-ratio").innerText = `${investRatio}% da renda mensal`;
    
    // Recriar ícone do Lucide no netStatus se necessário
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({ nodeList: [netStatus] });
    }

    // 3. Atualizar Alertas e Dicas
    updateDashboardAlerts(totalIncome, totalFixed, totalVariable, totalUnexpected, totalInvestments, netTotal);
    updateDetailedInsights(totalIncome, totalFixed, totalVariable, totalUnexpected, totalInvestments, netTotal, totalSaved);
    
    // 4. Desenhar / Atualizar Gráficos
    updateCharts(totalFixed, totalVariable, totalUnexpected, totalInvestments, Math.max(0, netTotal), totalIncome);
    
    // 5. Salvar no Python se configurado (Auto-save de 1.5s debounced para evitar gargalo de I/O de escrita em disco)
    if (shouldAutoSave) {
        debounceSave();
    }
}

// Formatação BRL
function formatCurrency(val) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val).replace(/\s/g, ' ');
}

// Debounce para salvamento
let saveTimeout = null;
function debounceSave() {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
        triggerSaveToPython();
    }, 1500);
}

function triggerSaveToPython() {
    console.log("SAVE_DATA:" + JSON.stringify(state));
}

// --------------------------------------------------------------------------
// ALGORITMO DE DICAS E ALERTAS
// --------------------------------------------------------------------------

// Atualiza alertas rápidos na aba Dashboard
function updateDashboardAlerts(income, fixed, variable, unexpected, invested, net) {
    const alertsContainer = document.getElementById("dash-quick-alerts");
    if (!alertsContainer) return;
    
    let alerts = [];
    
    if (net < 0) {
        alerts.push({
            type: "danger",
            title: "Atenção: Saldo Negativo",
            desc: `Você gastou ${formatCurrency(Math.abs(net))} a mais do que sua receita recorrente este mês.`,
            icon: "alert-octagon"
        });
    }
    
    const fixedPct = income > 0 ? (fixed / income) * 100 : 0;
    if (fixedPct > 50) {
        alerts.push({
            type: "warning",
            title: "Gastos Fixos Altos",
            desc: `Custos fixos estão em ${fixedPct.toFixed(0)}% da renda (meta sugerida: 50%).`,
            icon: "alert-triangle"
        });
    }

    const varPct = income > 0 ? (variable / income) * 100 : 0;
    if (varPct > 35) {
        alerts.push({
            type: "warning",
            title: "Gastos Variáveis Elevados",
            desc: `Despesas flexíveis consomem ${varPct.toFixed(0)}% do seu orçamento.`,
            icon: "shopping-bag"
        });
    }
    
    if (income > 0 && invested === 0 && net > 0) {
        alerts.push({
            type: "info",
            title: "Oportunidade de Poupar",
            desc: "Você possui saldo livre em conta. Considere investir parte desse valor.",
            icon: "coins"
        });
    }
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = `
            <div class="alert-empty-state">
                <i data-lucide="check-circle-2" style="color: var(--color-primary)"></i>
                <p>Tudo sob controle! Suas despesas estão em conformidade e o saldo está saudável.</p>
            </div>
        `;
    } else {
        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.type}">
                <i data-lucide="${alert.icon}"></i>
                <div>
                    <strong>${alert.title}</strong>
                    <p style="margin-top: 2px; opacity: 0.95; font-size: 12px;">${alert.desc}</p>
                </div>
            </div>
        `).join("");
    }
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({ nodeList: alertsContainer.querySelectorAll('[data-lucide]') });
    }
}

// Atualiza a aba Dicas & Insights (incluindo regra 50/30/20)
function updateDetailedInsights(income, fixed, variable, unexpected, invested, net, saved) {
    const fixedPct = income > 0 ? (fixed / income) * 100 : 0;
    const varAndUnpPct = income > 0 ? ((variable + unexpected) / income) * 100 : 0;
    const invAndSavPct = income > 0 ? ((invested + saved) / income) * 100 : 0;
    
    // Atualiza valores textuais
    document.getElementById("rule-fixed-pct").innerText = `${fixedPct.toFixed(0)}%`;
    document.getElementById("rule-var-pct").innerText = `${varAndUnpPct.toFixed(0)}%`;
    document.getElementById("rule-inv-pct").innerText = `${invAndSavPct.toFixed(0)}%`;
    
    // Feedbacks individuais das metas
    const updateFeedbackBadge = (id, pct, max, isMin = false) => {
        const badge = document.getElementById(id);
        if (!badge) return;
        
        if (income === 0) {
            badge.innerText = "Sem Receita";
            badge.className = "feedback-badge warning";
            return;
        }
        
        if (isMin) {
            if (pct >= max) {
                badge.innerText = "Excelente";
                badge.className = "feedback-badge success";
            } else if (pct >= max * 0.5) {
                badge.innerText = "Regular";
                badge.className = "feedback-badge warning";
            } else {
                badge.innerText = "Insuficiente";
                badge.className = "feedback-badge danger";
            }
        } else {
            if (pct <= max) {
                badge.innerText = "Dentro do Limite";
                badge.className = "feedback-badge success";
            } else if (pct <= max * 1.2) {
                badge.innerText = "Atenção";
                badge.className = "feedback-badge warning";
            } else {
                badge.innerText = "Crítico";
                badge.className = "feedback-badge danger";
            }
        }
    };
    
    updateFeedbackBadge("rule-fixed-feedback", fixedPct, 50);
    updateFeedbackBadge("rule-var-feedback", varAndUnpPct, 30);
    updateFeedbackBadge("rule-inv-feedback", invAndSavPct, 20, true);
    
    // Atualiza barra de progresso visual
    const progressBar = document.getElementById("rule-progress-bar");
    if (progressBar) {
        // Normaliza as porcentagens se somarem mais de 100% para manter visual limpo
        const totalPct = fixedPct + varAndUnpPct + invAndSavPct;
        let scale = 1;
        if (totalPct > 100) {
            scale = 100 / totalPct;
        }
        
        const fWidth = Math.max(10, fixedPct * scale);
        const vWidth = Math.max(10, varAndUnpPct * scale);
        const iWidth = Math.max(10, invAndSavPct * scale);
        
        progressBar.innerHTML = `
            <div class="progress-segment needs" style="width: ${fWidth}%;">Fixos (${fixedPct.toFixed(0)}%)</div>
            <div class="progress-segment wants" style="width: ${vWidth}%;">Var./Imp. (${varAndUnpPct.toFixed(0)}%)</div>
            <div class="progress-segment savings" style="width: ${iWidth}%;">Invest./Res. (${invAndSavPct.toFixed(0)}%)</div>
        `;
    }
    
    // Gera lista detalhada de dicas customizadas
    const tipsList = document.getElementById("tips-detailed-list");
    if (!tipsList) return;
    
    let tips = [];
    
    // Dica sobre custos fixos
    if (fixedPct > 50) {
        // Encontrar maior custo fixo para dar dica específica
        const maxFixed = state.fixedExpenses.reduce((max, x) => x.value > max.value ? x : max, { value: 0, description: "" });
        const specText = maxFixed.value > 0 ? ` O lançamento "${maxFixed.description}" de ${formatCurrency(maxFixed.value)} é o seu maior custo fixo.` : "";
        tips.push({
            type: "warning",
            title: "Como reduzir suas despesas fixas (Necessidades)",
            desc: `Seus gastos fixos correspondem a ${fixedPct.toFixed(0)}% da sua renda.${specText} Para diminuir essa parcela, analise assinaturas que não usa mais, tente renegociar planos de internet/celular e corte pequenos vazamentos como anuidades bancárias e de cartões.`,
            icon: "home"
        });
    } else if (fixedPct > 0) {
        tips.push({
            type: "success",
            title: "Despesas fixas sob controle",
            desc: `Parabéns! Seus custos fixos estão em ${fixedPct.toFixed(0)}% da renda mensal, proporcionando segurança para os demais gastos.`,
            icon: "check"
        });
    }

    // Dica sobre custos variáveis
    if (varAndUnpPct > 30) {
        const maxVar = [...state.variableExpenses, ...state.unexpectedExpenses].reduce((max, x) => x.value > max.value ? x : max, { value: 0, description: "" });
        const specText = maxVar.value > 0 ? ` (Destaque para "${maxVar.description}" custando ${formatCurrency(maxVar.value)}).` : "";
        tips.push({
            type: "danger",
            title: "Alerta de Despesas Variáveis e Imprevistas (Desejos)",
            desc: `Seus gastos variáveis somados aos imprevistos somam ${varAndUnpPct.toFixed(0)}% dos seus ganhos (limite recomendado: 30%).${specText} Defina metas específicas por categorias no mês (ex: estipular limite para restaurantes e compras online) e monitore o acumulado semanalmente.`,
            icon: "shopping-cart"
        });
    } else if (varAndUnpPct > 0) {
        tips.push({
            type: "success",
            title: "Despesas variáveis controladas",
            desc: `Seu estilo de vida e lazer está equilibrado com o seu bolso, gastando ${varAndUnpPct.toFixed(0)}% da renda.`,
            icon: "smile"
        });
    }

    // Dica sobre investimentos
    if (invAndSavPct < 20) {
        tips.push({
            type: "info",
            title: "Acelere seu futuro financeiro",
            desc: `Você está poupando/investindo ${invAndSavPct.toFixed(0)}% dos seus proventos (meta recomendada: mínima de 20%). Para atingir isso com facilidade, tente automatizar suas aplicações no início do mês: assim que receber seu salário, já transfira os 20% diretamente para a corretora ou reserva.`,
            icon: "trending-up"
        });
    } else {
        tips.push({
            type: "success",
            title: "Investidor focado no futuro!",
            desc: `Você está aplicando ${invAndSavPct.toFixed(0)}% dos seus rendimentos. Esse hábito reduz drasticamente o tempo necessário para alcançar a independência financeira.`,
            icon: "award"
        });
    }
    
    if (tips.length === 0) {
        tipsList.innerHTML = `
            <div class="tip-card info">
                <div class="tip-card-icon"><i data-lucide="help-circle"></i></div>
                <div class="tip-card-content">
                    <h4>Preencha as tabelas de dados</h4>
                    <p>Adicione seus salários e despesas fixas ou variáveis nas abas correspondentes para ver suas dicas personalizadas aqui.</p>
                </div>
            </div>
        `;
    } else {
        tipsList.innerHTML = tips.map(tip => `
            <div class="tip-card ${tip.type}">
                <div class="tip-card-icon"><i data-lucide="${tip.icon}"></i></div>
                <div class="tip-card-content">
                    <h4>${tip.title}</h4>
                    <p>${tip.desc}</p>
                </div>
            </div>
        `).join("");
    }
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({ nodeList: tipsList.querySelectorAll('[data-lucide]') });
    }
}

// --------------------------------------------------------------------------
// ATUALIZAÇÃO DOS GRÁFICOS (CHART.JS)
// --------------------------------------------------------------------------
function updateCharts(fixed, variable, unexpected, invested, leftover, income) {
    // 1. Gráfico de Rosca (Distribuição de Recursos)
    const distCanvas = document.getElementById("chartDistribution");
    if (distCanvas) {
        const dataValues = [fixed, variable, unexpected, invested, leftover];
        const dataLabels = ['Fixas', 'Variáveis', 'Imprevistos', 'Investimentos', 'Saldo Sobrando'];
        
        // Remove valores zerados para o gráfico ficar limpo
        const filteredLabels = [];
        const filteredData = [];
        const colors = ['#ef4444', '#f59e0b', '#ec4899', '#3b82f6', '#10b981'];
        const filteredColors = [];
        
        dataValues.forEach((val, i) => {
            if (val > 0) {
                filteredData.push(val);
                filteredLabels.push(dataLabels[i]);
                filteredColors.push(colors[i]);
            }
        });
        
        if (chartDistributionInstance) {
            chartDistributionInstance.data.labels = filteredLabels;
            chartDistributionInstance.data.datasets[0].data = filteredData;
            chartDistributionInstance.data.datasets[0].backgroundColor = filteredColors;
            chartDistributionInstance.update();
        } else {
            chartDistributionInstance = new Chart(distCanvas, {
                type: 'doughnut',
                data: {
                    labels: filteredLabels,
                    datasets: [{
                        data: filteredData,
                        backgroundColor: filteredColors,
                        borderWidth: 1,
                        borderColor: '#0f1218'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#9ca3af',
                                font: { family: 'Outfit', size: 11 },
                                boxWidth: 12
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.label}: ${formatCurrency(context.parsed)}`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }
    }
    
    // 2. Gráfico de Barras Comparativo (Receitas vs Despesas vs Investido)
    const expCanvas = document.getElementById("chartExpenses");
    if (expCanvas) {
        const totalExp = fixed + variable + unexpected;
        
        if (chartExpensesInstance) {
            chartExpensesInstance.data.datasets[0].data = [income, totalExp, invested];
            chartExpensesInstance.update();
        } else {
            chartExpensesInstance = new Chart(expCanvas, {
                type: 'bar',
                data: {
                    labels: ['Receita Total', 'Gastos Totais', 'Investimentos'],
                    datasets: [{
                        data: [income, totalExp, invested],
                        backgroundColor: ['#10b981', '#ef4444', '#3b82f6'],
                        borderRadius: 6,
                        borderWidth: 0,
                        maxBarThickness: 45
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            grid: { color: 'rgba(255,255,255,0.04)' },
                            ticks: {
                                color: '#9ca3af',
                                font: { family: 'Outfit', size: 10 },
                                callback: function(value) {
                                    return value >= 1000 ? 'R$ ' + (value/1000) + 'k' : 'R$ ' + value;
                                }
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: '#9ca3af',
                                font: { family: 'Outfit', size: 11 }
                            }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return ` ${formatCurrency(context.parsed.y || context.raw)}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

// --------------------------------------------------------------------------
// COMUNICAÇÃO COM O PYTHON (LOAD & SAVE)
// --------------------------------------------------------------------------

// Chamado pelo Python para alimentar o aplicativo com dados recuperados do arquivo
window.loadDataFromPython = function(jsonDataString) {
    try {
        const parsed = JSON.parse(jsonDataString);
        
        // Preencher estado garantindo retrocompatibilidade
        if (parsed.salaries) state.salaries = parsed.salaries;
        if (parsed.extraIncome) state.extraIncome = parsed.extraIncome;
        if (parsed.savedIncome) state.savedIncome = parsed.savedIncome;
        if (parsed.fixedExpenses) state.fixedExpenses = parsed.fixedExpenses;
        if (parsed.variableExpenses) state.variableExpenses = parsed.variableExpenses;
        if (parsed.unexpectedExpenses) state.unexpectedExpenses = parsed.unexpectedExpenses;
        if (parsed.investments) state.investments = parsed.investments;
        if (parsed.settings) {
            state.settings = { ...state.settings, ...parsed.settings };
        }
        
        // Assegurar e carregar sugestões salvas ou padrão
        ensureDefaultSuggestions();
        populateDatalists();
        fillSuggestionsInputs();
        
        // Atualizar campos de configurações visualmente
        const inputPath = document.getElementById("input-database-path");
        if (inputPath) inputPath.value = state.settings.databasePath;
        
        const inputOwner = document.getElementById("github-owner");
        const inputRepo = document.getElementById("github-repo");
        if (inputOwner) inputOwner.value = state.settings.githubOwner || "RobsonSilva31";
        if (inputRepo) inputRepo.value = state.settings.githubRepo || "gestor-financeiro";
        
        // Atualizar tag visual de sincronização
        updateSyncLabel();

        // Renderizar novamente todas as abas
        renderAllTables();
        recalculateAll(false); // Recalcular sem salvar de volta no Python para não dar loop
        
        showNotification("Carregado", "Os lançamentos do arquivo foram atualizados com sucesso!", "info");
    } catch (e) {
        console.error("Erro ao analisar dados carregados: " + e);
        showNotification("Erro de Carga", "Houve um problema ao carregar o arquivo financeiro.", "danger");
    }
};

// Notificar alteração de caminho do banco (feita pela UI)
window.updateDatabasePathFromPython = function(newPath) {
    if (newPath) {
        state.settings.databasePath = newPath;
        const inputPath = document.getElementById("input-database-path");
        if (inputPath) inputPath.value = newPath;
        
        updateSyncLabel();
        
        // Salva com o novo caminho
        triggerSaveToPython();
        
        showNotification("Banco Conectado", `Sincronizando com: ${newPath}`, "success");
    }
};

// Atualiza etiqueta de sincronização na barra inferior
function updateSyncLabel() {
    const syncLabel = document.getElementById("sync-label");
    const syncIcon = document.getElementById("sync-icon");
    
    if (state.settings.databasePath && state.settings.databasePath !== "dados_financeiros.json") {
        syncLabel.innerText = "Sincronizado na Nuvem";
        syncIcon.setAttribute("data-lucide", "cloud-lightning");
        syncIcon.style.color = "#3b82f6";
    } else {
        syncLabel.innerText = "Dados Locais";
        syncIcon.setAttribute("data-lucide", "cloud-check");
        syncIcon.style.color = "#22c55e";
    }
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({ nodeList: [syncIcon] });
    }
}

// --------------------------------------------------------------------------
// UI FEEDBACKS (NOTIFICAÇÕES FLUTUANTES)
// --------------------------------------------------------------------------
function showNotification(title, message, type = "success") {
    // Cria elemento de notificação se não existir
    let container = document.getElementById("notification-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "notification-container";
        container.style.position = "fixed";
        container.style.bottom = "20px";
        container.style.right = "20px";
        container.style.zIndex = "9999";
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.gap = "10px";
        document.body.appendChild(container);
    }
    
    const notification = document.createElement("div");
    notification.className = `alert-item ${type}`;
    notification.style.width = "300px";
    notification.style.boxShadow = "0 8px 16px rgba(0,0,0,0.4)";
    notification.style.borderRadius = "8px";
    notification.style.border = "1px solid rgba(255,255,255,0.1)";
    notification.style.backdropFilter = "blur(8px)";
    notification.style.animation = "slideIn 0.3s ease";
    
    const icons = {
        success: "check-circle",
        info: "info",
        warning: "alert-triangle",
        danger: "alert-octagon"
    };
    
    notification.innerHTML = `
        <i data-lucide="${icons[type] || 'check'}"></i>
        <div style="flex-grow:1;">
            <strong style="display:block;font-size:13px;margin-bottom:2px;">${title}</strong>
            <span style="font-size:12px;opacity:0.85;line-height:1.4;">${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({ nodeList: [notification] });
    }
    
    // Remover após 3.5 segundos
    setTimeout(() => {
        notification.style.animation = "fadeOut 0.3s ease";
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3500);
}

document.head.appendChild(animStyle);

// --------------------------------------------------------------------------
// SUGESTÕES DE AUTOCOMPLETE E FORMATAÇÃO DE ENTRADA
// --------------------------------------------------------------------------

// Garante que a estrutura padrão de sugestões exista nas configurações
function ensureDefaultSuggestions() {
    if (!state.settings) {
        state.settings = {};
    }
    if (!state.settings.suggestions) {
        state.settings.suggestions = {
            salaries: ["Salário Principal", "Salário Cônjuge", "Pró-labore"],
            extraIncome: ["Freelance", "Venda de Produto", "Rendimento", "Reembolso"],
            savedIncome: ["Reserva de Emergência", "Poupança de Emergência", "Caixa de Segurança"],
            fixedExpenses: ["Aluguel / Financiamento", "Condomínio", "Energia Elétrica", "Água e Esgoto", "Internet e TV", "Plano de Saúde", "Escola / Faculdade"],
            variableExpenses: ["Supermercado / Feira", "Combustível / Uber", "Restaurantes / Delivery", "Lazer / Cinema", "Roupas e Calçados", "Assinaturas (Netflix, Spotify)"],
            unexpectedExpenses: ["Mecânico / Oficina", "Farmácia / Médico", "Conserto Doméstico", "Presentes", "Impostos Anuais (IPVA/IPTU)"],
            investments: ["CDB 100% CDI", "Ações (B3)", "Fundos Imobiliários (FIIs)", "Tesouro Direto", "Poupança", "Criptomoedas"]
        };
    }
}

// Preenche os datalists HTML com as sugestões salvas nas configurações
function populateDatalists() {
    const categories = ['salaries', 'extraIncome', 'savedIncome', 'fixedExpenses', 'variableExpenses', 'unexpectedExpenses', 'investments'];
    categories.forEach(category => {
        const datalist = document.getElementById(`list-${category}`);
        if (datalist) {
            datalist.innerHTML = "";
            const items = state.settings.suggestions[category] || [];
            items.forEach(val => {
                const option = document.createElement("option");
                option.value = val;
                datalist.appendChild(option);
            });
        }
    });
}

// Preenche os campos de texto das configurações com os CSVs das sugestões
function fillSuggestionsInputs() {
    const categories = ['salaries', 'extraIncome', 'savedIncome', 'fixedExpenses', 'variableExpenses', 'unexpectedExpenses', 'investments'];
    categories.forEach(category => {
        const input = document.getElementById(`suggest-${category}`);
        if (input && state.settings.suggestions[category]) {
            input.value = state.settings.suggestions[category].join(', ');
        }
    });
}

// Manipulador acionado quando as sugestões são editadas pelo usuário na aba de configurações
window.updateCustomSuggestions = function(category, csvValue) {
    const list = csvValue.split(',')
                          .map(x => x.trim())
                          .filter(x => x !== "");
    
    state.settings.suggestions[category] = list;
    populateDatalists();
    triggerSaveToPython();
    showNotification("Sugestões Salvas", `Menu de sugestões atualizado!`, "success");
};

// Função auxiliar de formatação numérica pura (ex: 1.500,00)
function formatNumberBRL(val) {
    return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val);
}

// Funções para controle de Input com Máscara Monetária R$ em Tempo Real
window.onValueFocus = function(input) {
    // Ao focar, coloca o cursor antes do separador se houver decimais vazios (,00) para facilitar a digitação
    setTimeout(() => {
        let val = input.value;
        if (val.endsWith(",00")) {
            let idx = val.indexOf(",");
            input.setSelectionRange(idx, idx);
        } else {
            let len = val.length;
            input.setSelectionRange(len, len);
        }
    }, 10);
};

window.maskNumberBRL = function(input, category, id) {
    let val = input.value;
    
    // Remove tudo que não for dígito, vírgula ou ponto
    let cleanVal = val.replace(/[^0-9,.]/g, "");
    
    // Se estiver vazio, zera o valor no estado e atualiza
    if (!cleanVal) {
        const item = state[category].find(x => x.id === id);
        if (item) {
            item.value = 0;
            recalculateAll(true);
        }
        return;
    }
    
    // Divide parte inteira e decimal por vírgula ou ponto
    let hasSeparator = cleanVal.includes(',') || cleanVal.includes('.');
    let parts = cleanVal.split(/[,.]/);
    
    // Parte inteira: remove não dígitos
    let integerPart = parts[0].replace(/\D/g, "");
    
    // Parte decimal: remove não dígitos e limita a 2 casas
    let decimalPart = parts.length > 1 ? parts[1].replace(/\D/g, "").substring(0, 2) : "";
    
    // Formata parte inteira com pontos de milhar pt-BR
    let formattedInt = integerPart ? parseInt(integerPart, 10).toLocaleString('pt-BR') : "0";
    
    // Reconstrói a string formatada em tempo real (sem forçar o ,00 se o usuário ainda não digitou a vírgula)
    let formattedValue = formattedInt;
    if (hasSeparator) {
        formattedValue += "," + decimalPart;
    }
    
    // Define o valor visual no input
    input.value = formattedValue;
    
    // Salva o valor decimal equivalente no estado
    let finalNumString = (integerPart || "0") + "." + (decimalPart.padEnd(2, "0"));
    let numericValue = parseFloat(finalNumString) || 0;
    
    // Atualiza o estado
    const item = state[category].find(x => x.id === id);
    if (item) {
        item.value = numericValue;
        recalculateAll(true); // Atualiza totais e gráficos em tempo real
    }
};

window.onValueBlur = function(input, category, id) {
    const item = state[category].find(x => x.id === id);
    if (item) {
        // Formata completamente no blur (ex: adiciona o ,00 se faltar)
        input.value = formatNumberBRL(item.value);
    }
};
