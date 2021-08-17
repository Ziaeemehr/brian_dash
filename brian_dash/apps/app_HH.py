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
from brian_dash.models.HH import simulate_HH_neuron, filter_df
from brian_dash.input_factory import get_step_current
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
par = pd.read_csv("HH.csv")

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
                            data=par.to_dict("records"),
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
                    ], xs=12, sm=12, md=6, lg=6, xl=6,
                )
            ]
        ),

        html.Br(),

        # dbc.Row(
        #     [dbc.Col([dbc.Button("Submit", id="submit-val",
        #                          n_clicks=0, className="mr-2")],
        #              width={'size': 3, 'offset': 1}),
        #      ], justify='left',
        # ),
        dbc.Row([dbc.Col([html.Div(
            children=dcc.Graph(
                id="voltage-trace",
            ),
            className="card",)], xs=11, sm=11, md=11, lg=11, xl=11,
            )]),

    ], fluid=True,
)


@ app.callback(
    Output('voltage-trace', 'figure'),
    # Output("gate-trace", "figure"),
    # [Input("submit-val", "n_clicks")],
    # state=[
    #     State("datatable-params", "derived_virtual_data")
    # ]
    Input("datatable-params", "derived_virtual_data")
    
    # prevent_initial_call = True
)
def update_output_div(par):

    # if (n is None) or (n == 0):
    #     raise PreventUpdate

    df_par = pd.DataFrame(par)
    t_end = int(filter_df(df_par, "t_end"))
    t_start = int(filter_df(df_par, "t_start"))
    amplitude = filter_df(df_par, "amplitude")
    t_simulation = int(filter_df(df_par, "t_simulation"))

    current = get_step_current(t_start, t_end, b2.ms, amplitude * b2.uA)
    data = simulate_HH_neuron(df_par, current, t_simulation * b2.ms)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.1, x_title="Time (ms)",
                        print_grid=True)

    fig.add_trace(go.Scatter(x=data['t'], y=data['v'],
                             mode='lines',
                             name='V'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data['t'], y=data['h'],
                             mode='lines',
                             name='h'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data['t'], y=data['n'],
                             mode='lines',
                             name='n'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data['t'], y=data['m'],
                             mode='lines',
                             name='m'), row=2, col=1)
    fig.update_layout(autosize=False,
                      width=1500,
                      height=700,
                      )

    return fig  # v_fig, gate_fig


if __name__ == "__main__":
    app.run_server(debug=True, port=8000)
