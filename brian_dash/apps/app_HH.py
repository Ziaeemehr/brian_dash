import dash
import dash_table
import brian2 as b2
import pandas as pd
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from brian_dash.models.HH import simulate_HH_neuron, filter_dataframe
from brian_dash.input_factory import (
    get_step_current,
    get_ramp_current,
    get_sinusoidal_current,
    get_zero_current)
from plotly.subplots import make_subplots


format_float2 = Format(group=",", precision=2, scheme=Scheme.fixed)
header_background_color = "rgb(30, 30, 30)"
cell_background_color = "rgb(125, 180, 200)"
cell_background_editable = "white"
style_data = {
    "whiteSpace": "normal",
    "height": "auto",
    "border": "none",
    "border-bottom": "1px solid #ccc",
}

style_data_conditional_cell = [
    {
        "if": {"column_editable": False},
        "backgroundColor": "rgb(125, 180, 200)",
        "color": "white",
    }
]
data = pd.read_csv("HH.csv")
df_par = data.loc[data["category"] == "par"].reset_index()
df_current = data.loc[data["category"] == "cur"].reset_index()

app = dash.Dash(
    __name__,
    prevent_initial_callbacks=False,
    external_stylesheets=[dbc.themes.LITERA],  # BOOTSTRAP FLATLY
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1.0"}],
)

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col([
                html.P(
                    id="title",
                    children="Hodgkin Huxley neuron",
                    style={"text-align": "left",
                           "color": "black", "font-size": "30px",
                           #    "font-family": "Iranian Sans"
                           },
                )],  # width={'offset': 1},
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dash_table.DataTable(
                            id="datatable-params",
                            columns=[dict(id=i,
                                          name=j,
                                          format=k,
                                          editable=m,
                                          type=l
                                          )
                                     for i, j, k, m, l in zip(
                                ["parameter", "unit", "value"],
                                ["parameter", "unit", "value"],
                                [Format(), Format(), format_float2],
                                [False, False, True],
                                ["text", "text", "numeric"],
                            )],
                            data=df_par.to_dict("records"),
                            sort_action="native",
                            sort_mode="single",
                            style_header={
                                "backgroundColor": header_background_color,
                                "color": "white"},
                            style_cell_conditional=[
                                {"if": {"column_id": c}, "textAlign": "center"}
                                for c in ["parameter", "unit", "value"]
                            ],
                            style_data=style_data,
                            style_data_conditional=style_data_conditional_cell,
                        )
                    ], xs=11, sm=11, md=5, lg=5, xl=5,
                ),
                dbc.Col(
                    [
                        dbc.Row(dbc.Col([dcc.Dropdown(
                            id='dropdown1',
                            clearable=False,
                            style={'textAlign': 'center'},
                            options=[
                                {'label': 'step', 'value': 1},
                                {'label': 'ramp', 'value': 2},
                                {'label': 'sin', 'value': 3}
                            ],
                            value=1)], xs=11, sm=11, md=5, lg=5, xl=5)),
                        html.Br(),
                        dbc.Row(
                            dbc.Col([
                                dash_table.DataTable(
                                    id="datatable-current",
                                    columns=[dict(id=i,
                                                  name=j,
                                                  format=k,
                                                  editable=m,
                                                  type=l
                                                  )
                                             for i, j, k, m, l in zip(
                                        ["parameter", "unit", "value"],
                                        ["parameter", "unit", "value"],
                                        [Format(), Format(), format_float2],
                                        [False, False, True],
                                        ["text", "text", "numeric"],
                                    )],
                                    data=df_current.loc[df_current["step"] == 1].to_dict(
                                        "records"),
                                    sort_action="native",
                                    sort_mode="single",
                                    style_header={
                                        "backgroundColor": header_background_color,
                                        "color": "white"},
                                    style_cell_conditional=[
                                        {"if": {"column_id": c},
                                            "textAlign": "center"}
                                        for c in ["parameter", "unit", "value"]
                                    ],
                                    style_data=style_data,
                                    style_data_conditional=style_data_conditional_cell,
                                )
                            ], xs=11, sm=11, md=5, lg=5, xl=5,)),

                    ],
                )

            ]
        ),

        html.Br(),
        dbc.Row([dbc.Col([html.Div(
            children=dcc.Graph(
                id="voltage-trace",
            ),
            className="card",)], xs=11, sm=11, md=11, lg=11, xl=11,
        )]),
    ], fluid=True,
)


