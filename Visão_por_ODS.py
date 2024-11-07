import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D

st.set_page_config(page_title="View by SDG")

# Função para criar o gráfico de radar
def radar_factory(num_vars, frame='circle'):
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    class RadarTransform(PolarAxes.PolarTransform):
        def transform_path_non_affine(self, path):
            if path._interpolation_steps > 1:
                path = path.interpolated(num_vars)
            return Path(self.transform(path.vertices), path.codes)

    class RadarAxes(PolarAxes):
        name = 'radar'
        PolarTransform = RadarTransform

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')

        def fill(self, *args, closed=True, **kwargs):
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)

        def set_varlabels(self, labels, fontsize=10):
            self.set_thetagrids(np.degrees(theta), labels, fontsize=fontsize)

        def _gen_axes_patch(self):
            if frame == 'circle':
                return Circle((0.5, 0.5), 0.5)
            elif frame == 'polygon':
                return RegularPolygon((0.5, 0.5), num_vars, radius=.5, edgecolor="k")
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

        def _gen_axes_spines(self):
            if frame == 'circle':
                return super()._gen_axes_spines()
            elif frame == 'polygon':
                spine = Spine(axes=self, spine_type='circle', path=Path.unit_regular_polygon(num_vars))
                spine.set_transform(Affine2D().scale(.5).translate(.5, .5) + self.transAxes)
                return {'polar': spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta

# Carregar os dados e armazenar no st.session_state para compartilhar com outras páginas
@st.cache_data
def load_data():
    df = pd.read_csv("BASE.csv", delimiter=';')
    # Calcular a Average de todos os portos
    df['MEDIA'] = df[['SUAPE', 'ITAQUI', 'CABEDELO', 'S. FRANCISCO DO SUL', 'VALE', 'VPORTS']].mean(axis=1)
    return df

# Carregar o DataFrame na session_state, se não estiver já carregado
if 'df' not in st.session_state:
    st.session_state['df'] = load_data()

# Utilizar o DataFrame armazenado no session_state
df = st.session_state['df']

# Anonimizar os nomes dos portos
port_mapping = {
    'SUAPE': 'Port A',
    'ITAQUI': 'Port B',
    'CABEDELO': 'Port C',
    'S. FRANCISCO DO SUL': 'Port D',
    'VALE': 'Port E',
    'VPORTS': 'Port F'
}
df = df.rename(columns=port_mapping)

# Selectbox para selecionar o valor do campo 'TEMA'
tema_selecionado = st.sidebar.selectbox("Select SDG", df['TEMA'].unique())

# Filtrar as áreas disponíveis com base no tema selecionado, adicionando a opção "Todas"
areas_disponiveis = df[df['TEMA'] == tema_selecionado]['AREA'].unique().tolist()
areas_disponiveis.insert(0, "All")
area_selecionada = st.sidebar.selectbox("Select Area", areas_disponiveis)

# Filtrar o DataFrame com base no tema e, opcionalmente, na área selecionada
if area_selecionada == "All":
    df_filtrado = df[df['TEMA'] == tema_selecionado]
else:
    df_filtrado = df[(df['TEMA'] == tema_selecionado) & (df['AREA'] == area_selecionada)]

# Verificar se há dados para o tema e área selecionados
if df_filtrado.empty:
    st.warning(f"Não há dados disponíveis para o tema '{tema_selecionado}' e a área '{area_selecionada}'.")
else:
    # Definir número de variáveis para o gráfico de radar
    N = len(df_filtrado['ITEM'].unique())
    
    # Verificar se N é maior que zero para evitar divisão por zero
    if N == 0:
        st.warning("Não há itens disponíveis para gerar o gráfico de radar.")
    else:
        # Lista dos portos anonimizada
        portos_anonimos = list(port_mapping.values())

        # Criar o gráfico de radar
        theta = radar_factory(N, frame='polygon')

        # Cor verde personalizada (similar à da imagem fornecida)
        verde_custom = '#00A36C'  # Tom de verde ajustado

        # Configuração do layout do Streamlit
        st.markdown("<h1 style='text-align: center;; font-size: 34px;'>SDG Attributes: Indicators of the Port Sector</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{tema_selecionado} - Area: {area_selecionada}</h3>", unsafe_allow_html=True)

        # Gráficos principais
        fig, axs = plt.subplots(figsize=(18, 12), nrows=2, ncols=3, subplot_kw=dict(projection='radar'))
        fig.subplots_adjust(wspace=0.25, hspace=0.35, top=0.85, bottom=0.1)

        for ax, porto_anonimo in zip(axs.flat, portos_anonimos):
            valores = df_filtrado[porto_anonimo].values[:N]
            labels = df_filtrado['ITEM'].values[:N]

            ax.plot(theta, valores, color=verde_custom, linewidth=2)
            ax.fill(theta, valores, color=verde_custom, alpha=0.5)
            ax.set_varlabels(labels, fontsize=10)
            ax.set_title(porto_anonimo, weight='bold', size='medium', position=(0.5, 1.1), horizontalalignment='center')
            ax.grid(True, which='major', axis='x', color='gray', linestyle='-', linewidth=0.5)
            ax.grid(False, which='major', axis='y')
            ax.set_yticklabels([])

        st.pyplot(fig)

        # Gráficos comparativos individuais de cada porto com a Average
        st.markdown("<h3 style='text-align: center;'>Comparison of each Port with the Average</h3>", unsafe_allow_html=True)

        for porto_anonimo in portos_anonimos:
            fig, (ax1, ax2) = plt.subplots(figsize=(12, 6), nrows=1, ncols=2, subplot_kw=dict(projection='radar'))
            fig.subplots_adjust(wspace=0.5, top=0.85, bottom=0.15)

            valores_porto = df_filtrado[porto_anonimo].values[:N]
            valores_media = df_filtrado['MEDIA'].values[:N]
            labels = df_filtrado['ITEM'].values[:N]

            # Gráfico do porto específico
            ax1.plot(theta, valores_porto, color=verde_custom, linewidth=2, label=porto_anonimo)
            ax1.fill(theta, valores_porto, color=verde_custom, alpha=0.5)
            ax1.set_varlabels(labels, fontsize=10)
            ax1.set_title(porto_anonimo, weight='bold', size='medium', position=(0.5, 1.1), horizontalalignment='center')

            # Gráfico da Average
            ax2.plot(theta, valores_media, color='gray', linewidth=2, linestyle='--', label='Average')
            ax2.fill(theta, valores_media, color='gray', alpha=0.2)
            ax2.set_varlabels(labels, fontsize=10)
            ax2.set_title("Average", weight='bold', size='medium', position=(0.5, 1.1), horizontalalignment='center')

            # Configurações de grade e legendas
            for ax in (ax1, ax2):
                ax.grid(True, which='major', axis='x', color='gray', linestyle='-', linewidth=0.5)
                ax.grid(False, which='major', axis='y')
                ax.set_yticklabels([])

            st.pyplot(fig)
