import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
from collections import Counter

df = pd.read_csv(r'D:\hsenespr\project_hse_nursing_home\final_table\all_pansionaty_combined.csv', encoding='utf-8-sig')

df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df['reviews'] = pd.to_numeric(df['reviews'], errors='coerce').fillna(0)
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
df.loc[df['price'] > 15000, 'price'] = None

def price_segment(p):
    if pd.isna(p) or p == 0: return 'Нет данных'
    if p < 1500: return 'Эконом (до 1500)'
    if p < 3000: return 'Средний (1500-3000)'
    if p < 5000: return 'Комфорт (3000-5000)'
    return 'Премиум (5000+)'

def rating_cat(r):
    if pd.isna(r): return 'Нет рейтинга'
    if r >= 4.7: return 'Отличный'
    if r >= 4.0: return 'Хороший'
    if r >= 3.0: return 'Средний'
    return 'Низкий'

df['price_segment'] = df['price'].apply(price_segment)
df['rating_cat'] = df['rating'].apply(rating_cat)

# Топ услуг
services = ' | '.join(df[df['services'] != '']['services'].dropna().tolist())
services_df = pd.DataFrame(Counter([s.strip() for s in services.split('|') if s.strip()]).most_common(15), columns=['Услуга', 'Количество'])

# Данные для карты
map_data = df[df['lat'].notna() & df['lon'].notna()]

# Графики
fig_rating = go.Figure()
rating_data = df[df['rating'] > 0]['rating'].dropna()
fig_rating.add_trace(go.Histogram(x=rating_data, nbinsx=25, marker_color='#2ecc71'))
fig_rating.add_vline(x=rating_data.mean(), line_dash="dash", line_color="red", 
                     annotation_text=f"Среднее: {rating_data.mean():.2f}")
fig_rating.update_layout(title='Распределение рейтингов', height=400, template='plotly_white')

fig_reviews = px.scatter(df[df['rating'] > 0], x='reviews', y='rating', color='source',
                         title='Рейтинг vs Отзывы', size='reviews', size_max=15,
                         color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c'],
                         hover_data=['name', 'price'])
fig_reviews.update_layout(height=400, template='plotly_white')

segment_counts = df['price_segment'].value_counts().reset_index()
segment_counts.columns = ['segment', 'count']
fig_price_segments = px.bar(segment_counts, x='segment', y='count', 
                            title='Ценовые сегменты',
                            labels={'segment': 'Ценовой сегмент', 'count': 'Количество'},
                            color='segment',
                            color_discrete_sequence=['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#95a5a6'])
fig_price_segments.update_layout(height=400, template='plotly_white', showlegend=False)

fig_price_box = px.box(df[df['price'].notna()], y='price', 
                       title='Boxplot цен (все источники)',
                       labels={'price': 'Цена (руб/день)'},
                       color_discrete_sequence=['#3498db'])
fig_price_box.update_layout(height=400, template='plotly_white')

fig_map = px.scatter_mapbox(map_data, lat='lat', lon='lon', color='rating_cat',
                            hover_name='name', hover_data={'price': True, 'rating': True},
                            color_discrete_map={'Отличный': '#27AE60', 'Хороший': '#3B6FD4', 
                                                'Средний': '#F5A623', 'Низкий': '#E74C3C', 'Нет рейтинга': '#AAB0C0'},
                            zoom=8, center={'lat': 55.75, 'lon': 37.62}, title='Расположение пансионатов',
                            mapbox_style='open-street-map')
fig_map.update_layout(height=400, margin=dict(t=40, b=10, l=10, r=10))

fig_top = px.bar(df[df['rating'] > 0].nlargest(10, 'rating')[::-1], x='rating', y='name', orientation='h',
                 title='Топ-10 по рейтингу', labels={'rating': 'Рейтинг', 'name': ''},
                 color='rating', color_continuous_scale='Viridis', text='reviews')
fig_top.update_layout(height=450, template='plotly_white')
fig_top.update_traces(texttemplate='%{text} отзывов', textposition='outside')

fig_services = px.bar(services_df, x='Количество', y='Услуга', orientation='h',
                       title='Топ-15 услуг', color='Количество', color_continuous_scale='Oranges')
fig_services.update_layout(height=450, template='plotly_white')



app = Dash(__name__)
app.layout = html.Div([
    html.H1("Анализ рынка пансионатов для пожилых", style={'textAlign': 'center', 'padding': '20px'}),
    html.Div([dcc.Graph(figure=fig_rating)], style={'padding': '10px'}),
    html.Div([dcc.Graph(figure=fig_reviews)], style={'padding': '10px'}),
    html.Div([
        html.Div([dcc.Graph(figure=fig_price_segments)], className='six columns'),
        html.Div([dcc.Graph(figure=fig_price_box)], className='six columns'),
    ], style={'padding': '10px'}),
    html.Div([
        html.Div([dcc.Graph(figure=fig_map)], className='six columns'),
        html.Div([dcc.Graph(figure=fig_top)], className='six columns'),
    ], style={'padding': '10px'}),
    html.Div([dcc.Graph(figure=fig_services)], style={'padding': '10px'}),
])

if __name__ == '__main__':
    print("\nОткройте: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)