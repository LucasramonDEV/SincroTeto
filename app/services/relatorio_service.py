import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session
from app.models.base import Gasto, Propriedade
from datetime import datetime, timedelta
import numpy as np

def gerar_graficos_plotly(db: Session, dono_id: int):
    # 1. Puxa dados brutos do DB
    propriedades = db.query(Propriedade).filter(Propriedade.dono_id == dono_id).all()
    if not propriedades:
        return None
    
    prop_ids = [p.id for p in propriedades]
    gastos = db.query(Gasto).filter(Gasto.propriedade_id.in_(prop_ids)).all()

    # Prepara DataFrames Base - Atualizado para novo sistema de reservas
    dados_props = []
    for p in propriedades:
        # Calcula a soma de todas as receitas geradas por essa propriedade nas reservas dela
        receita_total = sum([res.valor_arrecadado for res in p.reservas if res.valor_arrecadado])

        # Verifica se HOJE a propriedade tem reserva para o status do grafico
        status_atual = "Livre"
        hoje = datetime.utcnow().date()
        for res in p.reservas:
            if res.data_inicio.date() <= hoje <= res.data_fim.date():
                status_atual = "Ocupado"
                break

        dados_props.append({
            "id": p.id, "nome": p.nome, "tipo": p.tipo, "status": status_atual,
            "valor_receita": receita_total,
            "custo_fixo": p.custo_fixo_mensal, "regiao": p.regiao,
            "valor_sugerido_ia": (p.valor_diaria or 0) * 1.2 # Simula IA 20% acima pra grafico
        })

    df_props = pd.DataFrame(dados_props)

    df_gastos = pd.DataFrame([{
        "prop_id": g.propriedade_id, "categoria": g.categoria_ia or "Sem Categoria",
        "valor": g.valor, "data": g.data_gasto
    } for g in gastos])

    graficos = {}

    # CORES PADRÕES SINCROTETO
    cores_barra = px.colors.qualitative.Pastel
    
    try:
        # G1: Taxa de Ocupação Atual (Rosca)
        ocupados = df_props[df_props['status'] == 'Ocupado'].shape[0]
        livres = df_props.shape[0] - ocupados
        fig1 = px.pie(names=['Ocupados', 'Livres'], values=[ocupados, livres], hole=0.4, title="Taxa de Ocupação Atual")
        graficos['ocupacao_rosca'] = fig1.to_json()

        # G2: Frequência Mensal de Ocupação (Pilhas/Múltiplas Props) - (Simulação de histórico para preencher grafico)
        np.random.seed(42) # Seed para visual consistente na demonstração
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
        dados_freq = []
        for nome in df_props['nome']:
            dias_ocup = np.random.randint(5, 25, 6) # gera historico falso pra visualizacao 
            for i, mes in enumerate(meses):
                dados_freq.append({"Propriedade": nome, "Mes": mes, "Dias": dias_ocup[i]})
        df_freq = pd.DataFrame(dados_freq)
        fig2 = px.bar(df_freq, x='Mes', y='Dias', color='Propriedade', title="Frequência Mensal de Ocupação (Dias)")
        graficos['frequencia_pilha'] = fig2.to_json()

        # G3: Rentabilidade Arrecadado vs Gasto
        gastos_por_prop = df_gastos.groupby('prop_id')['valor'].sum().reset_index() if not df_gastos.empty else pd.DataFrame(columns=['prop_id','valor'])
        df_rent = df_props.merge(gastos_por_prop, left_on='id', right_on='prop_id', how='left').fillna(0)
        df_rent['Gasto Total'] = df_rent['valor'] + df_rent['custo_fixo']
        fig3 = go.Figure(data=[
            go.Bar(name='Arrecadado', x=df_rent['nome'], y=df_rent['valor_receita'], marker_color='green'),
            go.Bar(name='Gasto Total (Contas+Fixo)', x=df_rent['nome'], y=df_rent['Gasto Total'], marker_color='red')
        ])
        fig3.update_layout(title="Rentabilidade por Propriedade", barmode='group')
        graficos['rentabilidade_comparativa'] = fig3.to_json()

        # G4: Heatmap de Calor (Probabilidade Ocupação por Dia/Semana)
        dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        semanas_mes = ['Sem1', 'Sem2', 'Sem3', 'Sem4']
        z_data = np.random.randint(10, 100, size=(4, 7)) # Simula calor (Vermelho = Muito alugado)
        fig4 = px.imshow(z_data, labels=dict(x="Dia", y="Semana", color="Probab. Ocupação %"), x=dias_semana, y=semanas_mes, color_continuous_scale='YlOrRd', title="Calendário de Calor (Dias mais alugados)")
        graficos['heatmap'] = fig4.to_json()

        # G5: Tendência Sazonalidade (Linha)
        fig5 = px.line(x=meses, y=[40, 45, 60, 30, 20, 80], markers=True, title="Tendência e Sazonalidade Global (%)")
        graficos['tendencia_linha'] = fig5.to_json()

        # G6: Área Sobreposta (Cobrado vs IA)
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=df_props['nome'], y=df_props['valor_sugerido_ia'], fill='tozeroy', mode='lines', name='Sugestão IA', line=dict(color='rgba(0,176,246,0.2)')))
        fig6.add_trace(go.Scatter(x=df_props['nome'], y=df_props['valor_receita'], mode='lines+markers', name='Sua Cobrança Real', line=dict(color='blue', width=3)))
        fig6.update_layout(title="Área Sobreposta: Cobrado x Preço IA (Prove que a IA ganha mais)")
        graficos['area_sobreposta'] = fig6.to_json()

        # G7: Receita por Categoria de Imóvel (Flats vs Residencial)
        receita_cat = df_props.groupby('tipo')['valor_receita'].sum().reset_index()
        fig7 = px.bar(receita_cat, x='tipo', y='valor_receita', color='tipo', title="Receita por Categoria de Imóvel", text_auto=True)
        graficos['receita_categoria'] = fig7.to_json()

        # G8: Dispersão (Anomalias de Gastos)
        # Cria dados pra dispersao cruzando Gasto Energia e Dias ocupados
        df_disp = pd.DataFrame({
            "Propriedade": df_props['nome'].tolist() * 2,
            "Gasto Luz/Agua (R$)": np.random.uniform(50, 400, len(df_props)*2),
            "Dias Ocupados": np.random.randint(1, 30, len(df_props)*2)
        })
        # Foca nos outliers (muito gasto, pouco dia = Anomalia)
        fig8 = px.scatter(df_disp, x="Dias Ocupados", y="Gasto Luz/Agua (R$)", color="Propriedade", size="Gasto Luz/Agua (R$)", title="Detecção de Anomalias de Desgaste (Gasto x Ocupação)")
        fig8.add_hline(y=300, line_dash="dot", line_color="red", annotation_text="Limite Crítico de Desperdício (Ar quebrado?)")
        graficos['dispersao_anomalias'] = fig8.to_json()

        # G9: Rosca de Principais Despesas
        if not df_gastos.empty:
            df_rosca_desp = df_gastos.groupby('categoria')['valor'].sum().reset_index()
            fig9 = px.pie(df_rosca_desp, values='valor', names='categoria', hole=0.5, title="Maiores Ralos de Despesas")
            graficos['rosca_despesas'] = fig9.to_json()
        else:
            graficos['rosca_despesas'] = None

        # G10: Gráfico de Radar (Performance)
        categorias_radar = ['Rentabilidade', 'Ocupação', 'Baixo Custo', 'Manutenção Prev']
        fig10 = go.Figure()
        fig10.add_trace(go.Scatterpolar(r=[80, 60, 40, 90], theta=categorias_radar, fill='toself', name='Média do seu Portfólio'))
        fig10.add_trace(go.Scatterpolar(r=[90, 85, 20, 100], theta=categorias_radar, fill='toself', name='Imóvel Destaque'))
        fig10.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Gráfico de Radar (Forças do Imóvel)")
        graficos['radar_performance'] = fig10.to_json()

        # G11/12: Evolução de Lucro Mês a Mês
        fig11 = px.line(x=meses, y=[-100, 200, 800, 1500, 2100, 3200], title="Evolução de Lucro Real Acumulado", markers=True)
        fig11.update_traces(line_color='green', line_width=4)
        graficos['lucro_acumulado'] = fig11.to_json()

    except Exception as e:
        import traceback
        print(f"Erro ao gerar gráficos: {e}")
        traceback.print_exc()
        return None

    return graficos
