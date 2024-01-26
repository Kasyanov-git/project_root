import base64

import dash
import requests
from dash import html, dcc, Input, Output, callback, State, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

backend_url = "http://localhost:8080"

app.layout = html.Div(style={'backgroundColor': '#245', 'color': 'black', 'height': '100vh'}, children=[
    html.Div(id='username-display', style={'color': 'white'}),
    dcc.Store(id='session', storage_type='session'),
    dcc.Store(id='selected-model', storage_type='session'),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

block_style = {
    'display': 'flex',
    'flex-direction': 'column',
    'justify-content': 'center',
    # 'align-items': 'center',
    'height': '100%',
    'padding': '2rem',
    'background-color': '#888',
    'border-radius': '0.5rem',
    'box-shadow': '0px 2px 5px rgba(0,0,0,0.3)',
    'margin': '1rem',
    'color': 'black',
}

index_page = html.Div(style=block_style, children=[
    html.H1('Добро пожаловать в Сервис классификации ПО'),
    dcc.Link(html.Button('Вход в систему'), href='/login'),
    html.Br(),
    dcc.Link(html.Button('Регистрация'), href='/register', style={'textDecoration': 'none'}),
])

login_page = html.Div(style=block_style, children=[
    html.H2('Вход'),
    dcc.Input(id="login-username", type="text", placeholder="Имя пользователя"),
    dcc.Input(id="login-password", type="password", placeholder="Пароль"),
    html.Button('Войти', id='login-button'),
    dcc.Link(html.Button('Регистрация'), href='/register', style={'textDecoration': 'none'}),
    html.Div(id="login-output"),
])

logout_page = html.Div([
    html.H2('Выход выполнен'),
    dcc.Link('Войти заново', href='/login')
])

register_page = html.Div(style=block_style, children=[
    html.H2('Регистрация'),
    dcc.Input(id="register-username", type="text", placeholder="Имя пользователя"),
    dcc.Input(id="register-password", type="password", placeholder="Пароль"),
    html.Button('Зарегистрироваться', id='register-button'),
    dcc.Link(html.Button('Вход в систему'), href='/login', style={'textDecoration': 'none'}),
    html.Div(id="register-output")
])

profile_page = html.Div(style=block_style, children=[
    html.H2('Профиль пользователя'),
    html.Div(id='profile-div'),
    dcc.Link(  # Добавляем ссылку в виде кнопки
        html.Button('Перейти к предсказаниям', id='go-to-predictions-button'),
        href='/predict',  # Указываем путь для перехода
        style={'textDecoration': 'none'}  # Убираем подчеркивание для ссылки
    ),
    dcc.Link(html.Button('Результаты предсказаний'), href='/prediction_results', style={'textDecoration': 'none'}),
])

prediction_page = html.Div(style=block_style, children=[
    html.H1("Предсказание"),
    html.Div(id="model-cost-info"),
    dcc.Dropdown(
        id="model-dropdown",
        options=[
            {'label': "Логистическая регрессия", 'value': 'lr_model'},
            {'label': "Градиентный бустинг", 'value': 'gb_model'},
        ],
        placeholder="Выберите модель"
    ),
    dcc.Upload(
        id="upload-file",
        children=html.Div([
            "Перетащите или ",
            html.A("выберите файл")
        ]),
        style={
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
        },
        multiple=False
    ),
    html.Button("Выполнить предсказание", id='submit-val', n_clicks=0),
    html.Div(id='container-button-basic',
             children='Upload a file and press submit'),
    dcc.Link(html.Button('Результаты предсказаний'), href='/prediction_results', style={'textDecoration': 'none'}),
])

prediction_results_page = html.Div(style=block_style, children=[
    html.H1("Результаты предсказаний"),
    html.Div(id='prediction-results-div')  # Храним здесь результаты
])

# Callback для отображения стоимости выбранной модели
@callback(
    Output("model-cost-info", "children"),
    [Input("model-dropdown", "value")],
    prevent_initial_call=True
)
def update_model_cost(model_name):
    if not model_name:
        return "Выберите модель, чтобы увидеть её стоимость."

    model_costs = {"lr_model": 10, "gb_model": 20}  # Заменить на актуальные значения
    cost = model_costs.get(model_name, "Модель не найдена")
    return f"Стоймость использования модели: {cost}"

# Callback для получения модели
@app.callback(
    Output('selected-model', 'data'),
    [Input("model-dropdown", "value")]
)
def update_selected_model(model_name):
    return model_name

# Callback для аутентификации пользователя и получения токена
@app.callback(
    [Output('session', 'data'), Output('url', 'pathname')],
    [Input("login-button", "n_clicks")],
    [State("login-username", "value"), State("login-password", "value")],
    prevent_initial_call=True
)
def login_callback(n_clicks, username, password):
    if not n_clicks:
        raise PreventUpdate

    response = requests.post(
        f"{backend_url}/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        session_data = response.json()
        token = session_data.get('access_token')
        user_id = session_data.get('user_id')
        print(user_id)
        return {'token': token, 'username': username, 'user_id': user_id}, '/profile'
    else:
        return f"Ошибка входа: {response.json().get('detail')}", no_update


#   Callback для отображения пользователя в сети
@app.callback(
    Output('username-display', 'children'),
    Input('url', 'pathname'),
    [State('session', 'data')]
)
def update_username_display(pathname, session_data):
    if not session_data or 'token' not in session_data or 'username' not in session_data:
        return ''
    else:
        return f"Пользователь: {session_data['username']}!"

#  Callback для регистрации пользователя
@callback(
    Output("register-output", "children"),
    [Input("register-button", "n_clicks")],
    [State("register-username", "value"), State("register-password", "value")],
)
def register_callback(n_clicks, username, password):
    if not n_clicks:
        raise PreventUpdate

    response = requests.post(
        f"{backend_url}/users/register",
        json={"username": username, "password": password}
    )

    if response.status_code == 200:
        return "Вы успешно зарегистрировались!"
    else:
        return f"Ошибка регистрации: {response.json().get('detail')}"

# страница профиля пользователя
@app.callback(
    Output('profile-div', 'children'),
    [Input('session', 'data'), Input('url', 'pathname')]
)
def load_profile(session_data, pathname):
    if pathname == '/profile' and session_data and 'token' in session_data:
        token = session_data['token']
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{backend_url}/users/me/", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            profile_info = html.Div([
                html.P(f"Username: {user_info['username']}"),
                html.P(f"ID: {user_info['id']}"),
                html.P(f"balance: {user_info['balance']}"),
                html.P(f"token: {user_info['token']}"),
                # Дополнительные элементы
            ])
            return profile_info

        return html.Div(['Произошла ошибка при загрузке данных профиля.'])
    return html.Div(['Вы не вошли в систему, чтобы видеть эту страницу.'])

#   Callback для отображения предсказания
@app.callback(
    Output('container-button-basic', 'children'),
    [Input('submit-val', 'n_clicks'),
     Input('session', 'data')],
    [State('upload-file', 'filename'),
     State('upload-file', 'contents'),
     State('selected-model', 'data')]
)
def update_output(n_clicks, session_data, filename, content, selected_model):
    if n_clicks > 0 and content is not None:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        files = {'file': (filename, decoded)}

        token = session_data.get('token', '')
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{backend_url}/upload_file/",
            files=files,
            headers=headers
        )
        if response.status_code == 200 and response.json()['file_id']:
            file_id = response.json()['file_id']
            print(file_id)
            prediction_response = requests.post(
                f"{backend_url}/predict/",
                params={'file_id': file_id, 'model_name': selected_model},
                headers=headers
            )
            if prediction_response.status_code == 200:
                # Обработка успешного получения предсказания
                return f"Модель: {prediction_response.json()}"
            else:
                # Обработка ошибки предсказания
                return f"Ошибка в работе модели: {prediction_response.text}"
        else:
            # Обработка ошибки загрузки файла
            return f"Ошибка загрузки файла: {response.text}"

    return 'Загрузите файл и нажмите на кнопку'

