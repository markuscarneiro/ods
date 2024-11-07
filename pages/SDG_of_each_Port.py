import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D

st.set_page_config(page_title="SDG of Each Port")

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

# Verificar se o DataFrame já está carregado no session_state
if 'df' not in st.session_state:
    st.error("O DataFrame não está carregado no session_state. Certifique-se de que a página anterior carregou o DataFrame.")

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

# Seleção de porto na sidebar com nomes anonimizados
porto_selecionado = st.sidebar.selectbox("Select Port", list(port_mapping.values()))

# Configuração do layout do Streamlit
st.markdown("<h1 style='text-align: center;'>SDG per Port vs. Average per SDG</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center;'>{porto_selecionado}</h3>", unsafe_allow_html=True)

# Obter todos os temas únicos (ODS)
temas = df['TEMA'].unique()

# Gerar um par de gráficos (porto e média) para cada tema
for tema in temas:
    df_filtrado = df[df['TEMA'] == tema]

    # Verificar se há dados para o tema selecionado
    if df_filtrado.empty:
        st.warning(f"Não há dados disponíveis para o tema '{tema}'.")
        continue

    # Definir número de variáveis para o gráfico de radar
    N = len(df_filtrado['ITEM'].unique())
    
    # Verificar se N é maior que zero para evitar divisão por zero
    if N == 0:
        st.warning(f"Não há itens disponíveis para gerar o gráfico de radar para o tema '{tema}'.")
        continue

    # Criar o gráfico de radar
    theta = radar_factory(N, frame='polygon')

    # Gráfico comparativo do porto selecionado com a média para o tema atual
    fig, (ax1, ax2) = plt.subplots(figsize=(12, 6), nrows=1, ncols=2, subplot_kw=dict(projection='radar'))
    fig.subplots_adjust(wspace=0.5, top=0.85, bottom=0.15)

    valores_porto = df_filtrado[porto_selecionado].values[:N]
    valores_media = df_filtrado['MEDIA'].values[:N]
    labels = df_filtrado['ITEM'].values[:N]

    # Gráfico do porto específico
    ax1.plot(theta, valores_porto, color='#00A36C', linewidth=2, label=porto_selecionado)
    ax1.fill(theta, valores_porto, color='#00A36C', alpha=0.5)
    ax1.set_varlabels(labels, fontsize=10)
    ax1.set_title(f"{porto_selecionado} - {tema}", weight='bold', size='medium', position=(0.5, 1.1), horizontalalignment='center')

    # Gráfico da média
    ax2.plot(theta, valores_media, color='gray', linewidth=2, linestyle='--', label='Média')
    ax2.fill(theta, valores_media, color='gray', alpha=0.2)
    ax2.set_varlabels(labels, fontsize=10)
    ax2.set_title(f"Média - {tema}", weight='bold', size='medium', position=(0.5, 1.1), horizontalalignment='center')

    # Configurações de grade e legendas
    for ax in (ax1, ax2):
        ax.grid(True, which='major', axis='x', color='gray', linestyle='-', linewidth=0.5)
        ax.grid(False, which='major', axis='y')
        ax.set_yticklabels([])

    st.pyplot(fig)