@app.callback(
    Output("datatable-current", "data"),
    [Input("dropdown1", "value")],
    prevent_initial_call=False
)
def update_current_table(value):

    idx = int(value)

    if idx == 1:
        df = df_current.loc[df_current["step"] == 1]
        return df.to_dict("records")
    elif idx == 2:
        df = df_current.loc[df_current["ramp"] == 1]
        return df.to_dict("records")

    else:
        df = df_current.loc[df_current["sin"] == 1]
        return df.to_dict("records")


@ app.callback(
    Output('voltage-trace', 'figure'),
    [Input("datatable-params", "derived_virtual_data"),
     Input("datatable-current", "derived_virtual_data"),
     Input("dropdown1", "value")],
    prevent_initial_call=False
)
def update_output(table_par, table_current, value):

    df_par = pd.DataFrame(table_par)
    df_c = pd.DataFrame(table_current)

    t_end = int(filter_dataframe(df_c, "end time"))
    t_start = int(filter_dataframe(df_c, "start time"))
    t_simulation = int(filter_dataframe(df_par, "simulation time"))

    list_par = []

    idx = int(value)
    if idx == 1:
        amplitude = filter_dataframe(df_c, "amplitude")
        list_par.append(amplitude)

        if None not in list_par:
            current = get_step_current(t_start, t_end, b2.ms, amplitude*b2.uA)

    elif idx == 2:

        amplitude_start = filter_dataframe(df_c, "amplitude start")
        amplitude_end = filter_dataframe(df_c, "amplitude end")
        list_par.extend([amplitude_start, amplitude_end])

        if None not in list_par:
            current = get_ramp_current(t_start, t_end,
                                       b2.ms,
                                       amplitude_start*b2.uA,
                                       amplitude_end*b2.uA)

    else:
        frequency = filter_dataframe(df_c, "frequency")
        direct_current = filter_dataframe(df_c, "direct current")
        phase_offset = filter_dataframe(df_c, "phase offset")
        amplitude = filter_dataframe(df_c, "amplitude")
        list_par.extend([frequency, direct_current,
                         phase_offset, amplitude])

        if None not in list_par:
            current = get_sinusoidal_current(t_start,
                                             t_end,
                                             b2.ms,
                                             amplitude*b2.uA,
                                             frequency*b2.Hz,
                                             direct_current*b2.uA,
                                             phase_offset)

    
    if None in list_par:
        raise PreventUpdate
    else:
        # fig = go.Figure()
        data = simulate_HH_neuron(df_par, current, t_simulation * b2.ms)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            vertical_spacing=0.1, x_title="Time (ms)")
        fig.add_trace(go.Scatter(x=data['t'], y=data['v'], mode='lines',
                                 name='V'), row=1, col=1)
        fig.add_trace(go.Scatter(x=data['t'], y=data['h'], mode='lines',
                                 name='h'), row=2, col=1)
        fig.add_trace(go.Scatter(x=data['t'], y=data['n'], mode='lines',
                                 name='n'), row=2, col=1)
        fig.add_trace(go.Scatter(x=data['t'], y=data['m'], mode='lines',
                                 name='m'), row=2, col=1)
        fig.add_trace(go.Scatter(x=data['t'], y=data['I'], mode='lines',
                                 name="I"), row=3, col=1)
        fig.update_layout(autosize=False,
                          width=1500,
                          height=700)
        return fig


if __name__ == "__main__":
    app.run_server(debug=False, port=8000)
