import plotly.graph_objects as go

def generate_forecast_plot(data):

    dates = [row.date_prevision for row in data]
    debit = [row.debit_riviere_m3s_prevu for row in data]
    pluie = [row.pluviometrie_mm_prevue for row in data]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=debit,
        name="Débit rivière (m3/s)",
        yaxis="y1"
    ))

    fig.add_trace(go.Bar(
        x=dates,
        y=pluie,
        name="Pluie (mm)",
        yaxis="y2",
        opacity=0.6
    ))

    fig.update_layout(
        title="Prévisions hydrométéorologiques",
        yaxis=dict(title="Débit m3/s"),
        yaxis2=dict(
            title="Pluie mm",
            overlaying="y",
            side="right"
        )
    )

    return fig.to_json()