# Опрос статуса задачи предсказания
@app.callback(
    Output('prediction-status', 'children'),
    Input('status-refresh-button', 'n_clicks'),
    [dash.dependencies.State('job-id', 'value'),
     dash.dependencies.State('token', 'value')]
)
def refresh_status(n_clicks, job_id, token):
    if n_clicks:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{backend_url}/get_prediction_status/{job_id}", headers=headers)

        if response.status_code == 200:
            status_data = response.json()
            return html.Div([
                html.H5('Prediction Status'),
                html.P(f"Status: {status_data['status']}"),
                # Информация о результате, если задача завершена
                html.P(f"Result: {status_data.get('result', 'Waiting for completion.')}"),
            ])
        else:
            # Обработка ошибок при запросе статуса
            return html.Div([
                html.H5('Failed to refresh prediction status'),
                html.P('Please try again.')
            ])

    return html.Div(id='prediction-status')


# Callback, который загружает результаты предсказаний для пользователя
@app.callback(
    Output('prediction-results-div', 'children'),
    [Input('session', 'data')]
)
def load_prediction_results(session_data):
    if not session_data or 'token' not in session_data:
        raise PreventUpdate
    token = session_data['token']
    user_id = session_data['user_id']
    response = requests.get(f"{backend_url}/users/{user_id}/predictions", headers={"Authorization": f"Bearer {token}"})
    print(user_id)
    if response.status_code == 200:
        predictions = response.json()
        results = [
            html.Div([
                html.P(f"ID задачи: {prediction['job_id']}"),
                html.P(f"Дата: {prediction['created_at']}"),
                html.P(f"Результат: {prediction['result']}"),
                html.Div(style={'height': '1px', 'backgroundColor': 'black'})
            ]) for prediction in predictions
        ]
        return results
    else:
        return html.Div('Произошла ошибка при загрузке результатов предсказаний.')

# Callback для обновления страницы
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'),
              [State('session', 'data')])
def display_page(pathname, session_data):
    if not session_data or 'token' not in session_data:
        if pathname == '/register':
            return register_page
        elif pathname == '/login':
            return login_page
        elif pathname == '/logout':
            return logout_page
        else:
            return index_page
    elif pathname == '/register':
        return register_page
    elif pathname == '/login':
        return login_page
    elif pathname == '/logout':
        return logout_page
    elif pathname == '/profile':
        return profile_page
    elif pathname == '/predict':
        return prediction_page
    elif pathname == '/prediction_results':
        return prediction_results_page
    else:
        return index_page


if __name__ == '__main__':
    app.run_server(debug=True)